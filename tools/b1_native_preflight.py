#!/usr/bin/env python3
"""One-job, one-step, synthetic-only native B1 GPU preflight."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import stat
import subprocess
import sys
import time
from typing import Any, Iterable

from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f
from mmbu_phase1 import b1_preflight


REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "config/phase1/b1-mocs-preflight.json"
PIN_PATH = REPO / "docs/phase1/b1-pin.json"
LOGIT_ATOL = 0.5
LOSS_ATOL = 1e-5
# Half a unit-scale BF16 machine epsilon. The gate compares numerically
# different batch shapes, so an FP32-scale threshold is not meaningful.
MICROBATCH_LOSS_ATOL = 2 ** -8
MICROBATCH_GRAD_ATOL = 2 ** -5
MICROBATCH_GRAD_RTOL = 0.05
MICROBATCH_GRAD_COSINE_MIN = 1 - MICROBATCH_GRAD_RTOL ** 2 / 2
SEED = 20261023
_LANGUAGE_LORA = re.compile(r"^model\.language_model\.layers\.\d+\.self_attn\.(?:q_proj|v_proj)$")
_RUNTIME_PACKAGES = {
    "accelerate": "accelerate", "numpy": "numpy", "peft": "peft", "pillow": "pillow",
    "safetensors": "safetensors", "torch": "torch", "torchvision": "torchvision",
    "transformers": "transformers",
}
_ADAPTER_FILES = ("adapter_config.json", "adapter_model.safetensors")


def fixture_specs() -> list[dict]:
    """Return the prospectively frozen, generated-only image fixture inventory."""
    rows = (
        ("small-rgb", "RGB", [28, 28], 1, "rgb"),
        ("large-rgb", "RGB", [280, 280], 2, "rgb"),
        ("nonsquare-rgb", "RGB", [84, 140], 3, "rgb"),
        ("extreme-aspect-rgb", "RGB", [28, 280], 4, "rgb"),
        ("grayscale-conversion", "L", [84, 84], 5, "convert_rgb"),
        ("rgba-conversion", "RGBA", [84, 84], 6, "composite_white_rgb"),
        ("exif-orientation", "RGB", [84, 140], 7, "exif_transpose_rgb"),
        ("boundary-27", "RGB", [27, 27], 8, "rgb"),
        ("boundary-28", "RGB", [28, 28], 9, "rgb"),
        ("boundary-29", "RGB", [29, 29], 10, "rgb"),
    )
    return [
        {"id": identity, "raw_mode": mode, "raw_size": size, "seed": seed, "transform": transform}
        for identity, mode, size, seed, transform in rows
    ]


def build_target_only_labels(input_ids: list[list[int]], attention_mask: list[list[int]], prompt_token_counts: list[int]) -> list[list[int]]:
    f.require(len(input_ids) == len(attention_mask) == len(prompt_token_counts), "labels", "batch dimensions must agree")
    result = []
    for row_index, (tokens, mask, prompt_count) in enumerate(zip(input_ids, attention_mask, prompt_token_counts)):
        f.require(len(tokens) == len(mask), f"labels[{row_index}]", "token and mask lengths must agree")
        f.integer(prompt_count, f"labels[{row_index}].prompt_token_count", minimum=1)
        active = [index for index, value in enumerate(mask) if value == 1]
        f.require(all(value in (0, 1) for value in mask), f"labels[{row_index}].attention_mask", "must be binary")
        f.require(active == list(range(active[0], len(mask))) if active else False,
                  f"labels[{row_index}].attention_mask", "must use left padding with a nonempty suffix")
        f.require(prompt_count < len(active), f"labels[{row_index}]", "must retain at least one target token")
        target_indices = set(active[prompt_count:])
        result.append([token if index in target_indices else -100 for index, token in enumerate(tokens)])
    return result


def exact_lora_targets(module_names: Iterable[str]) -> list[str]:
    matches = sorted(name for name in module_names if _LANGUAGE_LORA.fullmatch(name))
    f.require(bool(matches), "lora.targets", "no exact language attention q/v projections matched")
    f.require(len(matches) % 2 == 0, "lora.targets", "q/v projection count must be paired")
    return matches


def validate_update_inventory(
    declared: list[str],
    trainable: list[str],
    gradients: list[str],
    updated: list[str],
    expected_updated: list[str] | None = None,
) -> dict:
    expected_updated = declared if expected_updated is None else expected_updated
    for label, values in (("declared", declared), ("trainable", trainable), ("gradients", gradients),
                          ("updated", updated), ("expected_updated", expected_updated)):
        f.require(values == sorted(set(values)), f"parameters.{label}", "must be unique and sorted")
    f.literal(trainable, "parameters.trainable", declared)
    f.literal(gradients, "parameters.gradients", declared)
    f.require(bool(expected_updated) and set(expected_updated) <= set(declared), "parameters.expected_updated",
              "must be a nonempty subset of declared parameters")
    f.literal(updated, "parameters.updated", expected_updated)
    return {"declared": declared, "finite_gradients": gradients,
            "expected_updated": expected_updated, "updated": updated}


def validate_mrope_summary(summary: Any, batch_size: int, sequence_length: int) -> dict:
    summary = f.closed(summary, "mrope", (
        "position_shape", "position_dtype", "rope_deltas_shape", "rope_deltas_dtype",
        "image_temporal_unique_counts", "image_grid_temporal_counts",
        "position_sha256", "rope_deltas_sha256",
    ))
    f.literal(summary["position_shape"], "mrope.position_shape", [3, batch_size, sequence_length])
    f.literal(summary["position_dtype"], "mrope.position_dtype", "torch.int64")
    f.literal(summary["rope_deltas_shape"], "mrope.rope_deltas_shape", [batch_size, 1])
    f.literal(summary["rope_deltas_dtype"], "mrope.rope_deltas_dtype", "torch.int64")
    temporal = summary["image_temporal_unique_counts"]
    grids = summary["image_grid_temporal_counts"]
    f.literal(temporal, "mrope.image_temporal_unique_counts", grids)
    f.require(len(temporal) == batch_size and all(type(value) is int and value >= 1 for value in temporal),
              "mrope.image_temporal_unique_counts", "must contain one positive count per batch member")
    f.digest(summary["position_sha256"], "mrope.position_sha256")
    f.digest(summary["rope_deltas_sha256"], "mrope.rope_deltas_sha256")
    return summary


def build_geometry_records(
    fixtures: list[dict],
    image_grid_thw: list[list[int]],
    image_token_counts: list[int],
    patch_size: int,
    merge_size: int,
) -> list[dict]:
    f.require(len(fixtures) == len(image_grid_thw) == len(image_token_counts), "geometry",
              "fixture, grid, and token populations must agree")
    f.integer(patch_size, "geometry.patch_size", minimum=1)
    f.integer(merge_size, "geometry.merge_size", minimum=1)
    records = []
    for index, (fixture, grid, token_count) in enumerate(zip(fixtures, image_grid_thw, image_token_counts)):
        f.require(type(fixture) is dict, f"geometry[{index}].fixture", "must be an object")
        identity = f.text(fixture.get("id"), f"geometry[{index}].id")
        size = fixture.get("effective_size")
        f.require(type(size) is list and len(size) == 2, f"geometry[{index}].effective_size", "must be [width,height]")
        width = f.integer(size[0], f"geometry[{index}].effective_size[0]", minimum=1)
        height = f.integer(size[1], f"geometry[{index}].effective_size[1]", minimum=1)
        f.require(type(grid) is list and len(grid) == 3, f"geometry[{index}].grid", "must be [t,h,w]")
        temporal, grid_height, grid_width = (
            f.integer(value, f"geometry[{index}].grid[{axis}]", minimum=1)
            for axis, value in enumerate(grid)
        )
        token_count = f.integer(token_count, f"geometry[{index}].visual_token_count", minimum=1)
        merged_area = merge_size * merge_size
        f.require((temporal * grid_height * grid_width) % merged_area == 0,
                  f"geometry[{index}].grid", "must divide exactly by spatial merge area")
        f.literal(token_count, f"geometry[{index}].visual_token_count",
                  temporal * grid_height * grid_width // merged_area)
        processed_width = grid_width * patch_size
        processed_height = grid_height * patch_size
        scale_x = processed_width / width
        scale_y = processed_height / height
        box = [width * 0.25, height * 0.25, width * 0.5, height * 0.5]
        transformed = [box[0] * scale_x, box[1] * scale_y, box[2] * scale_x, box[3] * scale_y]
        restored = [transformed[0] / scale_x, transformed[1] / scale_y,
                    transformed[2] / scale_x, transformed[3] / scale_y]
        round_trip = max(abs(left - right) for left, right in zip(box, restored))
        f.require(round_trip <= 1e-9, f"geometry[{index}].round_trip", "coordinate transform does not invert")
        records.append({
            "id": identity,
            "effective_size": [width, height],
            "processed_size": [processed_width, processed_height],
            "image_grid_thw": grid,
            "visual_token_count": token_count,
            "scale_xy": [scale_x, scale_y],
            "round_trip_max_abs": round_trip,
        })
    return records


def validate_microbatch_equivalence(
    full_loss: float,
    accumulated_loss: float,
    gradient_max_abs_by_parameter: dict[str, float],
    gradient_relative_l2: float,
    gradient_cosine: float,
    loss_tolerance: float,
    gradient_tolerance: float,
    gradient_relative_l2_tolerance: float,
    gradient_cosine_minimum: float,
) -> dict:
    f.number(full_loss, "microbatch.full_loss")
    f.number(accumulated_loss, "microbatch.accumulated_loss")
    f.number(loss_tolerance, "microbatch.loss_tolerance", minimum=0)
    f.number(gradient_tolerance, "microbatch.gradient_tolerance", minimum=0)
    gradient_relative_l2 = f.number(gradient_relative_l2, "microbatch.gradient_relative_l2", minimum=0)
    gradient_cosine = f.number(gradient_cosine, "microbatch.gradient_cosine", minimum=-1, maximum=1)
    f.number(gradient_relative_l2_tolerance, "microbatch.gradient_relative_l2_tolerance", minimum=0)
    f.number(gradient_cosine_minimum, "microbatch.gradient_cosine_minimum", minimum=-1, maximum=1)
    f.require(type(gradient_max_abs_by_parameter) is dict and bool(gradient_max_abs_by_parameter),
              "microbatch.gradient_deltas", "must be a nonempty object")
    names = sorted(gradient_max_abs_by_parameter, key=lambda value: value.encode("utf-8"))
    f.literal(list(gradient_max_abs_by_parameter), "microbatch.gradient_deltas.order", names)
    deltas = []
    for name in names:
        f.text(name, "microbatch.gradient_deltas.name")
        delta = f.number(gradient_max_abs_by_parameter[name], f"microbatch.gradient_deltas.{name}", minimum=0)
        deltas.append(delta)
    loss_delta = abs(full_loss - accumulated_loss)
    gradient_delta = max(deltas)
    f.require(loss_delta <= loss_tolerance, "microbatch.loss",
              f"loss drift {loss_delta:.17g} exceeds tolerance {loss_tolerance:.17g}")
    f.require(gradient_delta <= gradient_tolerance, "microbatch.gradients",
              f"gradient drift {gradient_delta:.17g} exceeds tolerance {gradient_tolerance:.17g}")
    f.require(gradient_relative_l2 <= gradient_relative_l2_tolerance, "microbatch.gradient_relative_l2",
              f"relative L2 drift {gradient_relative_l2:.17g} exceeds tolerance {gradient_relative_l2_tolerance:.17g}")
    f.require(gradient_cosine >= gradient_cosine_minimum, "microbatch.gradient_cosine",
              f"cosine {gradient_cosine:.17g} is below minimum {gradient_cosine_minimum:.17g}")
    return {
        "full_loss": full_loss,
        "accumulated_loss": accumulated_loss,
        "loss_abs_delta": loss_delta,
        "loss_tolerance": loss_tolerance,
        "gradient_max_abs": gradient_delta,
        "gradient_tolerance": gradient_tolerance,
        "gradient_relative_l2": gradient_relative_l2,
        "gradient_relative_l2_tolerance": gradient_relative_l2_tolerance,
        "gradient_cosine": gradient_cosine,
        "gradient_cosine_minimum": gradient_cosine_minimum,
        "gradient_max_abs_by_parameter": gradient_max_abs_by_parameter,
    }


def parse_nvidia_smi_receipt(raw: str) -> dict:
    parts = [part.strip() for part in f.text(raw, "nvidia_smi").split(",")]
    f.require(len(parts) == 3, "nvidia_smi", "must contain driver, name, and memory")
    driver = f.text(parts[0], "nvidia_smi.driver_version")
    name = f.text(parts[1], "nvidia_smi.name")
    try:
        memory_mib = int(parts[2])
    except ValueError:
        f.fail("nvidia_smi.memory_mib", "must be an integer")
    f.integer(memory_mib, "nvidia_smi.memory_mib", minimum=1)
    return {"driver_version": driver, "name": name, "memory_mib": memory_mib}


def compare_logits(expected: list[float], observed: list[float], tolerance: float, path: str) -> float:
    f.require(len(expected) == len(observed) and bool(expected), path, "logit vectors must have equal nonzero length")
    f.number(tolerance, path + ".tolerance", minimum=0)
    deltas = []
    for index, (left, right) in enumerate(zip(expected, observed)):
        f.number(left, f"{path}.expected[{index}]")
        f.number(right, f"{path}.observed[{index}]")
        delta = abs(left - right)
        f.require(math.isfinite(delta), f"{path}[{index}]", "delta is nonfinite")
        deltas.append(delta)
    maximum = max(deltas)
    f.require(maximum <= tolerance, path, "logit drift exceeds tolerance")
    return maximum


def validate_runtime_identity(expected: Any, observed: Any) -> dict:
    expected = f.closed(expected, "runtime.expected", ("python", *_RUNTIME_PACKAGES))
    observed = f.closed(observed, "runtime.observed", expected)
    for key in expected:
        f.text(expected[key], f"runtime.expected.{key}")
        f.literal(observed[key], f"runtime.observed.{key}", expected[key])
    return observed


def inventory_adapter(root: Path) -> list[dict]:
    f.require(root.is_dir() and not root.is_symlink(), "adapter", "must be a real directory")
    names = sorted((path.name for path in root.iterdir()), key=lambda name: name.encode("utf-8"))
    f.literal(names, "adapter.files", list(_ADAPTER_FILES))
    rows = []
    for name in names:
        path = root / name
        info = path.lstat()
        f.require(stat.S_ISREG(info.st_mode), f"adapter.{name}", "must be a regular unaliased file")
        raw = path.read_bytes()
        after = path.lstat()
        before_identity = (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        after_identity = (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        f.require(after_identity == before_identity, f"adapter.{name}", "changed while being inventoried")
        rows.append({"path": name, "bytes": len(raw), "sha256": _sha(raw)})
    return rows


def verify_adapter_inventory(root: Path, expected: Any) -> list[dict]:
    expected = f.array(expected, "adapter.inventory", nonempty=True)
    observed = inventory_adapter(root)
    f.literal(observed, "adapter.inventory", expected)
    return observed


def validate_adapter_scope(config: Any, targets: list[str], base_model_path: str) -> dict:
    f.require(type(config) is dict, "adapter.config", "must be a JSON object")
    f.require(targets == sorted(set(targets)) and bool(targets), "adapter.targets",
              "must be a nonempty sorted unique list")
    f.literal(config.get("target_modules"), "adapter.config.target_modules", targets)
    f.literal(config.get("base_model_name_or_path"), "adapter.config.base_model_name_or_path", base_model_path)
    return config


def write_exact_adapter_scope(adapter_root: Path, targets: list[str], base_model_path: str) -> dict:
    path = adapter_root / "adapter_config.json"
    f.require(path.is_file() and not path.is_symlink(), "adapter.config", "missing regular adapter config")
    config = json.loads(path.read_text(encoding="utf-8"))
    f.require(type(config) is dict, "adapter.config", "must be a JSON object")
    config["target_modules"] = targets
    config["base_model_name_or_path"] = base_model_path
    validate_adapter_scope(config, targets, base_model_path)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return config


def validate_adapter_state_keys(keys: list[str], targets: list[str]) -> list[str]:
    f.require(keys == sorted(set(keys)), "adapter.state_keys", "must be unique and sorted")
    expected = sorted(
        f"base_model.model.{target}.lora_{side}.weight"
        for target in targets for side in ("A", "B")
    )
    f.literal(keys, "adapter.state_keys", expected)
    return keys


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _tensor_sha(tensor: Any) -> str:
    return _sha(tensor.detach().contiguous().cpu().view(-1).numpy().tobytes())


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical.dumps(value) + b"\n")


def make_images(specs: list[dict]) -> tuple[list[Any], list[dict]]:
    from io import BytesIO
    from PIL import Image, ImageOps

    images, evidence = [], []
    for spec in specs:
        width, height = spec["raw_size"]
        rng = random.Random(spec["seed"])
        channels = 1 if spec["raw_mode"] == "L" else 4 if spec["raw_mode"] == "RGBA" else 3
        raw = bytes(rng.randrange(256) for _ in range(width * height * channels))
        image = Image.frombytes(spec["raw_mode"], (width, height), raw)
        if spec["transform"] == "convert_rgb":
            image = image.convert("RGB")
        elif spec["transform"] == "composite_white_rgb":
            base = Image.new("RGB", image.size, (255, 255, 255))
            base.paste(image, mask=image.getchannel("A"))
            image = base
        elif spec["transform"] == "exif_transpose_rgb":
            encoded = BytesIO()
            exif = Image.Exif()
            exif[274] = 6
            image.save(encoded, format="JPEG", exif=exif)
            raw = encoded.getvalue()
            image = ImageOps.exif_transpose(Image.open(BytesIO(raw))).convert("RGB")
        f.literal(image.mode, f"fixture.{spec['id']}.mode", "RGB")
        rgb = image.tobytes()
        images.append(image)
        evidence.append({
            "id": spec["id"], "raw_mode": spec["raw_mode"], "raw_size": spec["raw_size"],
            "raw_sha256": _sha(raw), "effective_mode": image.mode,
            "effective_size": list(image.size), "effective_sha256": _sha(rgb),
            "transform": spec["transform"], "source": "generated_in_memory_synthetic_engineering",
        })
    return images, evidence


def _messages(prompt: str) -> list[dict]:
    return [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]


def chat_template_from_record(record: Any) -> str:
    f.require(type(record) is dict, "processor.chat_template_record", "must be a JSON object")
    return f.text(record.get("chat_template"), "processor.chat_template")


def load_pil_processor(model_root: Path) -> Any:
    """Load the exact local processor while forcing PIL for image decoding only.

    Transformers 5.19 applies a composite backend override to both image and
    video components.  PIL is deliberately selected for still images here,
    while the required but unused video component keeps its supported torchvision
    backend.  No video input is admitted by this preflight.
    """
    from transformers import AutoImageProcessor, AutoTokenizer, AutoVideoProcessor
    from transformers.models.qwen2_5_vl.processing_qwen2_5_vl import Qwen2_5_VLProcessor

    image_processor = AutoImageProcessor.from_pretrained(
        model_root, local_files_only=True, trust_remote_code=False, backend="pil"
    )
    video_processor = AutoVideoProcessor.from_pretrained(
        model_root, local_files_only=True, trust_remote_code=False, backend="torchvision"
    )
    tokenizer = AutoTokenizer.from_pretrained(
        model_root, local_files_only=True, trust_remote_code=False
    )
    template_record = json.loads((model_root / "chat_template.json").read_text(encoding="utf-8"))
    chat_template = chat_template_from_record(template_record)
    processor = Qwen2_5_VLProcessor(
        image_processor=image_processor,
        tokenizer=tokenizer,
        video_processor=video_processor,
        chat_template=chat_template,
    )
    f.literal(type(processor).__name__, "processor.class", "Qwen2_5_VLProcessor")
    f.literal(type(processor.image_processor).__name__, "processor.image.class", "Qwen2VLImageProcessorPil")
    f.literal(processor.image_processor.backend, "processor.image.backend", "pil")
    f.literal(type(processor.video_processor).__name__, "processor.video.class", "Qwen2VLVideoProcessor")
    f.literal(processor.video_processor.backend, "processor.video.backend", "torchvision")
    f.literal(type(processor.tokenizer).__name__, "processor.tokenizer.class", "Qwen2Tokenizer")
    return processor


def _encode(processor: Any, images: list[Any], prompts: list[str], targets: list[str] | None = None) -> tuple[Any, list[int]]:
    prompt_texts = [processor.apply_chat_template(_messages(prompt), tokenize=False, add_generation_prompt=True) for prompt in prompts]
    full_texts = prompt_texts if targets is None else [text + target + processor.tokenizer.eos_token for text, target in zip(prompt_texts, targets)]
    prompt_counts = []
    for image, text in zip(images, prompt_texts):
        one = processor(text=[text], images=[image], padding=False, return_tensors="pt")
        prompt_counts.append(int(one["attention_mask"].sum().item()))
    batch = processor(text=full_texts, images=images, padding=True, return_tensors="pt")
    return batch, prompt_counts


def _device_batch(batch: Any, device: Any) -> dict:
    return {key: value.to(device) if hasattr(value, "to") else value for key, value in batch.items()}


def _finite(torch: Any, tensor: Any, path: str) -> None:
    f.require(bool(torch.isfinite(tensor).all().item()), path, "contains a nonfinite value")


def run() -> None:
    config = b1_preflight.load_preflight_config(CONFIG_PATH)
    model_root = Path(config["paths"]["model_root"])
    evidence_root = Path(config["paths"]["evidence_root"])
    adapter_root = evidence_root / "adapter"
    f.require(not adapter_root.exists(), "adapter", "output already exists; one-shot run cannot overwrite")

    import torch
    import torch.nn.functional as functional
    import transformers
    import peft
    from peft import LoraConfig, get_peft_model
    from transformers import Qwen2_5_VLForConditionalGeneration

    f.require(torch.cuda.is_available(), "runtime.cuda", "CUDA is unavailable")
    f.literal(torch.cuda.device_count(), "runtime.cuda.device_count", 1)
    visible_devices = f.text(os.environ.get("CUDA_VISIBLE_DEVICES"), "runtime.CUDA_VISIBLE_DEVICES")
    torch.cuda.set_device(0)
    f.literal(torch.cuda.current_device(), "runtime.cuda.current_device", 0)
    device = torch.device("cuda:0")
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats()
    gpu_receipt = parse_nvidia_smi_receipt(subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version,name,memory.total", "--format=csv,noheader,nounits", "-i", "0"],
        check=True, capture_output=True, text=True,
    ).stdout.strip())
    f.literal(gpu_receipt["name"], "runtime.nvidia_smi.name", torch.cuda.get_device_name())

    expected_versions = {"python": config["runtime"]["python"]}
    expected_versions.update({key: config["runtime"][key] for key in _RUNTIME_PACKAGES})
    observed_versions = {"python": platform.python_version()}
    observed_versions.update({key: importlib.metadata.version(distribution) for key, distribution in _RUNTIME_PACKAGES.items()})
    validate_runtime_identity(expected_versions, observed_versions)

    started = time.monotonic()
    processor = load_pil_processor(model_root)
    processor.tokenizer.padding_side = "left"
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_root, local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
        attn_implementation="sdpa", device_map=None,
    ).to(device)
    f.literal(type(model).__name__, "model.class", "Qwen2_5_VLForConditionalGeneration")
    f.literal(model.config._attn_implementation, "model.attention", "sdpa")
    f.literal(processor.tokenizer.padding_side, "processor.padding_side", "left")
    f.require(hasattr(model.model, "visual"), "model.visual", "vision tower is missing")
    model.eval()

    specs = fixture_specs()
    images, fixture_evidence = make_images(specs)
    prompts = ["Describe the synthetic pattern using one short token."] * len(images)
    singles: dict[str, Any] = {}
    with torch.no_grad():
        for spec, image, prompt in zip(specs, images, prompts):
            batch, _ = _encode(processor, [image], [prompt])
            inputs = _device_batch(batch, device)
            output = model(**inputs, use_cache=False, return_dict=True)
            _finite(torch, output.logits, f"forward.{spec['id']}.logits")
            singles[spec["id"]] = output.logits[0, -1, :32].float().cpu()
        batch, _ = _encode(processor, images, prompts)
        inputs = _device_batch(batch, device)
        batched = model(**inputs, use_cache=False, return_dict=True)
        _finite(torch, batched.logits, "forward.batch.logits")
        f.require("mm_token_type_ids" in inputs, "mrope.mm_token_type_ids", "processor omitted modality token types")
        position_ids, rope_deltas = model.model.get_rope_index(
            inputs["input_ids"], mm_token_type_ids=inputs["mm_token_type_ids"],
            image_grid_thw=inputs.get("image_grid_thw"), attention_mask=inputs["attention_mask"],
        )
        temporal_counts = []
        for row_index in range(inputs["input_ids"].shape[0]):
            image_mask = (inputs["mm_token_type_ids"][row_index] == 1) & inputs["attention_mask"][row_index].bool()
            f.require(bool(image_mask.any().item()), f"mrope.row[{row_index}]", "contains no image tokens")
            temporal_counts.append(int(torch.unique(position_ids[0, row_index][image_mask]).numel()))
        grid_temporal = [int(value) for value in inputs["image_grid_thw"][:, 0].detach().cpu().tolist()]
        mrope_summary = validate_mrope_summary({
            "position_shape": list(position_ids.shape), "position_dtype": str(position_ids.dtype),
            "rope_deltas_shape": list(rope_deltas.shape), "rope_deltas_dtype": str(rope_deltas.dtype),
            "image_temporal_unique_counts": temporal_counts, "image_grid_temporal_counts": grid_temporal,
            "position_sha256": _tensor_sha(position_ids), "rope_deltas_sha256": _tensor_sha(rope_deltas),
        }, len(images), inputs["input_ids"].shape[1])
        image_token_counts = [
            int(((inputs["mm_token_type_ids"][index] == 1) & inputs["attention_mask"][index].bool()).sum().item())
            for index in range(len(images))
        ]
        geometry_records = build_geometry_records(
            fixture_evidence,
            inputs["image_grid_thw"].detach().cpu().tolist(),
            image_token_counts,
            int(processor.image_processor.patch_size),
            int(processor.image_processor.merge_size),
        )
        batch_deltas = {}
        for index, spec in enumerate(specs):
            delta = float((batched.logits[index, -1, :32].float().cpu() - singles[spec["id"]]).abs().max().item())
            f.require(delta <= LOGIT_ATOL, f"forward.batch.{spec['id']}", "single/batch logit drift exceeds tolerance")
            batch_deltas[spec["id"]] = delta
        reverse_batch, _ = _encode(processor, list(reversed(images)), list(reversed(prompts)))
        reverse = model(**_device_batch(reverse_batch, device), use_cache=False, return_dict=True)
        reverse_delta = float((reverse.logits[-1, -1, :32].float().cpu() - singles[specs[0]["id"]]).abs().max().item())
        f.require(reverse_delta <= LOGIT_ATOL, "forward.reverse_order", "call-order drift exceeds tolerance")
        visual_delta = float((singles[specs[0]["id"]] - singles[specs[1]["id"]]).abs().max().item())
        f.require(visual_delta > 0.0, "forward.visual_intervention", "changed image did not change declared logits")

        cache_batch, _ = _encode(processor, [images[0]], [prompts[0]])
        cache_inputs = _device_batch(cache_batch, device)
        model.model.rope_deltas = None
        cached_prefill = model(**cache_inputs, use_cache=True, return_dict=True)
        cached_rope = model.model.rope_deltas.detach().clone()
        f.require(cached_prefill.past_key_values is not None, "cache.prefill", "dynamic cache was not returned")
        model.model.rope_deltas = None
        uncached_prefill = model(**cache_inputs, use_cache=False, return_dict=True)
        prefill_delta = compare_logits(
            cached_prefill.logits[0, -1, :32].float().cpu().tolist(),
            uncached_prefill.logits[0, -1, :32].float().cpu().tolist(), LOGIT_ATOL, "cache.prefill",
        )
        model.model.rope_deltas = None
        repeated_prefill = model(**cache_inputs, use_cache=False, return_dict=True)
        repeat_delta = compare_logits(
            uncached_prefill.logits[0, -1, :32].float().cpu().tolist(),
            repeated_prefill.logits[0, -1, :32].float().cpu().tolist(), LOGIT_ATOL, "cache.repeated_prefill",
        )
        text_messages = [{"role": "user", "content": [{"type": "text", "text": "Return one plain token."}]}]
        text_prompt = processor.apply_chat_template(text_messages, tokenize=False, add_generation_prompt=True)
        text_batch = processor(text=[text_prompt], padding=True, return_tensors="pt")
        model.model.rope_deltas = None
        text_output = model(**_device_batch(text_batch, device), use_cache=False, return_dict=True)
        _finite(torch, text_output.logits, "cache.text_interleave.logits")
        model.model.rope_deltas = None
        post_text_prefill = model(**cache_inputs, use_cache=False, return_dict=True)
        text_interleave_delta = compare_logits(
            uncached_prefill.logits[0, -1, :32].float().cpu().tolist(),
            post_text_prefill.logits[0, -1, :32].float().cpu().tolist(), LOGIT_ATOL, "cache.text_interleave",
        )
        next_token = uncached_prefill.logits[:, -1, :].argmax(dim=-1, keepdim=True)
        full_ids = torch.cat([cache_inputs["input_ids"], next_token], dim=1)
        full_attention = torch.cat([cache_inputs["attention_mask"], torch.ones_like(next_token)], dim=1)
        full_mm_types = torch.cat([cache_inputs["mm_token_type_ids"], torch.zeros_like(next_token)], dim=1)
        model.model.rope_deltas = cached_rope
        step_position_ids = model._prepare_position_ids_for_generation(
            full_ids, {"attention_mask": full_attention, "past_key_values": cached_prefill.past_key_values}
        )[..., -1:]
        cached_step = model(
            input_ids=next_token, attention_mask=full_attention, past_key_values=cached_prefill.past_key_values,
            position_ids=step_position_ids, use_cache=True, return_dict=True,
        )
        model.model.rope_deltas = None
        full_inputs = dict(cache_inputs)
        full_inputs["input_ids"] = full_ids
        full_inputs["attention_mask"] = full_attention
        full_inputs["mm_token_type_ids"] = full_mm_types
        uncached_step = model(**full_inputs, use_cache=False, return_dict=True)
        step_delta = compare_logits(
            cached_step.logits[0, -1, :32].float().cpu().tolist(),
            uncached_step.logits[0, -1, :32].float().cpu().tolist(), LOGIT_ATOL, "cache.first_step",
        )
        cache_summary = {
            "class": type(cached_prefill.past_key_values).__name__, "prefill_max_abs": prefill_delta,
            "repeat_max_abs": repeat_delta, "text_interleave_max_abs": text_interleave_delta,
            "first_step_max_abs": step_delta, "tolerance": LOGIT_ATOL,
        }

    train_images = [images[0], images[2]]
    train_prompts = ["Name the synthetic pattern.", "Name this different synthetic pattern briefly."]
    targets = [" blue", " striped"]
    training_batch, prompt_counts = _encode(processor, train_images, train_prompts, targets)
    label_rows = build_target_only_labels(training_batch["input_ids"].tolist(), training_batch["attention_mask"].tolist(), prompt_counts)
    training_batch["labels"] = torch.tensor(label_rows, dtype=torch.long)
    training_inputs = _device_batch(training_batch, device)

    targets_exact = exact_lora_targets(name for name, _ in model.named_modules())
    lora = LoraConfig(r=2, lora_alpha=4, lora_dropout=0.0, bias="none", target_modules=targets_exact, task_type="CAUSAL_LM")
    model = get_peft_model(model, lora)
    declared = sorted(name for name, parameter in model.named_parameters() if parameter.requires_grad)
    f.require(bool(declared), "parameters.declared", "adapter exposes no trainable parameters")
    before = {name: parameter.detach().cpu().clone() for name, parameter in model.named_parameters() if parameter.requires_grad}
    optimizer = torch.optim.AdamW([parameter for parameter in model.parameters() if parameter.requires_grad], lr=1e-4, weight_decay=0.0)
    model.train()
    optimizer.zero_grad(set_to_none=True)
    output = model(**training_inputs, use_cache=False, return_dict=True)
    _finite(torch, output.logits, "training.logits")
    _finite(torch, output.loss, "training.loss")
    shifted_logits = output.logits[..., :-1, :].contiguous().float()
    shifted_labels = training_inputs["labels"][..., 1:].contiguous()
    manual_loss = functional.cross_entropy(shifted_logits.view(-1, shifted_logits.size(-1)), shifted_labels.view(-1), ignore_index=-100)
    loss_delta = float((manual_loss - output.loss.float()).abs().item())
    f.require(loss_delta <= LOSS_ATOL, "training.loss", "manual shifted CE disagrees with framework loss")
    output.loss.backward()
    full_gradients = {
        name: parameter.grad.detach().float().cpu().clone()
        for name, parameter in model.named_parameters() if parameter.requires_grad and parameter.grad is not None
    }
    full_loss_value = float(output.loss.detach().float().item())
    total_target_tokens = int((shifted_labels != -100).sum().item())
    f.require(total_target_tokens > 0, "microbatch.target_tokens", "full batch has no target tokens")
    optimizer.zero_grad(set_to_none=True)
    accumulated_loss_value = 0.0
    for micro_index, (image, prompt, target) in enumerate(zip(train_images, train_prompts, targets)):
        micro_batch, micro_prompt_counts = _encode(processor, [image], [prompt], [target])
        micro_labels = build_target_only_labels(
            micro_batch["input_ids"].tolist(), micro_batch["attention_mask"].tolist(), micro_prompt_counts
        )
        micro_batch["labels"] = torch.tensor(micro_labels, dtype=torch.long)
        micro_inputs = _device_batch(micro_batch, device)
        micro_target_tokens = int((micro_inputs["labels"][..., 1:] != -100).sum().item())
        f.require(micro_target_tokens > 0, f"microbatch[{micro_index}].target_tokens", "contains no target tokens")
        weight = micro_target_tokens / total_target_tokens
        micro_output = model(**micro_inputs, use_cache=False, return_dict=True)
        _finite(torch, micro_output.loss, f"microbatch[{micro_index}].loss")
        accumulated_loss_value += float(micro_output.loss.detach().float().item()) * weight
        (micro_output.loss * weight).backward()
    gradient_deltas = {}
    full_gradient_l2_sq = 0.0
    micro_gradient_l2_sq = 0.0
    gradient_diff_l2_sq = 0.0
    gradient_dot = 0.0
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            f.require(parameter.grad is not None and name in full_gradients,
                      f"microbatch.{name}.gradient", "gradient is missing")
            full_gradient = full_gradients[name].double()
            micro_gradient = parameter.grad.detach().double().cpu()
            difference = micro_gradient - full_gradient
            gradient_deltas[name] = float(difference.abs().max().item())
            full_gradient_l2_sq += float((full_gradient * full_gradient).sum().item())
            micro_gradient_l2_sq += float((micro_gradient * micro_gradient).sum().item())
            gradient_diff_l2_sq += float((difference * difference).sum().item())
            gradient_dot += float((full_gradient * micro_gradient).sum().item())
    full_gradient_l2 = math.sqrt(full_gradient_l2_sq)
    micro_gradient_l2 = math.sqrt(micro_gradient_l2_sq)
    f.require(full_gradient_l2 > 0 and micro_gradient_l2 > 0, "microbatch.gradient_norm", "must be positive")
    gradient_relative_l2 = math.sqrt(gradient_diff_l2_sq) / max(full_gradient_l2, micro_gradient_l2)
    gradient_cosine = gradient_dot / (full_gradient_l2 * micro_gradient_l2)
    microbatch_summary = validate_microbatch_equivalence(
        full_loss_value, accumulated_loss_value,
        dict(sorted(gradient_deltas.items(), key=lambda item: item[0].encode("utf-8"))),
        gradient_relative_l2, gradient_cosine,
        MICROBATCH_LOSS_ATOL, MICROBATCH_GRAD_ATOL,
        MICROBATCH_GRAD_RTOL, MICROBATCH_GRAD_COSINE_MIN,
    )
    # The microbatch pass is diagnostic only. Restore the declared one-step,
    # full-batch training path before the optimizer consumes any gradients.
    optimizer.zero_grad(set_to_none=True)
    optimizer_output = model(**training_inputs, use_cache=False, return_dict=True)
    _finite(torch, optimizer_output.loss, "training.optimizer_loss")
    optimizer_loss_delta = float((optimizer_output.loss.float() - output.loss.float()).abs().item())
    f.require(optimizer_loss_delta <= LOSS_ATOL, "training.optimizer_loss",
              "repeated full-batch loss exceeds tolerance")
    optimizer_output.loss.backward()
    gradient_names = []
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            f.require(parameter.grad is not None, f"parameters.{name}.gradient", "gradient is missing")
            _finite(torch, parameter.grad, f"parameters.{name}.gradient")
            gradient_names.append(name)
    optimizer.step()
    updated = []
    for name, parameter in model.named_parameters():
        if parameter.requires_grad and not torch.equal(before[name], parameter.detach().cpu()):
            updated.append(name)
    expected_updated = sorted(name for name in declared if ".lora_B." in name)
    f.require(len(expected_updated) * 2 == len(declared), "parameters.expected_updated",
              "standard zero-B LoRA must expose one A and one B matrix per target")
    inventory = validate_update_inventory(
        declared, declared, sorted(gradient_names), sorted(updated), expected_updated
    )
    parameter_records = []
    for name, parameter in model.named_parameters():
        if parameter.requires_grad:
            parameter_records.append({
                "name": name,
                "shape": list(parameter.shape),
                "parameter_dtype": str(parameter.dtype),
                "gradient_dtype": str(parameter.grad.dtype),
                "gradient_max_abs": float(parameter.grad.detach().float().abs().max().item()),
                "updated": name in updated,
            })
    optimizer_state_records = []
    for parameter_name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        state = optimizer.state[parameter]
        for key in sorted(state, key=lambda value: str(value).encode("utf-8")):
            value = state[key]
            if torch.is_tensor(value):
                _finite(torch, value, f"optimizer.{parameter_name}.{key}")
                optimizer_state_records.append({
                    "parameter": parameter_name, "state": key,
                    "shape": list(value.shape), "dtype": str(value.dtype),
                })

    model.eval()
    reload_batch, _ = _encode(processor, [images[0]], [prompts[0]])
    reload_inputs = _device_batch(reload_batch, device)
    with torch.no_grad():
        reload_output = model(**reload_inputs, use_cache=False, return_dict=True)
        model.get_base_model().model.rope_deltas = None
        generated = model.generate(
            **reload_inputs, max_new_tokens=3, do_sample=False, use_cache=True,
            return_dict_in_generate=True, output_scores=True,
        )
        generated_ids = generated.sequences[0].tolist()
        generated_suffix = generated.sequences[:, reload_batch["input_ids"].shape[1]:]
        teacher_deltas = []
        for step_index, score in enumerate(generated.scores):
            prefix = generated_suffix[:, :step_index]
            teacher_inputs = dict(reload_inputs)
            if prefix.shape[1]:
                teacher_inputs["input_ids"] = torch.cat([reload_inputs["input_ids"], prefix], dim=1)
                teacher_inputs["attention_mask"] = torch.cat(
                    [reload_inputs["attention_mask"], torch.ones_like(prefix)], dim=1
                )
                teacher_inputs["mm_token_type_ids"] = torch.cat(
                    [reload_inputs["mm_token_type_ids"], torch.zeros_like(prefix)], dim=1
                )
            model.get_base_model().model.rope_deltas = None
            teacher = model(**teacher_inputs, use_cache=False, return_dict=True)
            teacher_deltas.append(compare_logits(
                score[0, :32].float().cpu().tolist(), teacher.logits[0, -1, :32].float().cpu().tolist(),
                LOGIT_ATOL, f"generation.teacher_forced[{step_index}]",
            ))
        model.get_base_model().model.rope_deltas = None
        repeated_generated = model.generate(
            **reload_inputs, max_new_tokens=3, do_sample=False, use_cache=True,
            return_dict_in_generate=True, output_scores=False,
        )
        f.literal(repeated_generated.sequences[0].tolist(), "generation.repeated_ids", generated_ids)
    reload_logits = reload_output.logits[0, -1, :32].float().cpu()
    reload_reference = {
        "fixture_id": specs[0]["id"], "prompt": prompts[0],
        "input_ids": reload_batch["input_ids"][0].tolist(),
        "attention_mask": reload_batch["attention_mask"][0].tolist(),
        "logits_first_32": reload_logits.tolist(), "logit_atol": LOGIT_ATOL,
        "pixel_values_sha256": _tensor_sha(reload_batch["pixel_values"]),
        "generated_ids": generated_ids,
    }

    adapter_root.mkdir(mode=0o700)
    model.save_pretrained(adapter_root, safe_serialization=True)
    generated_card = adapter_root / "README.md"
    if generated_card.exists():
        f.require(generated_card.is_file() and not generated_card.is_symlink(), "adapter.README.md", "must be a regular file")
        generated_card.unlink()
    write_exact_adapter_scope(adapter_root, targets_exact, str(model_root))
    from safetensors import safe_open
    with safe_open(adapter_root / "adapter_model.safetensors", framework="pt", device="cpu") as stream:
        adapter_state_keys = validate_adapter_state_keys(list(stream.keys()), targets_exact)
    adapter_files = inventory_adapter(adapter_root)

    grid = training_inputs.get("image_grid_thw")
    elapsed_seconds = time.monotonic() - started
    properties = torch.cuda.get_device_properties(0)
    model_dtype_counts: dict[str, dict[str, int]] = {}
    for _, parameter in model.named_parameters():
        dtype = str(parameter.dtype)
        entry = model_dtype_counts.setdefault(dtype, {"tensors": 0, "elements": 0})
        entry["tensors"] += 1
        entry["elements"] += parameter.numel()
    result = {
        "schema": "mmbu.b1.native_preflight.result.v1", "status": "native_step_complete_offline_reload_pending",
        "seed": SEED, "synthetic_only": True, "optimizer_steps": 1,
        "model": {"class": type(model.get_base_model()).__name__, "dtype": "bfloat16", "attention": "sdpa"},
        "processor": {"class": type(processor).__name__, "image_processor_class": type(processor.image_processor).__name__, "padding_side": processor.tokenizer.padding_side},
        "fixtures": fixture_evidence,
        "processed": {"image_grid_thw": grid.detach().cpu().tolist() if grid is not None else None,
                      "pixel_values_sha256": _tensor_sha(training_inputs["pixel_values"]),
                      "geometry": geometry_records},
        "mrope": mrope_summary,
        "cache": cache_summary,
        "generation": {"new_tokens": 3, "generated_ids": generated_ids,
                       "teacher_forced_max_abs_by_step": teacher_deltas, "tolerance": LOGIT_ATOL},
        "forward": {"single_batch_max_abs": batch_deltas, "reverse_order_max_abs": reverse_delta,
                    "visual_intervention_max_abs": visual_delta, "tolerance": LOGIT_ATOL},
        "training": {"loss": float(output.loss.detach().float().item()), "manual_loss": float(manual_loss.detach().item()),
                     "loss_abs_delta": loss_delta, "loss_tolerance": LOSS_ATOL, "inventory": inventory,
                     "microbatch_equivalence": microbatch_summary,
                     "optimizer_full_batch_loss": float(optimizer_output.loss.detach().float().item()),
                     "optimizer_full_batch_loss_abs_delta": optimizer_loss_delta,
                     "parameter_records": parameter_records,
                     "optimizer_state_records": optimizer_state_records,
                     "logits_dtype": str(output.logits.dtype), "loss_dtype": str(output.loss.dtype)},
        "adapter_files": adapter_files,
        "adapter_state_keys": adapter_state_keys,
        "reload_reference": reload_reference,
        "resources": {"elapsed_seconds": elapsed_seconds,
                      "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                      "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
                      "gpu_name": torch.cuda.get_device_name(),
                      "cuda_visible_devices": visible_devices,
                      "cuda_runtime": torch.version.cuda,
                      "compute_capability": list(torch.cuda.get_device_capability()),
                      "gpu_total_memory_bytes": properties.total_memory,
                      "gpu_multiprocessor_count": properties.multi_processor_count,
                      "nvidia_smi": gpu_receipt,
                      "fixtures_per_second": len(specs) / elapsed_seconds,
                      "slurm_job_id": f.text(os.environ.get("SLURM_JOB_ID"), "runtime.SLURM_JOB_ID"),
                      "argv": sys.argv},
        "versions": observed_versions,
        "model_parameter_dtype_counts": model_dtype_counts,
    }
    _write_json(evidence_root / "native-preflight.json", result)


if __name__ == "__main__":
    try:
        run()
    except f.ContractViolation as exc:
        sys.stderr.write(str(exc) + "\n")
        raise SystemExit(2)
