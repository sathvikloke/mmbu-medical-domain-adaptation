#!/usr/bin/env python3
"""Offline native input encoding for pending ROCO RGB PNGs; no model execution.

The report is an engineering token/preprocessing observation, never data-use
approval, answer grading, image-label validation, or a model-memory estimate.
Only a new output report is written; source files and snapshots remain intact.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import socket
import sys
from unittest.mock import patch
import urllib.request

import processor_probe as helpers


PACKAGE = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT = "Engineering preprocessing probe. This request measures input encoding only. Use only this image and question."
COMMON_BOUND = {"shortest_edge": 65536, "longest_edge": 262144}
MAX_FILE_BYTES = 16 * 1024 * 1024


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def bounded_read(path, limit=MAX_FILE_BYTES):
    """Read at most limit + 1 bytes so ordinary file drift cannot defeat the cap."""
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ValueError("file exceeds probe byte bound")
    return data


def strict_json(text):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("nonfinite JSON value")
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError("nonfinite JSON value")
        return parsed
    return json.loads(text, object_pairs_hook=unique, parse_constant=nonfinite, parse_float=finite_float)


@contextmanager
def denied_network():
    """Deny Python DNS/socket connection/urllib network entry points in-process."""
    attempts = []
    def deny(*args, **kwargs):
        attempts.append("denied network call")
        raise RuntimeError("network access is forbidden in the source processor probe")
    with patch.object(socket, "create_connection", deny), patch.object(socket, "getaddrinfo", deny), \
            patch.object(socket.socket, "connect", deny), patch.object(socket.socket, "connect_ex", deny), \
            patch.object(urllib.request, "urlopen", deny):
        yield attempts


def summarize(values):
    """Exact sample totals plus linear-interpolated empirical percentiles (type 7)."""
    if not values:
        return None
    ordered = sorted(values)
    def quantile(p):
        at = (len(ordered) - 1) * p
        low, high = math.floor(at), math.ceil(at)
        return ordered[low] + (ordered[high] - ordered[low]) * (at - low)
    return {"n": len(values), "min": min(values), "max": max(values),
            "total": sum(values), "mean": math.fsum(values) / len(values),
            "p50": quantile(.5), "p90": quantile(.9), "p95": quantile(.95)}


def run(args):
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    with denied_network() as attempts:
        import torch
        from PIL import Image
        from transformers import AutoProcessor
        sys.path.insert(0, str(PACKAGE / "src"))
        from mmbu_prep.contracts import build_task_input
        from mmbu_prep.images import inspect_images
        torch.set_num_threads(1)
        manifest_bytes = bounded_read(args.manifest)
        rows = [strict_json(line) for line in manifest_bytes.decode("utf-8").splitlines() if line.strip()]
        if len(rows) != args.expected_records:
            raise ValueError(f"expected exactly {args.expected_records} source records, received {len(rows)}")
        if any(not isinstance(row, dict) or row.get("review_status") != "pending"
               or row.get("allowed_purposes") != [] for row in rows):
            raise ValueError("this engineering probe requires pending rows with empty allowed_purposes")
        root = args.image_root.resolve(strict=True)
        inspection = inspect_images(rows, image_root=root, max_pixels=4_000_000, max_file_bytes=MAX_FILE_BYTES)
        if not inspection["ok"]:
            raise ValueError("source image inspection failed: " + json.dumps(inspection["errors"]))
        if any(item["format"] != "PNG" or item["mode"] != "RGB" or item["frames"] != 1
               or item["orientation_requires_transform"] for item in inspection["images"]):
            raise ValueError("only inspected single-frame RGB PNGs with no orientation transform are accepted")
        inspected = {item["record_id"]: item for item in inspection["images"]}
        registry_bytes = bounded_read(args.registry)
        registry = strict_json(registry_bytes.decode("utf-8"))
        if len(registry["models"]) != 3 or len({m["model_id"] for m in registry["models"]}) != 3:
            raise ValueError("the probe requires the three distinct registered candidates")
        policies = {"native_default": {}}
        if args.include_common_bound:
            policies["common_area_65536_262144"] = {"size": COMMON_BOUND}
        report = {
            "schema_version": 1, "kind": "pending_source_native_processor_engineering_probe",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "model_executed": False, "optimization_performed": False, "evaluation_performed": False,
            "source_use_approved": False, "source_status_changed": False, "gpu_used": False,
            "manifest_sha256": sha256(manifest_bytes), "registry_sha256": sha256(registry_bytes),
            "code_sha256": {"tools/source_processor_probe.py": sha256(Path(__file__).read_bytes()),
                            "tools/processor_probe.py": sha256(Path(helpers.__file__).read_bytes()),
                            "src/mmbu_prep/contracts.py": sha256((PACKAGE / "src/mmbu_prep/contracts.py").read_bytes()),
                            "src/mmbu_prep/images.py": sha256((PACKAGE / "src/mmbu_prep/images.py").read_bytes())},
            "environment": {"python": sys.version, "torch": torch.__version__,
                            "transformers": __import__("transformers").__version__,
                            "pillow": Image.__version__, "device": "cpu", "torch_threads": 1},
            "record_count": len(rows), "image_inspection": inspection,
            "system_prompt": SYSTEM_PROMPT, "system_prompt_origin": "provisional synthetic engineering fixture",
            "input_contract": "build_task_input selects image_path/question/caller system prompt only; no assistant answer is encoded",
            "policies": policies, "template_kwargs": {}, "padding": False, "truncation": False,
            "percentile_method": "Hyndman-Fan type 7: sort values; index=(n-1)*p; linearly interpolate adjacent order statistics; no rounding",
            "summary_scope": f"observed {len(rows)}-image engineering sample per model/policy, not a population or performance estimate",
            "models": [],
        }
        for model in registry["models"]:
            result = {"model_id": model["model_id"], "revision": model["revision"], "policies": {}}
            try:
                directory, manifest = helpers.artifacts(model, args.artifacts, download=False)
                result["artifact_manifest"] = manifest
                with helpers.capture() as loader_warnings:
                    processor = AutoProcessor.from_pretrained(directory, local_files_only=True, trust_remote_code=False)
                result.update(processor_class=type(processor).__name__, tokenizer_class=type(processor.tokenizer).__name__,
                              image_processor_class=type(processor.image_processor).__name__,
                              native_image_processor_config=processor.image_processor.to_dict(),
                              chat_template_sha256=sha256(processor.chat_template.encode()),
                              loader_warnings=loader_warnings)
                for policy, kwargs in policies.items():
                    records = []
                    prompts = {}
                    for row in rows:
                        item = inspected[row["record_id"]]
                        image_path = (root / row["image_path"]).resolve(strict=True)
                        if not image_path.is_relative_to(root):
                            raise ValueError("image path escapes inspected root")
                        payload = bounded_read(image_path)
                        if sha256(payload) != item["raw_sha256"]:
                            raise ValueError("image bytes changed after inspection")
                        selected = build_task_input(row, SYSTEM_PROMPT)
                        messages = helpers.make_messages(selected)
                        rendered = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                        poisoned = dict(row)
                        for key in ("answer", "options", "context", "caption", "raw_caption", "pmcid", "source_id",
                                    "source_image_id", "record_id", "history", "messages", "previous_prediction"):
                            poisoned[key] = "EXCLUDED_REFERENCE_SENTINEL_729"
                        clean_render = processor.apply_chat_template(
                            helpers.make_messages(build_task_input(poisoned, SYSTEM_PROMPT)),
                            tokenize=False, add_generation_prompt=True)
                        isolated = rendered == clean_render and "EXCLUDED_REFERENCE_SENTINEL_729" not in rendered
                        prompt_hash = sha256(rendered.encode())
                        prompts[prompt_hash] = rendered
                        with Image.open(io.BytesIO(payload)) as image:
                            image.load()
                            if image.mode != "RGB" or list(image.size) != [item["width"], item["height"]]:
                                raise ValueError("decoded image disagrees with inspection")
                            encoded = helpers.encode_case(processor, rendered, image,
                                                          padding=False, truncation=False, **kwargs)
                        entry = {"record_id": row["record_id"], "image_path": row["image_path"],
                                 "actual_png_sha256": item["raw_sha256"], "pixel_sha256": item["pixel_sha256"],
                                 "original_hw": [item["height"], item["width"]], "mode": item["mode"],
                                 "review_status": row["review_status"], "allowed_purposes": row["allowed_purposes"],
                                 "rendered_prompt_sha256": prompt_hash, "excluded_fields_invariant": isolated,
                                 **encoded}
                        if encoded["status"] == "passed":
                            entry["input_tokens"] = encoded["arrays"]["input_ids"]["shape"][1]
                            entry["visual_tokens"] = encoded["image_token_count"]
                            entry["nonvisual_input_tokens_including_template"] = entry["input_tokens"] - entry["visual_tokens"]
                        if not isolated:
                            entry["status"] = "failed"
                        records.append(entry)
                    successes = [x for x in records if x["status"] == "passed"]
                    result["policies"][policy] = {
                        "status": "passed" if len(successes) == len(rows) else "failed",
                        "records": records, "rendered_prompts": prompts,
                        "summary": {"expected_records": len(rows), "success_count": len(successes),
                                    "failure_count": len(rows) - len(successes),
                                    "visual_tokens": summarize([x["visual_tokens"] for x in successes]),
                                    "input_tokens": summarize([x["input_tokens"] for x in successes]),
                                    "nonvisual_input_tokens_including_template": summarize([x["nonvisual_input_tokens_including_template"] for x in successes])},
                    }
                    print(f"{model['model_id']} / {policy}: {len(successes)}/{len(rows)} encodings passed", flush=True)
                result["status"] = "passed" if all(x["status"] == "passed" for x in result["policies"].values()) else "failed"
            except Exception as error:
                result.update(status="unavailable_or_failed", error_type=type(error).__name__, error=str(error))
            report["models"].append(result)
        unchanged = bounded_read(args.manifest) == manifest_bytes and bounded_read(args.registry) == registry_bytes
        unchanged = unchanged and all(sha256(bounded_read(root / row["image_path"])) == row["image_sha256"] for row in rows)
        report["input_manifest_registry_and_png_bytes_unchanged"] = unchanged
        report["network_guards"] = {"HF_HUB_OFFLINE": True, "TRANSFORMERS_OFFLINE": True,
            "local_files_only": True, "trust_remote_code": False,
            "denied_hooks": ["socket.create_connection", "socket.getaddrinfo", "socket.socket.connect",
                             "socket.socket.connect_ex", "urllib.request.urlopen"], "attempted_calls": len(attempts)}
        report["status"] = "passed" if unchanged and not attempts and all(x["status"] == "passed" for x in report["models"]) else "failed"
        report["limits"] = [
            "Input tensors/token counts only; no model forward, gradients, optimization, answers or evaluation scores.",
            "Processor changes in resolution and visual-token count do not establish retained diagnostic information.",
            "No inference from input-token counts to GPU memory, runtime throughput, model fit or model ranking.",
            "Pending status and empty allowed purposes remain unchanged; this report grants no training, evaluation or release approval.",
            "Totals and percentiles summarize only this deterministic inspection sample and fixed synthetic system prompt.",
        ]
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--image-root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=PACKAGE / "configs/model-registry.json")
    parser.add_argument("--artifacts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New report file; existing output is never overwritten")
    parser.add_argument("--expected-records", type=int, default=24)
    parser.add_argument("--include-common-bound", action="store_true", help="Also probe a shared 65,536–262,144 pixel area range")
    args = parser.parse_args(argv)
    try:
        if args.expected_records < 1:
            raise ValueError("expected-records must be positive")
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError("output already exists")
        report = run(args)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    except (ImportError, OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"status": "unavailable_or_failed", "error_type": type(error).__name__, "error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "records": report["record_count"],
                      "models": len(report["models"]), "network_attempts": report["network_guards"]["attempted_calls"],
                      "source_use_approved": False}))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
