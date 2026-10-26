#!/usr/bin/env python3
"""Run one arm of the external-only biomedical Lane 1 shakedown on one GPU."""

from __future__ import annotations

import argparse
from fractions import Fraction
import importlib.metadata
from io import BytesIO
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import time
from typing import Any
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from mmbu_phase1 import biomedical_lane1, canonical, rational
from mmbu_phase1 import fields as f
import b1_native_preflight as b1_native
import b2_native_preflight as b2_native


ARMS = (
    {"architecture": "base", "candidate_id": "recipe_arch::B0::base", "objective": "base"},
    {"architecture": "language_lora", "candidate_id": "recipe_arch::B1-L::profile::task_only", "objective": "task"},
    {"architecture": "language_lora", "candidate_id": "recipe_arch::B1-L::profile::dual", "objective": "dual"},
    {"architecture": "language_lora_projector", "candidate_id": "recipe_arch::B2-P::profile::task_only", "objective": "task"},
    {"architecture": "language_lora_projector", "candidate_id": "recipe_arch::B2-P::profile::dual", "objective": "dual"},
)
_RUNTIME_PACKAGES = ("numpy", "peft", "pillow", "torch", "torchvision", "transformers")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--config", type=Path, default=ROOT / "config/phase1/biomedical-lane1-shakedown.json")
    result.add_argument("--arm-index", required=True, type=int, choices=range(len(ARMS)))
    result.add_argument("--output-root", required=True, type=Path)
    return result


def validate_config(value: Any) -> dict:
    value = f.closed(value, "config", ("allowed_arms", "authorization", "data", "execution", "model",
                                         "schema_id", "schema_version"))
    f.literal(value["schema_id"], "config.schema_id", "mmbu.biomedical.lane1_native_config")
    f.literal(value["schema_version"], "config.schema_version", 1)
    f.literal(value["allowed_arms"], "config.allowed_arms", [arm["candidate_id"] for arm in ARMS])
    authorization = f.closed(value["authorization"], "config.authorization",
                             ("authorized_actions", "authorized_by", "prohibited_actions"))
    f.literal(authorization["prohibited_actions"], "config.authorization.prohibited_actions",
              ["final_submission", "mmbu_public_set_evaluation", "upload"])
    f.require("gpu_hpc_training" in authorization["authorized_actions"],
              "config.authorization.authorized_actions", "GPU training must be explicitly authorized")
    f.text(authorization["authorized_by"], "config.authorization.authorized_by")
    data = f.closed(value["data"], "config.data", ("busbra_archive", "development_units_per_source",
                                                     "pathmnist_archive", "portfolio_manifest",
                                                     "training_units_per_source"))
    for key in ("busbra_archive", "pathmnist_archive", "portfolio_manifest"):
        f.text(data[key], f"config.data.{key}")
    for key in ("training_units_per_source", "development_units_per_source"):
        f.integer(data[key], f"config.data.{key}", minimum=1)
    execution = f.closed(value["execution"], "config.execution", ("epochs", "gradient_clip_norm",
                                                                    "max_context_new_tokens",
                                                                    "max_task_new_tokens", "mode",
                                                                    "network_policy", "seed", "world_size"))
    f.literal(execution["mode"], "config.execution.mode", "shakedown")
    f.literal(execution["network_policy"], "config.execution.network_policy", "denied")
    f.literal(execution["world_size"], "config.execution.world_size", 1)
    for key in ("epochs", "gradient_clip_norm", "max_context_new_tokens", "max_task_new_tokens"):
        f.integer(execution[key], f"config.execution.{key}", minimum=1)
    f.integer(execution["seed"], "config.execution.seed", minimum=0)
    model = f.closed(value["model"], "config.model", ("attention_implementation", "dtype", "learning_rate",
                                                       "lora_alpha", "lora_dropout", "lora_rank", "model_id",
                                                       "model_root", "revision", "weight_decay"))
    f.literal(model["model_id"], "config.model.model_id", "Qwen/Qwen2.5-VL-7B-Instruct")
    f.literal(model["revision"], "config.model.revision", "cc594898137f460bfe9f0759e9844b3ce807cfb5")
    f.literal(model["attention_implementation"], "config.model.attention_implementation", "sdpa")
    f.literal(model["dtype"], "config.model.dtype", "bfloat16")
    learning_rate = rational.from_wire(model["learning_rate"], "config.model.learning_rate")
    f.require(0 < learning_rate < Fraction(1), "config.model.learning_rate", "must be in (0,1)")
    for key in ("lora_alpha", "lora_rank"):
        f.integer(model[key], f"config.model.{key}", minimum=1)
    f.literal(model["lora_dropout"], "config.model.lora_dropout", 0)
    f.literal(model["weight_decay"], "config.model.weight_decay", 0)
    f.text(model["model_root"], "config.model.model_root")
    return value


