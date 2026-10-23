#!/usr/bin/env python3
"""One-job, one-step, synthetic-only native B1 GPU preflight."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
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
SEED = 20261023
_LANGUAGE_LORA = re.compile(r"^model\.language_model\.layers\.\d+\.self_attn\.(?:q_proj|v_proj)$")


def fixture_specs() -> list[dict]:
    """Return the prospectively frozen, generated-only image fixture inventory."""
    rows = (
        ("small-rgb", "RGB", [28, 28], 1, "rgb"),
        ("large-rgb", "RGB", [280, 280], 2, "rgb"),
        ("nonsquare-rgb", "RGB", [84, 140], 3, "rgb"),
        ("extreme-aspect-rgb", "RGB", [28, 280], 4, "rgb"),
        ("grayscale-conversion", "L", [84, 84], 5, "convert_rgb"),
        ("rgba-conversion", "RGBA", [84, 84], 6, "composite_white_rgb"),
        ("exif-orientation", "RGB", [84, 140], 7, "transpose_90_cw_rgb"),
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


def validate_update_inventory(declared: list[str], trainable: list[str], gradients: list[str], updated: list[str]) -> dict:
    for label, values in (("declared", declared), ("trainable", trainable), ("gradients", gradients), ("updated", updated)):
        f.require(values == sorted(set(values)), f"parameters.{label}", "must be unique and sorted")
    f.literal(trainable, "parameters.trainable", declared)
    f.literal(gradients, "parameters.gradients", declared)
    f.literal(updated, "parameters.updated", declared)
    return {"declared": declared, "finite_gradients": gradients, "updated": updated}


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


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _tensor_sha(tensor: Any) -> str:
    return _sha(tensor.detach().contiguous().cpu().view(-1).numpy().tobytes())


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical.dumps(value) + b"\n")


def make_images(specs: list[dict]) -> tuple[list[Any], list[dict]]:
    from PIL import Image

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
        elif spec["transform"] == "transpose_90_cw_rgb":
            image = image.transpose(Image.Transpose.ROTATE_270)
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
    device = torch.device("cuda:0")
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats(device)

    expected_versions = config["runtime"]
    observed_versions = {
        "torch": torch.__version__, "transformers": transformers.__version__, "peft": peft.__version__,
    }
    for key, observed in observed_versions.items():
        f.literal(observed, f"runtime.{key}", expected_versions[key])

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
            "repeat_max_abs": repeat_delta, "first_step_max_abs": step_delta, "tolerance": LOGIT_ATOL,
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
    inventory = validate_update_inventory(declared, sorted(gradient_names), sorted(gradient_names), sorted(updated))
    for state in optimizer.state.values():
        for key, value in state.items():
            if torch.is_tensor(value):
                _finite(torch, value, f"optimizer.{key}")

    model.eval()
    reload_batch, _ = _encode(processor, [images[0]], [prompts[0]])
    reload_inputs = _device_batch(reload_batch, device)
    with torch.no_grad():
        reload_output = model(**reload_inputs, use_cache=False, return_dict=True)
    reload_logits = reload_output.logits[0, -1, :32].float().cpu()
    reload_reference = {
        "fixture_id": specs[0]["id"], "prompt": prompts[0],
        "input_ids": reload_batch["input_ids"][0].tolist(),
        "attention_mask": reload_batch["attention_mask"][0].tolist(),
        "logits_first_32": reload_logits.tolist(), "logit_atol": LOGIT_ATOL,
        "pixel_values_sha256": _tensor_sha(reload_batch["pixel_values"]),
    }

    adapter_root.mkdir(mode=0o700)
    model.save_pretrained(adapter_root, safe_serialization=True)
    adapter_files = []
    for path in sorted(adapter_root.iterdir(), key=lambda item: item.name.encode("utf-8")):
        f.require(path.is_file() and not path.is_symlink(), f"adapter.{path.name}", "must be a regular file")
        adapter_files.append({"path": path.name, "bytes": path.stat().st_size, "sha256": _sha(path.read_bytes())})

    grid = training_inputs.get("image_grid_thw")
    result = {
        "schema": "mmbu.b1.native_preflight.result.v1", "status": "native_step_complete_offline_reload_pending",
        "seed": SEED, "synthetic_only": True, "optimizer_steps": 1,
        "model": {"class": type(model.get_base_model()).__name__, "dtype": "bfloat16", "attention": "sdpa"},
        "processor": {"class": type(processor).__name__, "image_processor_class": type(processor.image_processor).__name__, "padding_side": processor.tokenizer.padding_side},
        "fixtures": fixture_evidence,
        "processed": {"image_grid_thw": grid.detach().cpu().tolist() if grid is not None else None,
                      "pixel_values_sha256": _tensor_sha(training_inputs["pixel_values"])},
        "mrope": mrope_summary,
        "cache": cache_summary,
        "forward": {"single_batch_max_abs": batch_deltas, "reverse_order_max_abs": reverse_delta,
                    "visual_intervention_max_abs": visual_delta, "tolerance": LOGIT_ATOL},
        "training": {"loss": float(output.loss.detach().float().item()), "manual_loss": float(manual_loss.detach().item()),
                     "loss_abs_delta": loss_delta, "loss_tolerance": LOSS_ATOL, "inventory": inventory},
        "adapter_files": adapter_files,
        "reload_reference": reload_reference,
        "resources": {"elapsed_seconds": time.monotonic() - started,
                      "peak_allocated_bytes": torch.cuda.max_memory_allocated(device),
                      "peak_reserved_bytes": torch.cuda.max_memory_reserved(device),
                      "gpu_name": torch.cuda.get_device_name(device)},
        "versions": observed_versions,
    }
    _write_json(evidence_root / "native-preflight.json", result)


if __name__ == "__main__":
    try:
        run()
    except f.ContractViolation as exc:
        sys.stderr.write(str(exc) + "\n")
        raise SystemExit(2)
