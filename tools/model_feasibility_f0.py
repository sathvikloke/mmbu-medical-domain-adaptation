#!/usr/bin/env python3
"""One-attempt, generated-only native F0 model feasibility runner."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time
import traceback
from typing import Any

from mmbu_phase1 import canonical, model_feasibility
from mmbu_phase1 import fields as f


REPO = Path(__file__).resolve().parents[1]
STAGES = ("initialization", "snapshot", "load", "forward", "backward", "optimizer", "save", "reload", "completed")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def require_new_output_root(path: Path) -> None:
    f.require(not path.exists() and not path.is_symlink(), "f0.output_root", "must not already exist")


def validate_offline_environment(environment: dict[str, str]) -> dict[str, str]:
    result = {key: environment.get(key) for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")}
    f.literal(result, "f0.offline_environment", {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    return result


def reload_command(
    python: str, script: str, manifest: str, candidate_index: int, snapshot: str, adapter: str, output: str,
) -> list[str]:
    return [
        python, script, "--manifest", manifest, "--candidate-index", str(candidate_index), "--snapshot", snapshot,
        "--adapter", adapter, "--output", output,
    ]


def failure_receipt(
    candidate: dict, stage: str, error: str, started_at: str, ended_at: str, snapshot: str,
    manifest_sha256: str, *, optimizer_updates: int = 0, adapter_inventory: list[dict] | None = None,
    snapshot_tree_sha256: str | None = None, resources: dict | None = None,
) -> dict:
    f.one_of(stage, "f0.failure.stage", STAGES[:-1])
    return {
        "adapter_inventory": [] if adapter_inventory is None else adapter_inventory,
        "biomedical_content_used": False,
        "candidate": candidate,
        "ended_at": ended_at,
        "error": error,
        "evidence_class": "generated_only_model_feasibility",
        "manifest_sha256": manifest_sha256,
        "mmbu_public_content_used": False,
        "optimizer_updates": optimizer_updates,
        "reload_prediction_match": None,
        "resources": resources,
        "schema_id": "mmbu.phase1.model_feasibility_result",
        "schema_version": 1,
        "snapshot": snapshot,
        "snapshot_tree_sha256": snapshot_tree_sha256,
        "started_at": started_at,
        "status": "failed",
        "terminal_stage": stage,
    }


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.write_bytes(canonical.dumps(value) + b"\n")


def snapshot_inventory(root: Path) -> tuple[list[dict], str]:
    f.require(root.is_dir() and not root.is_symlink(), "f0.snapshot", "must be a real directory")
    rows = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: str(item.relative_to(root)).encode()):
        raw = path.read_bytes()
        rows.append({"bytes": len(raw), "path": str(path.relative_to(root)), "sha256": _sha(raw)})
    f.require(bool(rows), "f0.snapshot", "contains no files")
    return rows, _sha(canonical.dumps(rows))


def generated_image(spec: dict):
    from PIL import Image
    rng = random.Random(spec["seed"])
    raw = bytes(rng.randrange(256) for _ in range(spec["width"] * spec["height"] * spec["channels"]))
    return Image.frombytes("RGB", (spec["width"], spec["height"]), raw), _sha(raw)


def messages(prompt: str, answer: str | None = None) -> list[dict]:
    value = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": prompt}]}]
    if answer is not None:
        value.append({"role": "assistant", "content": [{"type": "text", "text": answer}]})
    return value


def render_chat(processor: Any, family: str, conversation: list[dict], *, generation: bool) -> str:
    options = {"tokenize": False, "add_generation_prompt": generation}
    if family == "qwen3_5":
        options["enable_thinking"] = False
    return processor.apply_chat_template(conversation, **options)


def encode(processor: Any, family: str, image: Any, prompt: str, target: str | None = None):
    prompt_text = render_chat(processor, family, messages(prompt), generation=True)
    full_text = prompt_text if target is None else render_chat(
        processor, family, messages(prompt, target), generation=False
    )
    prompt_batch = processor(text=[prompt_text], images=[image], padding=False, return_tensors="pt")
    batch = processor(text=[full_text], images=[image], padding=False, return_tensors="pt")
    return batch, int(prompt_batch["attention_mask"].sum().item())


def load_native(snapshot: Path, candidate: dict):
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    processor = AutoProcessor.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
    if hasattr(processor, "tokenizer"):
        processor.tokenizer.padding_side = "left"
    model = AutoModelForImageTextToText.from_pretrained(
        snapshot, local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
        attn_implementation="sdpa", device_map=None,
    )
    return processor, model


def exact_lora_targets(model: Any, suffixes: list[str]) -> list[str]:
    names = [name for name, _ in model.named_modules()]
    targets = sorted(
        name for name in names
        if "language_model" in name and any(name.endswith("." + suffix) for suffix in suffixes)
    )
    f.require(bool(targets), "f0.lora.targets", "no language-model q/v projections matched")
    for suffix in suffixes:
        f.require(any(name.endswith("." + suffix) for name in targets), "f0.lora.targets",
                  f"no module matched {suffix}")
    return targets


def tensor_digest(named_parameters: list[tuple[str, Any]]) -> str:
    import torch

    digest = hashlib.sha256()
    for name, parameter in named_parameters:
        digest.update(name.encode("utf-8") + b"\0")
        raw = parameter.detach().contiguous().cpu().view(torch.uint8).numpy().tobytes()
        digest.update(raw)
    return digest.hexdigest()


def adapter_inventory(root: Path) -> list[dict]:
    rows = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()), key=lambda item: str(item.relative_to(root)).encode()):
        raw = path.read_bytes()
        rows.append({"bytes": len(raw), "path": str(path.relative_to(root)), "sha256": _sha(raw)})
    f.require(bool(rows), "f0.adapter", "save produced no files")
    return rows


def _device_batch(batch: Any, device: Any) -> dict:
    return {key: value.to(device) if hasattr(value, "to") else value for key, value in batch.items()}


def deterministic_prediction(model: Any, inputs: dict, prompt_length: int) -> list[int]:
    import torch
    model.eval()
    with torch.no_grad():
        generated = model.generate(
            **inputs, max_new_tokens=2, do_sample=False, num_beams=1, num_return_sequences=1, use_cache=True,
        )
    return generated[0, prompt_length:].detach().cpu().tolist()


def run(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    manifest_raw = manifest_path.read_bytes()
    manifest = model_feasibility.validate_manifest(canonical.loads(manifest_raw))
    candidate = model_feasibility.candidate_by_index(manifest, args.candidate_index)
    snapshot = (Path(args.snapshot_root).resolve() / candidate["candidate_id"])
    output_root = Path(args.output_root).resolve()
    require_new_output_root(output_root)
    output_root.mkdir(parents=True, mode=0o700)
    started_at = utc_now()
    started = time.monotonic()
    stage = "initialization"
    manifest_sha = _sha(manifest_raw)
    snapshot_sha = None
    inventory = []
    optimizer_updates = 0
    try:
        validate_offline_environment(os.environ)
        import torch
        from peft import LoraConfig, get_peft_model

        f.require(torch.cuda.is_available(), "f0.cuda", "CUDA unavailable")
        f.literal(torch.cuda.device_count(), "f0.cuda.device_count", 1)
        torch.cuda.set_device(0)
        device = torch.device("cuda:0")
        torch.manual_seed(manifest["runtime"]["seed"])
        torch.cuda.manual_seed_all(manifest["runtime"]["seed"])
        torch.use_deterministic_algorithms(manifest["runtime"]["deterministic_algorithms"])
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.cuda.reset_peak_memory_stats()

        stage = "snapshot"
        snapshot_rows, snapshot_sha = snapshot_inventory(snapshot)

        stage = "load"
        processor, base = load_native(snapshot, candidate)
        parameter_count = sum(parameter.numel() for parameter in base.parameters())
        f.literal(parameter_count, "f0.model.parameter_count", candidate["expected_parameter_count"])
        base.to(device)
        image, fixture_sha = generated_image(manifest["fixture"])

        stage = "forward"
        batch, prompt_count = encode(
            processor, candidate["loader_family"], image, manifest["fixture"]["prompt"], manifest["fixture"]["target"]
        )
        labels = batch["input_ids"].clone()
        labels[:, :prompt_count] = -100
        f.require(bool((labels != -100).any().item()), "f0.labels", "contains no target token")
        batch["labels"] = labels
        inputs = _device_batch(batch, device)
        targets = exact_lora_targets(base, manifest["lora"]["target_suffixes"])
        lora = LoraConfig(
            r=manifest["lora"]["rank"], lora_alpha=manifest["lora"]["alpha"],
            lora_dropout=manifest["lora"]["dropout"], bias="none", target_modules=targets,
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(base, lora)
        trainable = sorted((name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad)
        f.require(bool(trainable), "f0.trainable", "LoRA exposed no trainable tensors")
        before = tensor_digest(trainable)
        optimizer = torch.optim.AdamW(
            [parameter for _, parameter in trainable], lr=manifest["lora"]["learning_rate"],
            weight_decay=manifest["lora"]["weight_decay"],
        )
        model.train()
        optimizer.zero_grad(set_to_none=True)
        output = model(**inputs, use_cache=False, return_dict=True)
        f.require(output.loss is not None and bool(torch.isfinite(output.loss).item()), "f0.loss", "must be finite")

        stage = "backward"
        output.loss.backward()
        for name, parameter in trainable:
            f.require(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all().item()),
                      f"f0.gradient.{name}", "must exist and be finite")

        stage = "optimizer"
        optimizer.step()
        optimizer_updates = 1
        after = tensor_digest(trainable)
        f.require(before != after, "f0.optimizer", "no trainable parameter changed")

        stage = "save"
        adapter = output_root / "adapter"
        model.save_pretrained(adapter, safe_serialization=True)
        inventory = adapter_inventory(adapter)
        generation_batch, _ = encode(
            processor, candidate["loader_family"], image, manifest["fixture"]["prompt"], None
        )
        generation_inputs = _device_batch(generation_batch, device)
        prediction = deterministic_prediction(model, generation_inputs, generation_batch["input_ids"].shape[1])
        del output, inputs, generation_inputs, optimizer, model, base
        torch.cuda.empty_cache()

        stage = "reload"
        reload_path = output_root / "reload-result.json"
        environment = dict(os.environ)
        environment["HF_HUB_OFFLINE"] = "1"
        environment["TRANSFORMERS_OFFLINE"] = "1"
        command = reload_command(
            sys.executable, str(REPO / "tools/model_feasibility_f0_reload.py"), str(manifest_path),
            args.candidate_index, str(snapshot), str(adapter), str(reload_path),
        )
        completed = subprocess.run(command, check=False, capture_output=True, text=True, env=environment)
        f.literal(completed.returncode, "f0.reload.returncode", 0)
        reload_result = canonical.loads(reload_path.read_bytes())
        f.literal(reload_result["prediction_ids"], "f0.reload.prediction_ids", prediction)

        stage = "completed"
        result = {
            "adapter_inventory": inventory,
            "biomedical_content_used": False,
            "candidate": candidate,
            "ended_at": utc_now(),
            "error": None,
            "evidence_class": "generated_only_model_feasibility",
            "fixture_sha256": fixture_sha,
            "lora_targets": targets,
            "manifest_sha256": manifest_sha,
            "mmbu_public_content_used": False,
            "optimizer_updates": 1,
            "parameter_count": parameter_count,
            "prediction_ids": prediction,
            "reload_prediction_match": True,
            "resources": {
                "elapsed_seconds": time.monotonic() - started,
                "gpu_name": torch.cuda.get_device_name(0),
                "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated(0),
                "peak_cuda_reserved_bytes": torch.cuda.max_memory_reserved(0),
                "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            },
            "runtime": {
                "python": platform.python_version(),
                "torch": importlib.metadata.version("torch"),
                "transformers": importlib.metadata.version("transformers"),
                "peft": importlib.metadata.version("peft"),
            },
            "schema_id": "mmbu.phase1.model_feasibility_result",
            "schema_version": 1,
            "snapshot": str(snapshot),
            "snapshot_inventory": snapshot_rows,
            "snapshot_tree_sha256": snapshot_sha,
            "started_at": started_at,
            "status": "passed",
            "terminal_stage": stage,
        }
        _write(output_root / "result.json", result)
        return 0
    except Exception as exc:
        receipt = failure_receipt(
            candidate, stage, f"{type(exc).__name__}: {exc}", started_at, utc_now(), str(snapshot), manifest_sha,
            optimizer_updates=optimizer_updates, adapter_inventory=inventory,
            snapshot_tree_sha256=snapshot_sha,
            resources={"elapsed_seconds": time.monotonic() - started},
        )
        receipt["traceback"] = traceback.format_exc()
        _write(output_root / "result.json", receipt)
        return 2


def arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--candidate-index", required=True, type=int)
    parser.add_argument("--snapshot-root", required=True)
    parser.add_argument("--output-root", required=True)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(arguments()))