def load_portfolio(path: Path) -> dict:
    raw = path.read_bytes()
    value = canonical.loads(raw)
    f.literal(value.get("schema_id"), "portfolio.schema_id", "mmbu.biomedical.compiled_portfolio")
    f.literal(value.get("schema_version"), "portfolio.schema_version", 1)
    f.literal(value.get("mmbu_public_content_used"), "portfolio.mmbu_public_content_used", False)
    f.literal(value.get("rows_digest"), "portfolio.rows_digest", canonical.value_digest(value.get("rows")))
    receipts = f.array(value.get("source_receipts"), "portfolio.source_receipts", nonempty=True)
    f.literal(sorted(item["source_id"] for item in receipts), "portfolio.source_ids", ["busbra", "pathmnist"])
    for index, receipt in enumerate(receipts):
        f.literal(receipt.get("mmbu_content_used"), f"portfolio.source_receipts[{index}].mmbu_content_used", False)
    value["raw_sha256"] = canonical.raw_digest(raw)
    return value


class ImageStore:
    def __init__(self, busbra_path: Path, pathmnist_path: Path):
        import numpy

        self._numpy = numpy
        self._busbra = zipfile.ZipFile(busbra_path)
        self._pathmnist = numpy.load(pathmnist_path, allow_pickle=False)
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


def _load_base(config: dict, device: Any):
    import torch
    from transformers import Qwen2_5_VLForConditionalGeneration

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        Path(config["model"]["model_root"]), local_files_only=True, trust_remote_code=False,
        torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map=None,
    ).to(device)
    f.literal(type(model).__name__, "model.class", "Qwen2_5_VLForConditionalGeneration")
    f.literal(model.config._attn_implementation, "model.attention", "sdpa")
    return model


def _adapt(model: Any, arm: dict, config: dict) -> tuple[Any, list[str]]:
    if arm["architecture"] == "base":
        return model, []
    from peft import LoraConfig, get_peft_model

    targets = b1_native.exact_lora_targets(name for name, _ in model.named_modules())
    base_projector = sorted(
        name for name, _ in model.named_parameters() if name.startswith("model.visual.merger.")
    )
    modules_to_save = ["visual.merger"] if arm["architecture"] == "language_lora_projector" else None
    adapter = LoraConfig(
        r=config["model"]["lora_rank"], lora_alpha=config["model"]["lora_alpha"],
        lora_dropout=config["model"]["lora_dropout"], bias="none", target_modules=targets,
        modules_to_save=modules_to_save, task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, adapter)
    names = sorted(name for name, parameter in model.named_parameters() if parameter.requires_grad)
    language = sorted(b2_native._lora_trainable_names(targets))
    if arm["architecture"] == "language_lora":
        f.literal(names, "trainable_scope", language)
    else:
        b2_native.validate_trainable_scope(names, targets, base_projector)
    return model, names


def _encode_training(processor: Any, image: Any, prompt: str, target: str, device: Any):
    import torch

    batch, prompt_counts = b1_native._encode(processor, [image], [prompt], [" " + target])
    labels = b1_native.build_target_only_labels(
        batch["input_ids"].tolist(), batch["attention_mask"].tolist(), prompt_counts,
    )
    batch["labels"] = torch.tensor(labels, dtype=torch.long)
    return b1_native._device_batch(batch, device)


