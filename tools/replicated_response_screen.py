#!/usr/bin/env python3
"""Run one frozen condition of the replicated external-biomedical response screen."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
from io import BytesIO
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time
import traceback
from typing import Any
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import biomedical_lane1, canonical, rational, replicated_response as response
from mmbu_phase1 import fields as f


STAGES = (
    "initialization", "portfolio", "snapshot", "load", "adaptation", "training", "evaluation", "save",
    "reload", "completed",
)
_RUNTIME_PACKAGES = ("numpy", "peft", "pillow", "torch", "transformers")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def require_new_output_root(path: Path) -> None:
    f.require(not path.exists() and not path.is_symlink(), "response.output_root", "must not already exist")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.write_bytes(canonical.dumps(value) + b"\n")


def load_portfolio(path: Path) -> dict:
    raw = path.read_bytes()
    value = canonical.loads(raw)
    f.literal(value.get("schema_id"), "portfolio.schema_id", "mmbu.biomedical.compiled_portfolio")
    f.literal(value.get("schema_version"), "portfolio.schema_version", 1)
    f.literal(value.get("mmbu_public_content_used"), "portfolio.mmbu_public_content_used", False)
    f.literal(value.get("rows_digest"), "portfolio.rows_digest", canonical.value_digest(value.get("rows")))
    f.literal(sorted(item["source_id"] for item in value.get("source_receipts", [])),
              "portfolio.source_ids", ["busbra", "pathmnist"])
    value["raw_sha256"] = _sha(raw)
    return value


def select_populations(portfolio: dict, manifest: dict, condition: dict) -> dict[str, list[dict]]:
    """Select one population with the frozen selection seed, never the training seed."""
    response.validate_manifest(manifest)
    response.candidate_by_id(manifest, condition["candidate_id"])
    selection = manifest["selection"]
    rows = portfolio["rows"]
    train = biomedical_lane1.select_rows(
        rows, split="train", per_source=selection["training_units_per_source"],
        seed=selection["selection_seed"], allow_confirmation=False,
    )
    development = biomedical_lane1.select_rows(
        rows, split="development", per_source=selection["development_units_per_source"],
        seed=selection["selection_seed"], allow_confirmation=False,
    )
    train = [response.official_context_row(row) for row in train]
    development = [response.official_context_row(row) for row in development]
    f.require(
        {row["independent_unit_id"] for row in train}.isdisjoint(
            {row["independent_unit_id"] for row in development}
        ),
        "response.population", "train and development independent units overlap",
    )
    return {"development": development, "train": train}


class ImageStore:
    def __init__(self, source_root: Path):
        import numpy

        self._busbra = zipfile.ZipFile(source_root / "BUSBRA.zip")
        self._pathmnist = numpy.load(source_root / "pathmnist_224.npz", allow_pickle=False)
        self._arrays: dict[str, Any] = {}

    def close(self) -> None:
        self._busbra.close()
        self._pathmnist.close()
        self._arrays.clear()

    def image(self, row: dict):
        from PIL import Image

        if row["source_id"] == "busbra":
            with self._busbra.open(row["image_member"]) as stream:
                image = Image.open(BytesIO(stream.read()))
                image.load()
                return image.convert("RGB")
        key = row["image_array_key"]
        if key not in self._arrays:
            self._arrays[key] = self._pathmnist[key]
        return Image.fromarray(self._arrays[key][row["image_index"]]).convert("RGB")


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
        processor, family, messages(prompt, target), generation=False,
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
    f.literal(sum(parameter.numel() for parameter in model.parameters()), "response.parameter_count",
              candidate["expected_parameter_count"])
    return processor, model


def exact_lora_targets(model: Any, suffixes: list[str]) -> list[str]:
    names = [name for name, _ in model.named_modules()]
    targets = sorted(
        name for name in names
        if "language_model" in name and any(name.endswith("." + suffix) for suffix in suffixes)
    )
    f.require(bool(targets), "response.lora.targets", "no language-model targets matched")
    for suffix in suffixes:
        f.require(any(name.endswith("." + suffix) for name in targets), "response.lora.targets",
                  f"no module matched {suffix}")
    return targets


def expected_optimizer_updates(manifest: dict, condition: dict) -> int:
    response.validate_manifest(manifest)
    if condition["profile"] == "base":
        return 0
    return (manifest["selection"]["training_units_per_source"] * 2 * manifest["training"]["epochs"])


def _device_batch(batch: Any, device: Any) -> dict:
    return {key: value.to(device) if hasattr(value, "to") else value for key, value in batch.items()}


def _encode_training(processor: Any, family: str, image: Any, prompt: str, target: str, device: Any):
    import torch

    batch, prompt_count = encode(processor, family, image, prompt, target)
    labels = batch["input_ids"].clone()
    labels[:, :prompt_count] = -100
    f.require(bool((labels != -100).any().item()), "response.labels", "contains no target token")
    batch["labels"] = labels.to(dtype=torch.long)
    return _device_batch(batch, device)


def _adapter_inventory(root: Path) -> list[dict]:
    rows = []
    for path in sorted((item for item in root.rglob("*") if item.is_file()),
                       key=lambda item: str(item.relative_to(root)).encode("utf-8")):
        raw = path.read_bytes()
        rows.append({"bytes": len(raw), "path": str(path.relative_to(root)), "sha256": _sha(raw)})
    f.require(bool(rows), "response.adapter", "save produced no files")
    return rows


def adapt(model: Any, manifest: dict, condition: dict) -> tuple[Any, list[str], list[str]]:
    if condition["profile"] == "base":
        return model, [], []
    from peft import LoraConfig, get_peft_model

    training = manifest["training"]
    targets = exact_lora_targets(model, training["lora_target_suffixes"])
    adapter = LoraConfig(
        r=training["lora_rank"], lora_alpha=training["lora_alpha"],
        lora_dropout=training["lora_dropout"], bias="none", target_modules=targets, task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, adapter)
    trainable = sorted(name for name, parameter in model.named_parameters() if parameter.requires_grad)
    f.require(bool(trainable), "response.trainable", "LoRA exposed no trainable parameters")
    return model, targets, trainable


def train(
    model: Any, processor: Any, store: ImageStore, rows: list[dict], manifest: dict, condition: dict, device: Any,
) -> list[dict]:
    import torch

    if condition["profile"] == "base":
        return []
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(
        parameters,
        lr=float(rational.from_wire(manifest["training"]["learning_rate"], "response.learning_rate")),
        weight_decay=manifest["training"]["weight_decay"],
    )
    mode = "task" if condition["profile"] == "task_only" else "dual"
    trace = []
    model.train()
    for epoch in range(manifest["training"]["epochs"]):
        for position, row in enumerate(rows):
            image = store.image(row)
            optimizer.zero_grad(set_to_none=True)
            endpoint_losses = []
            for endpoint, prompt, target, mass_wire in biomedical_lane1.training_views(row, mode):
                inputs = _encode_training(
                    processor, "qwen3_5", image, prompt, target, device,
                )
                output = model(**inputs, use_cache=False, return_dict=True)
                f.require(output.loss is not None and bool(torch.isfinite(output.loss).item()),
                          "response.training.loss", "must be finite")
                mass = float(rational.from_wire(mass_wire, "response.training.mass"))
                (output.loss * mass).backward()
                endpoint_losses.append({
                    "endpoint": endpoint,
                    "loss": float(output.loss.detach().float().item()),
                    "mass": mass_wire,
                })
            gradient_norm = torch.nn.utils.clip_grad_norm_(
                parameters, manifest["training"]["gradient_clip_norm"],
            )
            f.require(bool(torch.isfinite(gradient_norm).item()), "response.training.gradient_norm", "must be finite")
            optimizer.step()
            trace.append({
                "endpoint_losses": endpoint_losses,
                "epoch": epoch,
                "position": position,
                "row_id": row["row_id"],
            })
    f.literal(len(trace), "response.optimizer_updates", expected_optimizer_updates(manifest, condition))
    return trace


def _generate(model: Any, processor: Any, family: str, image: Any, prompt: str, limit: int, device: Any) -> str:
    import torch

    batch, _ = encode(processor, family, image, prompt, None)
    inputs = _device_batch(batch, device)
    input_length = int(inputs["input_ids"].shape[1])
    with torch.no_grad():
        output = model.generate(
            **inputs, do_sample=False, num_beams=1, num_return_sequences=1, use_cache=True,
            max_new_tokens=limit, pad_token_id=processor.tokenizer.pad_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
        )
    return processor.tokenizer.decode(output[0, input_length:], skip_special_tokens=True).strip()


def evaluate(
    model: Any, processor: Any, store: ImageStore, rows: list[dict], manifest: dict, candidate: dict, device: Any,
) -> tuple[list[dict], dict]:
    model.eval()
    predictions = []
    for row in rows:
        image = store.image(row)
        task = _generate(
            model, processor, candidate["loader_family"], image, row["task_prompt"],
            manifest["training"]["max_task_new_tokens"], device,
        )
        context = _generate(
            model, processor, candidate["loader_family"], image, row["context_prompt"],
            manifest["training"]["max_context_new_tokens"], device,
        )
        predictions.append({"context": context, "row_id": row["row_id"], "task": task})
    return predictions, biomedical_lane1.score_predictions(rows, predictions)


def reload_command(
    python: str, script: str, manifest: str, condition_index: int, portfolio: str, snapshots: str,
    sources: str, adapter: str | None, output: str,
) -> list[str]:
    command = [
        python, script, "--manifest", manifest, "--condition-index", str(condition_index),
        "--portfolio", portfolio, "--snapshot-root", snapshots, "--source-root", sources,
    ]
    if adapter is not None:
        command.extend(["--adapter", adapter])
    command.extend(["--output", output])
    return command


def failure_receipt(
    candidate: dict, condition: dict, stage: str, error: str, started_at: str, ended_at: str,
    manifest_sha256: str, portfolio_sha256: str | None, *, optimizer_updates: int = 0,
) -> dict:
    f.one_of(stage, "response.failure.stage", STAGES[:-1])
    return {
        "adapter_inventory": [],
        "biomedical_content_used": True,
        "candidate": candidate,
        "condition": condition,
        "development_metrics": None,
        "development_predictions": None,
        "ended_at": ended_at,
        "error": error,
        "evidence_class": "external_biomedical_exploratory_response",
        "manifest_sha256": manifest_sha256,
        "mmbu_public_content_used": False,
        "optimizer_updates": optimizer_updates,
        "portfolio_sha256": portfolio_sha256,
        "promotion_eligible": False,
        "reload_prediction_match": None,
        "schema_id": "mmbu.biomedical.replicated_response_result",
        "schema_version": 1,
        "source_admission_complete": False,
        "started_at": started_at,
        "status": "failed",
        "terminal_stage": stage,
    }


def _runtime_receipt(torch: Any) -> dict:
    return {
        "gpu_name": torch.cuda.get_device_name(0),
        "hostname": platform.node(),
        "packages": {name: importlib.metadata.version(name) for name in _RUNTIME_PACKAGES},
        "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
        "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved(0)),
        "python": platform.python_version(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
    }


def run(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    manifest_raw = manifest_path.read_bytes()
    manifest = response.validate_manifest(canonical.loads(manifest_raw))
    condition = response.condition_by_index(manifest, args.condition_index)
    candidate = response.candidate_by_id(manifest, condition["candidate_id"])
    output_root = Path(args.output_root).resolve()
    require_new_output_root(output_root)
    output_root.mkdir(parents=True, mode=0o700)
    started_at = utc_now()
    started = time.monotonic()
    stage = "initialization"
    portfolio_sha = None
    updates = 0
    try:
        f.literal({key: os.environ.get(key) for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")},
                  "response.offline", {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        import torch

        f.require(torch.cuda.is_available(), "response.cuda", "CUDA unavailable")
        f.literal(torch.cuda.device_count(), "response.cuda.device_count", 1)
        torch.cuda.set_device(0)
        device = torch.device("cuda:0")
        seed = condition["training_seed"] if condition["training_seed"] is not None else manifest["training"]["seeds"][0]
        random.seed(seed)
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.cuda.reset_peak_memory_stats()

        stage = "portfolio"
        portfolio = load_portfolio(Path(args.portfolio).resolve())
        portfolio_sha = portfolio["raw_sha256"]
        populations = select_populations(portfolio, manifest, condition)
        train_ids = [row["row_id"] for row in populations["train"]]
        development_ids = [row["row_id"] for row in populations["development"]]

        stage = "snapshot"
        snapshot = Path(args.snapshot_root).resolve() / candidate["snapshot_name"]
        f.require(snapshot.is_dir() and not snapshot.is_symlink(), "response.snapshot", "must be a real directory")

        stage = "load"
        processor, model = load_native(snapshot, candidate)
        model.to(device)
        stage = "adaptation"
        model, targets, trainable_names = adapt(model, manifest, condition)

        store = ImageStore(Path(args.source_root).resolve())
        try:
            stage = "training"
            trace = train(model, processor, store, populations["train"], manifest, condition, device)
            updates = len(trace)
            stage = "evaluation"
            predictions, metrics = evaluate(
                model, processor, store, populations["development"], manifest, candidate, device,
            )
            stage = "save"
            adapter_root = None
            inventory = []
            if condition["profile"] != "base":
                adapter_root = output_root / "adapter"
                model.save_pretrained(adapter_root, safe_serialization=True)
                inventory = _adapter_inventory(adapter_root)
        finally:
            store.close()

        del model
        torch.cuda.empty_cache()
        stage = "reload"
        reload_path = output_root / "reload-result.json"
        command = reload_command(
            sys.executable, str(ROOT / "tools/replicated_response_reload.py"), str(manifest_path),
            args.condition_index, str(Path(args.portfolio).resolve()), str(Path(args.snapshot_root).resolve()),
            str(Path(args.source_root).resolve()), None if adapter_root is None else str(adapter_root), str(reload_path),
        )
        environment = dict(os.environ)
        environment["HF_HUB_OFFLINE"] = "1"
        environment["TRANSFORMERS_OFFLINE"] = "1"
        completed = subprocess.run(command, check=False, capture_output=True, text=True, env=environment)
        f.literal(completed.returncode, "response.reload.returncode", 0)
        reload_result = canonical.loads(reload_path.read_bytes())
        f.literal(reload_result["predictions"], "response.reload.predictions", predictions)
        f.literal(reload_result["metrics"], "response.reload.metrics", metrics)

        stage = "completed"
        result = {
            "adapter_inventory": inventory,
            "biomedical_content_used": True,
            "candidate": candidate,
            "condition": condition,
            "development_ids_digest": canonical.value_digest(development_ids),
            "development_metrics": metrics,
            "development_predictions": predictions,
            "elapsed_seconds": time.monotonic() - started,
            "ended_at": utc_now(),
            "error": None,
            "evidence_class": "external_biomedical_exploratory_response",
            "lora_targets": targets,
            "manifest_sha256": _sha(manifest_raw),
            "mmbu_public_content_used": False,
            "optimizer_updates": updates,
            "parameter_count": candidate["expected_parameter_count"],
            "portfolio_sha256": portfolio_sha,
            "promotion_eligible": False,
            "reload_prediction_match": True,
            "runtime": _runtime_receipt(torch),
            "schema_id": "mmbu.biomedical.replicated_response_result",
            "schema_version": 1,
            "snapshot": str(snapshot),
            "source_admission_complete": False,
            "started_at": started_at,
            "status": "passed",
            "terminal_stage": stage,
            "train_trace": trace,
            "trainable_parameter_names": trainable_names,
            "training_ids_digest": canonical.value_digest(train_ids),
        }
        _write(output_root / "result.json", result)
        return 0
    except Exception as exc:
        receipt = failure_receipt(
            candidate, condition, stage, f"{type(exc).__name__}: {exc}", started_at, utc_now(),
            _sha(manifest_raw), portfolio_sha, optimizer_updates=updates,
        )
        receipt["traceback"] = traceback.format_exc()
        _write(output_root / "result.json", receipt)
        return 2


def arguments(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--condition-index", required=True, type=int)
    parser.add_argument("--portfolio", required=True)
    parser.add_argument("--snapshot-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-root", required=True)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(run(arguments()))
