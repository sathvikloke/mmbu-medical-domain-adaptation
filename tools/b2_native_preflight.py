#!/usr/bin/env python3
"""One-job, one-step, synthetic-only B2-P projector preflight."""

from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any

from mmbu_phase1 import b1_preflight
from mmbu_phase1 import b2_preflight
from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f


REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "config/phase1/b2-mocs-preflight.json"
B1_CONFIG_PATH = REPO / "config/phase1/b1-mocs-preflight.json"
PIN_PATH = REPO / "docs/phase1/b1-pin.json"
SEED = 20261023
LOGIT_ATOL = 0.5
_RUNTIME_PACKAGES = {
    "accelerate": "accelerate", "numpy": "numpy", "peft": "peft", "pillow": "pillow",
    "safetensors": "safetensors", "torch": "torch", "torchvision": "torchvision",
    "transformers": "transformers",
}


def _lora_trainable_names(targets: list[str]) -> list[str]:
    return [
        f"base_model.model.{target}.lora_{side}.default.weight"
        for target in targets for side in ("A", "B")
    ]


def _projector_trainable_names(projector_parameters: list[str]) -> list[str]:
    prefix = "model.visual.merger."
    values = []
    for name in projector_parameters:
        f.require(name.startswith(prefix), "b2.projector_parameters", "must remain inside the visual merger")
        suffix = name.removeprefix(prefix)
        values.append(f"base_model.model.model.visual.merger.modules_to_save.default.{suffix}")
    return values


def validate_trainable_scope(
    names: list[str], targets: list[str], projector_parameters: list[str]
) -> dict[str, Any]:
    """Require the live trainable set to be exactly language LoRA plus merger copy."""
    f.require(names == sorted(set(names)), "b2.trainable", "must be unique and sorted")
    language = sorted(_lora_trainable_names(targets))
    projector = sorted(_projector_trainable_names(projector_parameters))
    f.literal(names, "b2.trainable", sorted(language + projector))
    return {"all": names, "language_lora": language, "projector": projector}


def validate_adapter_state_keys(
    keys: list[str], targets: list[str], projector_parameters: list[str]
) -> list[str]:
    """Require the serialized adapter to contain no undeclared model tensors."""
    f.require(keys == sorted(set(keys)), "b2.adapter.state_keys", "must be unique and sorted")
    expected = [
        f"base_model.model.{target}.lora_{side}.weight"
        for target in targets for side in ("A", "B")
    ]
    expected.extend(f"base_model.model.{name}" for name in projector_parameters)
    f.literal(keys, "b2.adapter.state_keys", sorted(expected))
    return keys


def validate_update_inventory(
    declared: list[str], gradients: list[str], updated: list[str],
    language: list[str], projector: list[str],
) -> dict[str, Any]:
    for label, values in (("declared", declared), ("gradients", gradients), ("updated", updated),
                          ("language", language), ("projector", projector)):
        f.require(values == sorted(set(values)), f"b2.parameters.{label}", "must be unique and sorted")
    f.literal(gradients, "b2.parameters.gradients", declared)
    expected_updated = sorted([name for name in language if ".lora_B." in name] + projector)
    f.literal(updated, "b2.parameters.updated", expected_updated)
    return {
        "declared": declared,
        "finite_gradients": gradients,
        "expected_updated": expected_updated,
        "updated": updated,
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical.dumps(value) + b"\n")


def project_b1_pin(pin: Any) -> dict:
    """Project the richer paper pin onto the artifact verifier's closed input."""
    f.require(type(pin) is dict, "b2.pin", "must be a JSON object")
    required = ("model_id", "model_revision", "processor_id", "processor_revision", "upstream_metadata", "weight_manifest")
    for key in required:
        f.require(key in pin, f"b2.pin.{key}", "is required")
    weights = pin["weight_manifest"]
    f.require(type(weights) is dict, "b2.pin.weight_manifest", "must be a JSON object")
    weight_keys = ("index_path", "index_bytes", "index_sha256", "shards")
    for key in weight_keys:
        f.require(key in weights, f"b2.pin.weight_manifest.{key}", "is required")
    return {
        "model_id": pin["model_id"],
        "model_revision": pin["model_revision"],
        "processor_id": pin["processor_id"],
        "processor_revision": pin["processor_revision"],
        "upstream_metadata": pin["upstream_metadata"],
        "weight_manifest": {key: weights[key] for key in weight_keys},
    }


