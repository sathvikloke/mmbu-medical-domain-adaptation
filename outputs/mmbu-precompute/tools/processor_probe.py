#!/usr/bin/env python3
"""CPU-only native processor probes; never instantiate a model or download weights.

Download mode fetches a fixed list of data/config files at a full commit SHA.
All AutoProcessor loads use local_files_only=True and trust_remote_code=False.
Offline is the default. The report records missing dependencies/artifacts explicitly.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import logging
import os
from pathlib import Path
import platform
import re
import sys
import urllib.error
import urllib.request
import warnings


PACKAGE = Path(__file__).resolve().parents[1]
FILES = (
    "config.json", "preprocessor_config.json", "video_preprocessor_config.json",
    "processor_config.json", "tokenizer_config.json", "tokenizer.json", "vocab.json",
    "merges.txt", "special_tokens_map.json", "added_tokens.json",
    "chat_template.json", "chat_template.jinja",
)
REQUIRED = {"config.json", "preprocessor_config.json", "tokenizer_config.json", "tokenizer.json"}
MAX_FILE_BYTES = 40 * 1024 * 1024
MAX_MODEL_BYTES = 96 * 1024 * 1024
DEPENDENCIES = {"transformers": "transformers", "torch": "torch", "torchvision": "torchvision",
                "numpy": "numpy", "Pillow": "PIL", "tokenizers": "tokenizers",
                "huggingface-hub": "huggingface_hub"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def validate_identity(model_id: str, revision: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", model_id):
        raise ValueError("model_id must be an owner/name without path traversal")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("revision must be a full lowercase 40-character commit SHA")


def artifacts(model: dict, root: Path, download: bool) -> tuple[Path, dict]:
    model_id, revision = model["model_id"], model["revision"]
    validate_identity(model_id, revision)
    directory = root / model_id.replace("/", "--") / revision
    manifest_path = directory / "artifact-manifest.json"
    if download:
        directory.mkdir(parents=True, exist_ok=True)
        records = []
        total = 0
        for filename in FILES:
            url = f"https://huggingface.co/{model_id}/resolve/{revision}/{filename}"
            try:
                with urllib.request.urlopen(url, timeout=60) as response:
                    data = response.read(MAX_FILE_BYTES + 1)
                if len(data) > MAX_FILE_BYTES:
                    raise ValueError(f"artifact exceeds {MAX_FILE_BYTES} bytes: {filename}")
                total += len(data)
                if total > MAX_MODEL_BYTES:
                    raise ValueError("per-model artifact download limit exceeded")
                (directory / filename).write_bytes(data)
                records.append({"filename": filename, "url": url, "bytes": len(data),
                                "sha256": sha256(data), "status": "downloaded"})
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
                records.append({"filename": filename, "url": url, "status": "http_404"})
        manifest = {"model_id": model_id, "revision": revision,
                    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "files": records}
        dump(manifest_path, manifest)
    if not manifest_path.exists():
        raise FileNotFoundError(f"offline artifact manifest missing: {manifest_path}; use --download")
    manifest = json.loads(manifest_path.read_text())
    if (manifest.get("model_id"), manifest.get("revision")) != (model_id, revision):
        raise ValueError("artifact identity disagrees with selected model/revision")
    observed = set()
    for item in manifest["files"]:
        filename = item["filename"]
        if filename not in FILES or filename in observed:
            raise ValueError("unexpected or duplicate filename in artifact manifest")
        observed.add(filename)
        path = directory / filename
        if item["status"] == "downloaded":
            data = path.read_bytes()
            if sha256(data) != item["sha256"] or len(data) != item["bytes"]:
                raise ValueError(f"artifact hash/size mismatch: {filename}")
        elif item["status"] == "http_404":
            if path.exists():
                raise ValueError(f"unexpected local artifact marked unavailable: {filename}")
        else:
            raise ValueError("unknown artifact status")
    present = {item["filename"] for item in manifest["files"] if item["status"] == "downloaded"}
    if not REQUIRED <= present:
        raise FileNotFoundError(f"required processor artifacts missing: {sorted(REQUIRED - present)}")
    unexpected = {p.name for p in directory.iterdir()} - present - {"artifact-manifest.json"}
    if unexpected:
        raise ValueError(f"unexpected files in processor-only directory: {sorted(unexpected)}")
    if not any(name in present for name in ("chat_template.json", "chat_template.jinja")):
        # Some checkpoints embed their template in tokenizer_config.json.
        if not json.loads((directory / "tokenizer_config.json").read_text()).get("chat_template"):
            raise ValueError("no native chat template found")
    return directory, manifest


@contextmanager
def capture():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("transformers")
    logger.addHandler(handler)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = {"python_warnings": [], "transformers_log": ""}
        try:
            yield result
        finally:
            result["python_warnings"] = [str(w.message) for w in caught]
            result["transformers_log"] = stream.getvalue()
            logger.removeHandler(handler)


def array_summary(value) -> dict:
    import numpy as np
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    array = np.ascontiguousarray(value)
    result = {"shape": list(array.shape), "dtype": str(array.dtype),
              "sha256": sha256(array.tobytes()), "finite": bool(np.isfinite(array).all())}
    if array.size:
        result.update(min=float(array.min()), max=float(array.max()), mean=float(array.mean()))
    return result


def encode_case(processor, rendered: str, picture, **kwargs) -> dict:
    import numpy as np
    with capture() as captured:
        try:
            encoded = processor(text=[rendered], images=[picture], return_tensors="pt",
                                device="cpu", **kwargs)
            repeated = processor(text=[rendered], images=[picture], return_tensors="pt",
                                 device="cpu", **kwargs)
            summary = {key: array_summary(value) for key, value in encoded.items()}
            grids = encoded["image_grid_thw"].tolist()
            merge = processor.image_processor.merge_size
            expected = sum(int(np.prod(grid)) // (merge * merge) for grid in grids)
            image_token_id = processor.tokenizer.convert_tokens_to_ids(processor.image_token)
            actual = int((encoded["input_ids"] == image_token_id).sum())
            checks = {"deterministic_all_outputs": all(
                key in repeated and array_summary(repeated[key]) == value for key, value in summary.items()),
                "image_token_count_matches_grid": expected == actual,
                "finite_all_outputs": all(value["finite"] for value in summary.values()),
                "all_tensors_cpu": all(str(value.device) == "cpu" for value in encoded.values())}
            result = {"status": "passed" if all(checks.values()) else "failed", "checks": checks,
                      "arrays": summary, "image_grid_thw": grids,
                      "image_token_id": image_token_id, "image_token_count": actual,
                      "grid_token_count": expected,
                      "resized_hw_from_grid": [[grid[1] * processor.image_processor.patch_size,
                                                grid[2] * processor.image_processor.patch_size]
                                               for grid in grids]}
        except Exception as error:
            result = {"status": "rejected", "error_type": type(error).__name__, "error": str(error)}
    result["warnings"] = captured
    return result


def make_messages(selected: dict, context: bool = False) -> list:
    """Synthetic harness adapter; deliberately only accepts selector output fields."""
    text = ("Describe these requested fields: " + ", ".join(selected["requested_fields"])) if context else selected["question"]
    return [{"role": "system", "content": selected["system_prompt"]},
            {"role": "user", "content": [{"type": "image"}, {"type": "text", "text": text}]}]


def assistant_alignment(processor, messages: list, picture, template_kwargs: dict) -> dict:
    """Measure native token prefix; expose a boundary only when it is exact."""
    answer = '{"answer": "synthetic"}'
    full_messages = messages + [{"role": "assistant", "content": answer}]
    with capture() as captured:
        try:
            prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                                   **template_kwargs)
            full = processor.apply_chat_template(full_messages, tokenize=False, add_generation_prompt=False,
                                                 **template_kwargs)
            def encode(text):
                return processor(text=[text], images=[picture], return_tensors="pt", device="cpu")
            prompt_encoded, full_encoded = encode(prompt), encode(full)
            prompt_ids, full_ids = prompt_encoded["input_ids"][0].tolist(), full_encoded["input_ids"][0].tolist()
            integrated_checks = {}
            for name, conversation, generation, split_encoded in (
                ("prompt", messages, True, prompt_encoded), ("full", full_messages, False, full_encoded)):
                multimodal = deepcopy(conversation)
                for message in multimodal:
                    if isinstance(message["content"], list):
                        for block in message["content"]:
                            if block["type"] == "image":
                                block["image"] = picture
                integrated = processor.apply_chat_template(
                    multimodal, tokenize=True, add_generation_prompt=generation,
                    return_dict=True, return_tensors="pt", processor_kwargs={"device": "cpu"}, **template_kwargs)
                integrated_checks[name] = set(integrated) == set(split_encoded) and all(
                    array_summary(integrated[key]) == array_summary(value) for key, value in split_encoded.items())
            prefix = full_ids[:len(prompt_ids)] == prompt_ids
            suffix = full_ids[len(prompt_ids):] if prefix else None
            first_diff = next((i for i, (a, b) in enumerate(zip(prompt_ids, full_ids)) if a != b),
                              min(len(prompt_ids), len(full_ids)))
            result = {"status": "exact_prefix" if prefix else "prefix_mismatch_do_not_infer_mask",
                      "template_kwargs": template_kwargs, "toy_response": answer,
                      "prompt_rendered": prompt, "full_rendered": full,
                      "prompt_tokens": len(prompt_ids), "full_tokens": len(full_ids),
                      "prompt_token_ids": prompt_ids, "full_token_ids": full_ids,
                      "prompt_is_exact_token_prefix": prefix,
                      "integrated_chat_encode_equals_split_render_encode": integrated_checks,
                      "first_divergence_index": None if prefix else first_diff,
                      "native_suffix_token_ids": suffix,
                      "native_suffix_decoded": processor.tokenizer.decode(suffix, skip_special_tokens=False) if prefix else None,
                      "assistant_label_start": len(prompt_ids) if prefix else None,
                      "eos_token": processor.tokenizer.eos_token,
                      "eos_token_id": processor.tokenizer.eos_token_id,
                      "native_suffix_contains_eos": processor.tokenizer.eos_token_id in suffix if prefix else None,
                      "label_scope": "native assistant suffix including any end/newline tokens; no model/training or production mask"}
        except Exception as error:
            result = {"status": "unavailable", "template_kwargs": template_kwargs,
                      "error_type": type(error).__name__, "error": str(error)}
    result["warnings"] = captured
    return result


def probe(model: dict, directory: Path) -> dict:
    import numpy as np
    from PIL import Image, ImageDraw
    from jinja2 import Environment, meta
    import torch
    from transformers import AutoProcessor
    sys.path.insert(0, str(PACKAGE / "src"))
    from mmbu_prep.contracts import build_context_input, build_task_input
    torch.set_num_threads(1)
    with capture() as loader_warnings:
        processor = AutoProcessor.from_pretrained(directory, local_files_only=True, trust_remote_code=False)
    image_processor = processor.image_processor
    template_variables = meta.find_undeclared_variables(Environment().parse(processor.chat_template))
    supports_thinking = "enable_thinking" in template_variables
    result = {"processor_class": type(processor).__name__, "tokenizer_class": type(processor.tokenizer).__name__,
              "image_processor_class": type(image_processor).__name__, "loader_warnings": loader_warnings,
              "native_image_processor_config": image_processor.to_dict(),
              "native_template_variables": sorted(template_variables),
              "enable_thinking_template_variable": supports_thinking,
              "native_chat_template_sha256": sha256(processor.chat_template.encode())}
    record = {"image_path": "synthetic://rgb", "question": "TASK_ONLY_517: Count the drawn squares.",
              "options": ["OPTION_POISON_682"], "answer": "ANSWER_POISON_349",
              "context": {"modality": "CONTEXT_POISON_207"}, "history": ["HISTORY_POISON_923"],
              "previous_prediction": "PREDICTION_POISON_815", "messages": ["MESSAGES_POISON_270"]}
    altered = dict(record, answer="ALTERED_ANSWER", options=["ALTERED_OPTION"],
                   context={"modality": "ALTERED_CONTEXT"}, history=["ALTERED_HISTORY"],
                   previous_prediction="ALTERED_PREDICTION", messages=["ALTERED_MESSAGES"])
    task = make_messages(build_task_input(record, "Synthetic task probe. Do not use prior requests."))
    context = make_messages(build_context_input(record, ["modality", "stain"], "Synthetic context probe."), True)
    task2 = make_messages(build_task_input(altered, "Synthetic task probe. Do not use prior requests."))
    context2 = make_messages(build_context_input(dict(altered, question="ALTERED_QUESTION"),
                                              ["modality", "stain"], "Synthetic context probe."), True)
    rendered = processor.apply_chat_template(task, tokenize=False, add_generation_prompt=True)
    context_rendered = processor.apply_chat_template(context, tokenize=False, add_generation_prompt=True)
    task2_rendered = processor.apply_chat_template(task2, tokenize=False, add_generation_prompt=True)
    context2_rendered = processor.apply_chat_template(context2, tokenize=False, add_generation_prompt=True)
    no_generation = processor.apply_chat_template(task, tokenize=False, add_generation_prompt=False)
    no_thinking = processor.apply_chat_template(task, tokenize=False, add_generation_prompt=True,
                                              enable_thinking=False) if supports_thinking else None
    tokens = lambda text: processor.tokenizer(text, add_special_tokens=False)["input_ids"]
    poison_values = ["OPTION_POISON_682", "ANSWER_POISON_349", "CONTEXT_POISON_207", "HISTORY_POISON_923",
                     "PREDICTION_POISON_815", "MESSAGES_POISON_270"]
    checks = {"task_reference_invariant": tokens(rendered) == tokens(task2_rendered),
              "context_task_and_reference_invariant": tokens(context_rendered) == tokens(context2_rendered),
              "context_excludes_task_question": "TASK_ONLY_517" not in context_rendered,
              "both_exclude_poison_values": all(s not in rendered + context_rendered for s in poison_values),
              "one_image_placeholder_each": rendered.count(processor.image_token) == context_rendered.count(processor.image_token) == 1,
              "generation_prompt_changes_render": rendered != no_generation,
              "render_and_tokenizer_repeat_deterministic": rendered == processor.apply_chat_template(task, tokenize=False, add_generation_prompt=True)
              and tokens(rendered) == tokens(rendered)}
    result["chat"] = {"checks": checks, "task_rendered": rendered, "context_rendered": context_rendered,
                      "without_generation_prompt": no_generation, "thinking_disabled_rendered": no_thinking,
                      "generation_suffix": rendered[len(no_generation):] if rendered.startswith(no_generation) else None,
                      "task_text_token_ids": tokens(rendered), "context_text_token_ids": tokens(context_rendered)}
    alignment_image = Image.new("RGB", (64, 64), (31, 67, 109))
    result["assistant_alignment"] = {
        "native_default": assistant_alignment(processor, task, alignment_image, {}),
        "thinking_disabled": assistant_alignment(processor, task, alignment_image, {"enable_thinking": False})
        if supports_thinking else {"status": "unsupported_template_variable", "template_kwargs": {"enable_thinking": False}}}
    cases = {}
    for width, height in [(64, 64), (301, 199), (640, 480), (1024, 256), (1600, 1200), (1, 512)]:
        rgb = Image.new("RGB", (width, height), (31, 67, 109))
        draw = ImageDraw.Draw(rgb)
        draw.rectangle((width // 4, height // 4, width // 2, height // 2), fill=(245, 70, 20))
        draw.ellipse((width // 2, height // 2, width * 3 // 4, height * 3 // 4), fill=(30, 230, 65))
        name = f"rgb_{width}x{height}"
        cases[name] = {"input_hw": [height, width], "input_sha256": sha256(rgb.tobytes()),
                       **encode_case(processor, rendered, rgb)}
        if (width, height) == (640, 480):
            cases["rgb_640x480_bounded"] = {"input_hw": [height, width],
                "override": {"size": {"shortest_edge": 4096, "longest_edge": 65536}},
                **encode_case(processor, rendered, rgb, size={"shortest_edge": 4096, "longest_edge": 65536})}
    levels = np.array([0, 1, 255, 256, 1024, 32768, 65535], dtype=np.uint16)
    values = np.tile(np.repeat(levels, 16), (112, 1))
    pil16 = Image.fromarray(values)
    rgb8 = pil16.convert("RGB")
    converted = np.asarray(rgb8)
    hazards = {"synthetic_source_dtype": str(values.dtype), "synthetic_pil_mode": pil16.mode,
               "source_shape": list(values.shape), "source_unique_values": np.unique(values).tolist(),
               "PIL_RGB_unique_values": np.unique(converted).tolist(),
               "PIL_RGB_clips_all_values_above_255": bool(np.all(converted[..., 0][values > 255] == 255)),
               "PIL_RGB_preserves_source_levels": len(np.unique(converted)) == len(np.unique(values)),
               "pil_native16": encode_case(processor, rendered, pil16),
               "pil_explicit_RGB": encode_case(processor, rendered, rgb8),
               "numpy_uint16_2d": encode_case(processor, rendered, values),
               "numpy_uint16_rgb": encode_case(processor, rendered, np.repeat(values[..., None], 3, axis=2)),
               "numpy_float01_rgb_default_rescale": encode_case(processor, rendered, converted.astype(np.float32) / 255),
               "numpy_float01_rgb_without_rescale": encode_case(processor, rendered, converted.astype(np.float32) / 255, do_rescale=False)}
    a = hazards["pil_native16"].get("arrays", {}).get("pixel_values")
    b = hazards["pil_explicit_RGB"].get("arrays", {}).get("pixel_values")
    hazards["native16_equals_explicit_clipped_RGB"] = a == b if a and b else None
    result["rgb_cases"] = cases
    result["native16_hazards"] = hazards
    result["expected_extreme_aspect_rejection"] = cases["rgb_1x512"]["status"] == "rejected" and "aspect ratio" in cases["rgb_1x512"].get("error", "")
    result["integrated_chat_encode_checked"] = all(
        item.get("integrated_chat_encode_equals_split_render_encode") == {"prompt": True, "full": True}
        for item in result["assistant_alignment"].values() if item["status"] != "unsupported_template_variable")
    result["status"] = "passed" if all(checks.values()) and result["expected_extreme_aspect_rejection"] and result["integrated_chat_encode_checked"] and all(
        item["status"] == "passed" for name, item in cases.items() if name != "rgb_1x512") else "failed"
    result["scope"] = "synthetic CPU processor compatibility only; no forward pass, model state, performance, or GPU fit"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=PACKAGE / "configs/model-registry.json")
    parser.add_argument("--artifacts", type=Path, required=True, help="processor-only snapshot/cache directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", action="append", help="select registry model ID; repeat for multiple")
    parser.add_argument("--revision", help="override full commit SHA; requires one explicit --model")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--download", action="store_true", help="allow bounded fixed-list downloads at exact revision")
    mode.add_argument("--offline", action="store_true", help="explicit offline mode (also the default)")
    args = parser.parse_args()
    if not args.download:
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
    if args.revision and (not args.model or len(args.model) != 1):
        parser.error("--revision requires exactly one --model")
    models = json.loads(args.registry.read_text())["models"]
    if args.model:
        unknown = set(args.model) - {m["model_id"] for m in models}
        if unknown:
            parser.error(f"unknown model IDs: {sorted(unknown)}")
        models = [m for m in models if m["model_id"] in args.model]
    if args.revision:
        models = [dict(models[0], revision=args.revision)]
    versions = {}
    missing = []
    for dist, module in DEPENDENCIES.items():
        try:
            versions[dist] = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            versions[dist] = None
        if importlib.util.find_spec(module) is None:
            missing.append(dist)
    report = {"schema_version": 1, "run_at_utc": datetime.now(timezone.utc).isoformat(),
              "python": sys.version, "platform": platform.platform(), "dependency_versions": versions,
              "script_sha256": sha256(Path(__file__).read_bytes()),
              "registry_sha256": sha256(args.registry.read_bytes()), "mode": "download" if args.download else "offline",
              "weight_downloads_allowed": False, "model_instantiation": False, "trust_remote_code": False,
              "missing_dependencies": missing, "models": []}
    for model in models:
        item = {"model_id": model["model_id"], "revision": model["revision"]}
        try:
            validate_identity(model["model_id"], model["revision"])
            if missing:
                item.update(status="unavailable", reason="missing dependencies", missing_dependencies=missing)
            else:
                directory, manifest = artifacts(model, args.artifacts, args.download)
                item["artifact_manifest"] = manifest
                item.update(probe(model, directory))
        except Exception as error:
            item.update(status="unavailable", error_type=type(error).__name__, error=str(error))
        report["models"].append(item)
        print(f"{model['model_id']}: {item['status']}", flush=True)
        dump(args.output, report)
    report["status"] = "passed" if report["models"] and all(m["status"] == "passed" for m in report["models"]) else "incomplete"
    dump(args.output, report)
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