def train(model: Any, processor: Any, store: ImageStore, rows: list[dict], arm: dict, config: dict, device: Any) -> list[dict]:
    import torch

    if arm["objective"] == "base":
        return []
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    f.require(bool(parameters), "optimizer.parameters", "adapted arm must have trainable parameters")
    learning_rate = float(rational.from_wire(config["model"]["learning_rate"], "config.model.learning_rate"))
    optimizer = torch.optim.AdamW(parameters, lr=learning_rate, weight_decay=0)
    trace = []
    model.train()
    for epoch in range(config["execution"]["epochs"]):
        for position, row in enumerate(rows):
            image = store.image(row)
            optimizer.zero_grad(set_to_none=True)
            endpoint_losses = []
            for endpoint, prompt, target, mass_wire in biomedical_lane1.training_views(row, arm["objective"]):
                inputs = _encode_training(processor, image, prompt, target, device)
                output = model(**inputs, use_cache=False, return_dict=True)
                f.require(bool(torch.isfinite(output.loss).item()), "training.loss", "nonfinite loss")
                mass = float(rational.from_wire(mass_wire, "training.mass"))
                (output.loss * mass).backward()
                endpoint_losses.append({"endpoint": endpoint, "loss": float(output.loss.detach().float().item()),
                                        "mass": mass_wire})
            gradient_norm = torch.nn.utils.clip_grad_norm_(parameters, config["execution"]["gradient_clip_norm"])
            f.require(bool(torch.isfinite(gradient_norm).item()), "training.gradient_norm", "nonfinite gradient norm")
            optimizer.step()
            trace.append({"endpoint_losses": endpoint_losses, "epoch": epoch, "position": position,
                          "row_id": row["row_id"]})
    return trace


def _generate(model: Any, processor: Any, image: Any, prompt: str, max_new_tokens: int, device: Any) -> str:
    import torch

    batch, _ = b1_native._encode(processor, [image], [prompt])
    inputs = b1_native._device_batch(batch, device)
    input_length = int(inputs["input_ids"].shape[1])
    with torch.no_grad():
        output = model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens,
                                pad_token_id=processor.tokenizer.pad_token_id,
                                eos_token_id=processor.tokenizer.eos_token_id)
    return processor.tokenizer.decode(output[0, input_length:], skip_special_tokens=True).strip()


def evaluate(model: Any, processor: Any, store: ImageStore, rows: list[dict], config: dict, device: Any) -> tuple[list[dict], dict]:
    model.eval()
    predictions = []
    for row in rows:
        image = store.image(row)
        task = _generate(model, processor, image, row["task_prompt"],
                         config["execution"]["max_task_new_tokens"], device)
        context = None
        if row.get("context_target") is not None:
            context = _generate(model, processor, image, row["context_prompt"],
                                config["execution"]["max_context_new_tokens"], device)
        predictions.append({"context": context, "row_id": row["row_id"], "task": task})
    return predictions, biomedical_lane1.score_predictions(rows, predictions)


def _runtime_receipt(torch: Any) -> dict:
    gpu = b1_native.parse_nvidia_smi_receipt(subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version,name,memory.total", "--format=csv,noheader,nounits", "-i", "0"],
        check=True, capture_output=True, text=True,
    ).stdout.strip())
    return {
        "gpu": gpu,
        "hostname": platform.node(),
        "packages": {name: importlib.metadata.version(name) for name in _RUNTIME_PACKAGES},
        "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "python": platform.python_version(),
        "slurm_job_id": f.text(os.environ.get("SLURM_JOB_ID"), "runtime.SLURM_JOB_ID"),
    }