def run() -> None:
    config = b2_preflight.load_preflight_config(CONFIG_PATH)
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        f.literal(os.environ.get(key), f"environment.{key}", "1")
    evidence_root = Path(config["paths"]["evidence_root"])
    adapter_root = evidence_root / "adapter"
    f.require(not adapter_root.exists(), "b2.adapter", "output already exists; one-shot run cannot overwrite")

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import b1_native_preflight as b1_native
    import torch
    import torch.nn.functional as functional
    from peft import LoraConfig, get_peft_model
    from transformers import Qwen2_5_VLForConditionalGeneration

    f.require(torch.cuda.is_available(), "runtime.cuda", "CUDA is unavailable")
    f.literal(torch.cuda.device_count(), "runtime.cuda.device_count", 1)
    visible_devices = f.text(os.environ.get("CUDA_VISIBLE_DEVICES"), "runtime.CUDA_VISIBLE_DEVICES")
    torch.cuda.set_device(0)
    device = torch.device("cuda:0")
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats()

    expected_versions = {"python": config["runtime"]["python"]}
    expected_versions.update({key: config["runtime"][key] for key in _RUNTIME_PACKAGES})
    observed_versions = {"python": platform.python_version()}
    observed_versions.update({key: importlib.metadata.version(distribution) for key, distribution in _RUNTIME_PACKAGES.items()})
    b1_native.validate_runtime_identity(expected_versions, observed_versions)

    b1_config = b1_preflight.load_preflight_config(B1_CONFIG_PATH)
    f.literal(b1_config["model"], "b2.b1_model", {
        "allowed_files": b1_config["model"]["allowed_files"],
        "model_id": config["model"]["model_id"],
        "revision": config["model"]["revision"],
    })
    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    artifact_manifest = b1_preflight.verify_pinned_artifacts(
        config=b1_config, pin=project_b1_pin(pin), root=config["paths"]["model_root"]
    )
    b1_terminal = canonical.loads((Path(config["paths"]["b1_evidence_root"]) / "terminal-run.json").read_bytes())
    b1_reload = canonical.loads((Path(config["paths"]["b1_evidence_root"]) / "offline-reload.json").read_bytes())
    f.literal(b1_terminal.get("status"), "b2.b1_terminal.status", "passed")
    f.literal(b1_terminal.get("exit_code"), "b2.b1_terminal.exit_code", 0)
    f.literal(b1_reload.get("status"), "b2.b1_reload.status", "passed")
    f.literal(b1_reload.get("network_guard_proven"), "b2.b1_reload.network_guard_proven", True)

    started = time.monotonic()
    model_root = Path(config["paths"]["model_root"])
    processor = b1_native.load_pil_processor(model_root)
    processor.tokenizer.padding_side = "left"
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_root, local_files_only=True, trust_remote_code=False,
        torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map=None,
    ).to(device)
    f.literal(type(model).__name__, "b2.model.class", "Qwen2_5_VLForConditionalGeneration")
    f.literal(model.config._attn_implementation, "b2.model.attention", "sdpa")

    base_projector = sorted(
        name for name, _ in model.named_parameters()
        if name.startswith(config["architecture"]["projector_module"] + ".")
    )
    f.literal(base_projector, "b2.projector.parameters", config["architecture"]["projector_parameters"])
    targets = b1_native.exact_lora_targets(name for name, _ in model.named_modules())

    specs = [b1_native.fixture_specs()[0], b1_native.fixture_specs()[2]]
    images, fixture_evidence = b1_native.make_images(specs)
    prompts = ["Name the synthetic pattern.", "Name this different synthetic pattern briefly."]
    answers = [" blue", " striped"]
    batch, prompt_counts = b1_native._encode(processor, images, prompts, answers)
    label_rows = b1_native.build_target_only_labels(
        batch["input_ids"].tolist(), batch["attention_mask"].tolist(), prompt_counts
    )
    batch["labels"] = torch.tensor(label_rows, dtype=torch.long)
    inputs = b1_native._device_batch(batch, device)

    architecture = config["architecture"]
    adapter_config = LoraConfig(
        r=architecture["lora_rank"], lora_alpha=architecture["lora_alpha"],
        lora_dropout=architecture["lora_dropout"], bias="none", target_modules=targets,
        modules_to_save=architecture["modules_to_save"], task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, adapter_config)
    declared = sorted(name for name, parameter in model.named_parameters() if parameter.requires_grad)
    scope = validate_trainable_scope(declared, targets, base_projector)
    before = {
        name: parameter.detach().cpu().clone()
        for name, parameter in model.named_parameters() if parameter.requires_grad
    }
    optimizer = torch.optim.AdamW(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=architecture["learning_rate"], weight_decay=0.0,
    )
    model.train()
    optimizer.zero_grad(set_to_none=True)
    output = model(**inputs, use_cache=False, return_dict=True)
    b1_native._finite(torch, output.logits, "b2.training.logits")
    b1_native._finite(torch, output.loss, "b2.training.loss")
    shifted_logits = output.logits[..., :-1, :].contiguous().float()
    shifted_labels = inputs["labels"][..., 1:].contiguous()
    manual_loss = functional.cross_entropy(
        shifted_logits.view(-1, shifted_logits.size(-1)),
        shifted_labels.view(-1), ignore_index=-100,
    )
    loss_delta = float((manual_loss - output.loss.float()).abs().item())
    f.require(loss_delta <= 1e-5, "b2.training.loss", "manual shifted CE disagrees with framework loss")
    output.loss.backward()
    gradients = []
    parameter_records = []
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        f.require(parameter.grad is not None, f"b2.parameters.{name}.gradient", "gradient is missing")
        b1_native._finite(torch, parameter.grad, f"b2.parameters.{name}.gradient")
        gradients.append(name)
        parameter_records.append({
            "name": name,
            "shape": list(parameter.shape),
            "parameter_dtype": str(parameter.dtype),
            "gradient_dtype": str(parameter.grad.dtype),
            "gradient_max_abs": float(parameter.grad.detach().float().abs().max().item()),
            "component": "projector" if name in scope["projector"] else "language_lora",
        })
    optimizer.step()
    updated = sorted(
        name for name, parameter in model.named_parameters()
        if parameter.requires_grad and not torch.equal(before[name], parameter.detach().cpu())
    )
    update_inventory = validate_update_inventory(
        declared, sorted(gradients), updated, scope["language_lora"], scope["projector"]
    )

    model.eval()
    reference_batch, _ = b1_native._encode(processor, [images[0]], [prompts[0]])
    reference_inputs = b1_native._device_batch(reference_batch, device)
    with torch.no_grad():
        reference_output = model(**reference_inputs, use_cache=False, return_dict=True)
    reload_reference = {
        "fixture_id": specs[0]["id"],
        "prompt": prompts[0],
        "input_ids": reference_batch["input_ids"][0].tolist(),
        "attention_mask": reference_batch["attention_mask"][0].tolist(),
        "logits_first_32": reference_output.logits[0, -1, :32].float().cpu().tolist(),
        "logit_atol": LOGIT_ATOL,
        "pixel_values_sha256": b1_native._tensor_sha(reference_batch["pixel_values"]),
    }

    adapter_root.mkdir(mode=0o700, parents=False)
    model.save_pretrained(adapter_root, safe_serialization=True)
    generated_card = adapter_root / "README.md"
    if generated_card.exists():
        f.require(generated_card.is_file() and not generated_card.is_symlink(), "b2.adapter.README", "must be regular")
        generated_card.unlink()
    written_config = b1_native.write_exact_adapter_scope(adapter_root, targets, str(model_root))
    f.literal(written_config.get("modules_to_save"), "b2.adapter.modules_to_save", architecture["modules_to_save"])
    from safetensors import safe_open
    with safe_open(adapter_root / "adapter_model.safetensors", framework="pt", device="cpu") as stream:
        adapter_state_keys = validate_adapter_state_keys(list(stream.keys()), targets, base_projector)
    adapter_files = b1_native.inventory_adapter(adapter_root)

    gpu_receipt = b1_native.parse_nvidia_smi_receipt(subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version,name,memory.total", "--format=csv,noheader,nounits", "-i", "0"],
        check=True, capture_output=True, text=True,
    ).stdout.strip())
    elapsed = time.monotonic() - started
    result = {
        "schema": "mmbu.b2.projector_preflight.result.v1",
        "status": "native_step_complete_offline_reload_pending",
        "recipe_id": architecture["recipe_id"],
        "seed": SEED,
        "synthetic_only": True,
        "optimizer_steps": 1,
        "b1_provenance": {
            "artifact_manifest": artifact_manifest,
            "terminal_status": b1_terminal["status"],
            "offline_reload_status": b1_reload["status"],
        },
        "fixtures": fixture_evidence,
        "training": {
            "loss": float(output.loss.detach().float().item()),
            "manual_loss": float(manual_loss.detach().item()),
            "loss_abs_delta": loss_delta,
            "trainable_scope": scope,
            "update_inventory": update_inventory,
            "parameter_records": parameter_records,
        },
        "adapter_files": adapter_files,
        "adapter_state_keys": adapter_state_keys,
        "reload_reference": reload_reference,
        "resources": {
            "elapsed_seconds": elapsed,
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
            "peak_reserved_bytes": torch.cuda.max_memory_reserved(),
            "gpu_name": torch.cuda.get_device_name(),
            "cuda_visible_devices": visible_devices,
            "cuda_runtime": torch.version.cuda,
            "nvidia_smi": gpu_receipt,
            "slurm_job_id": f.text(os.environ.get("SLURM_JOB_ID"), "runtime.SLURM_JOB_ID"),
            "argv": sys.argv,
        },
        "versions": observed_versions,
    }
    _write_json(evidence_root / "native-preflight.json", result)


if __name__ == "__main__":
    try:
        run()
    except f.ContractViolation as exc:
        sys.stderr.write(str(exc) + "\n")
        raise SystemExit(2)