def run(config: dict, arm_index: int, output_root: Path) -> dict:
    import torch

    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        f.literal(os.environ.get(key), f"environment.{key}", "1")
    f.require(torch.cuda.is_available(), "runtime.cuda", "CUDA unavailable")
    f.literal(torch.cuda.device_count(), "runtime.cuda.device_count", 1)
    torch.cuda.set_device(0)
    device = torch.device("cuda:0")
    seed = config["execution"]["seed"]
    random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats()

    arm = ARMS[arm_index]
    lane_root = Path(f.text(os.environ.get("MMBU_LANE1_ROOT"), "environment.MMBU_LANE1_ROOT"))
    f.require(lane_root.is_absolute(), "environment.MMBU_LANE1_ROOT", "must be an absolute path")
    portfolio = load_portfolio(lane_root / config["data"]["portfolio_manifest"])
    train_rows = biomedical_lane1.select_rows(
        portfolio["rows"], split="train", per_source=config["data"]["training_units_per_source"], seed=seed,
    )
    development_rows = biomedical_lane1.select_rows(
        portfolio["rows"], split="development", per_source=config["data"]["development_units_per_source"], seed=seed,
    )
    selected_ids = [row["row_id"] for row in train_rows]
    f.require(not ({row["independent_unit_id"] for row in train_rows} &
                   {row["independent_unit_id"] for row in development_rows}),
              "selection", "independent-unit overlap between train and development")

    processor = b1_native.load_pil_processor(Path(config["model"]["model_root"]))
    processor.tokenizer.padding_side = "left"
    store = ImageStore(lane_root / config["data"]["busbra_archive"],
                       lane_root / config["data"]["pathmnist_archive"])
    started = time.monotonic()
    try:
        model = _load_base(config, device)
        model, trainable_names = _adapt(model, arm, config)
        trace = train(model, processor, store, train_rows, arm, config, device)
        arm_root = output_root / f"arm-{arm_index}"
        f.require(not arm_root.exists(), "output", "arm output already exists")
        arm_root.mkdir(parents=True)
        adapter_root = None
        if arm["architecture"] != "base":
            adapter_root = arm_root / "adapter"
            model.save_pretrained(adapter_root, safe_serialization=True)
        predictions, metrics = evaluate(model, processor, store, development_rows, config, device)

        del model
        torch.cuda.empty_cache()
        reloaded = _load_base(config, device)
        if adapter_root is not None:
            from peft import PeftModel
            reloaded = PeftModel.from_pretrained(reloaded, adapter_root, local_files_only=True, is_trainable=False).to(device)
        reload_predictions, reload_metrics = evaluate(reloaded, processor, store, development_rows, config, device)
        f.literal(reload_predictions, "reload.predictions", predictions)
        f.literal(reload_metrics, "reload.metrics", metrics)
        elapsed = time.monotonic() - started
        result = {
            "arm": arm,
            "config_digest": canonical.value_digest(config),
            "development_metrics": metrics,
            "development_predictions": predictions,
            "elapsed_seconds": elapsed,
            "evidence_class": "biomedical_shakedown",
            "limitations": [
                "Bounded wiring shakedown only; not eligible for scientific selection or a score increase.",
                "No MMBU public data, upload, or submission was used.",
            ],
            "mmbu_public_content_used": False,
            "optimizer_updates": len(trace),
            "portfolio_raw_sha256": portfolio["raw_sha256"],
            "reload_prediction_match": True,
            "runtime": _runtime_receipt(torch),
            "schema_id": "mmbu.biomedical.lane1_arm_result",
            "schema_version": 1,
            "scientific_selection_output_observed": False,
            "seed": seed,
            "status": "passed",
            "train_trace": trace,
            "trainable_parameter_names": trainable_names,
            "training_order_digest": canonical.value_digest(selected_ids),
        }
        (arm_root / "result.json").write_bytes(canonical.dumps(result) + b"\n")
        return result
    finally:
        store.close()


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config = validate_config(canonical.loads(args.config.read_bytes()))
        result = run(config, args.arm_index, args.output_root)
    except Exception as exc:
        print(f"biomedical Lane 1 arm failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(canonical.dumps({"candidate_id": result["arm"]["candidate_id"],
                           "metrics": result["development_metrics"], "status": result["status"]}).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
