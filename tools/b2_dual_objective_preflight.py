#!/usr/bin/env python3
"""One-job synthetic native proof of the B2 answer/context objective adapter."""

from __future__ import annotations

from fractions import Fraction
import importlib.metadata
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from mmbu_phase1 import b2_dual_preflight, dual_objective
from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f


REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "config/phase1/b2-dual-objective-preflight.json"
SEED = 20261023


def exposure_row(unit, endpoint, view, share, endpoint_share, token_count, target, fields=()):
    return {
        "accepted": True, "base_unit_mass": Fraction(1), "effective_unit_mass": Fraction(1),
        "endpoint_id": endpoint, "endpoint_share": endpoint_share, "independent_unit_id": unit,
        "prospective_balance_multiplier": Fraction(1), "rejection_reason": None,
        "requested_context_fields": list(fields), "source_family_id": "synthetic-engineering",
        "split_group_id": f"group-{unit}", "supervised_token_count": token_count,
        "target_bytes": target.encode("utf-8"), "task_form": "synthetic",
        "token_normalization_id": "uniform_within_view_v1",
        "schedule_position_or_epoch_rule": "one_complete_cycle_v1", "unit_total_mass": Fraction(1),
        "view_id": view, "view_share": share,
    }


def _encode_views(processor, b1_native, torch, records, images_by_id):
    images = [images_by_id[record["image_id"]] for record in records]
    prompts = [record["prompt"] for record in records]
    targets = [record["target"] for record in records]
    batch, prompt_counts = b1_native._encode(processor, images, prompts, targets)
    labels = b1_native.build_target_only_labels(
        batch["input_ids"].tolist(), batch["attention_mask"].tolist(), prompt_counts
    )
    batch["labels"] = torch.tensor(labels, dtype=torch.long)
    return batch, labels


def _weighted_loss(torch, functional, logits, labels, weight_rows):
    shifted_logits = logits[..., :-1, :].contiguous().float()
    shifted_labels = labels[..., 1:].contiguous()
    weights = torch.tensor(weight_rows, device=shifted_logits.device, dtype=torch.float32)
    f.literal(list(weights.shape), "objective.weight_shape", list(shifted_labels.shape))
    per_token = functional.cross_entropy(
        shifted_logits.view(-1, shifted_logits.size(-1)), shifted_labels.view(-1),
        ignore_index=-100, reduction="none",
    ).view_as(shifted_labels)
    numerator = (per_token * weights).sum()
    denominator = weights.sum()
    f.require(float(denominator.item()) > 0, "objective.denominator", "must be positive")
    loss = numerator / denominator
    return loss, numerator, denominator


def _gradient_comparison(torch, full, model):
    deltas = {}
    full_sq = micro_sq = diff_sq = dot = 0.0
    for name, parameter in model.named_parameters():
        if not parameter.requires_grad:
            continue
        f.require(parameter.grad is not None and name in full, f"gradients.{name}", "missing gradient")
        left = full[name].double()
        right = parameter.grad.detach().double().cpu()
        difference = right - left
        deltas[name] = float(difference.abs().max().item())
        full_sq += float((left * left).sum().item())
        micro_sq += float((right * right).sum().item())
        diff_sq += float((difference * difference).sum().item())
        dot += float((left * right).sum().item())
    full_norm, micro_norm = math.sqrt(full_sq), math.sqrt(micro_sq)
    f.require(full_norm > 0 and micro_norm > 0, "gradients.norm", "must be positive")
    return dict(sorted(deltas.items())), math.sqrt(diff_sq) / max(full_norm, micro_norm), dot / (full_norm * micro_norm)


def run() -> None:
    config = b2_dual_preflight.load_preflight_config(CONFIG_PATH)
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        f.literal(os.environ.get(key), f"environment.{key}", "1")
    evidence_root = Path(config["paths"]["evidence_root"])
    output_path = evidence_root / "native-dual-objective.json"
    f.require(not output_path.exists(), "evidence.output", "one-shot output already exists")

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import b1_native_preflight as b1_native
    import b2_native_preflight as b2_native
    import torch
    import torch.nn.functional as functional
    from peft import LoraConfig, get_peft_model
    from transformers import Qwen2_5_VLForConditionalGeneration

    f.require(torch.cuda.is_available(), "runtime.cuda", "CUDA unavailable")
    f.literal(torch.cuda.device_count(), "runtime.cuda.device_count", 1)
    torch.cuda.set_device(0)
    device = torch.device("cuda:0")
    torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
    torch.backends.cuda.matmul.allow_tf32 = False; torch.backends.cudnn.allow_tf32 = False
    torch.cuda.reset_peak_memory_stats()
    for package, expected in (("peft", config["runtime"]["peft"]),
                              ("torch", config["runtime"]["torch"]),
                              ("transformers", config["runtime"]["transformers"])):
        f.literal(importlib.metadata.version(package), f"runtime.{package}", expected)
    f.literal(platform.python_version(), "runtime.python", config["runtime"]["python"])

    started = time.monotonic()
    model_root = Path(config["paths"]["model_root"])
    processor = b1_native.load_pil_processor(model_root)
    processor.tokenizer.padding_side = "left"
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_root, local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
        attn_implementation="sdpa", device_map=None,
    ).to(device)
    # Attempts 1 and 2 used fixtures 0-3.  This successor uses untouched
    # conversion fixtures and freezes singleton microbatches for every view.
    specs = [b1_native.fixture_specs()[4], b1_native.fixture_specs()[5]]
    images, fixtures = b1_native.make_images(specs)
    images_by_id = {"image-a": images[0], "image-b": images[1]}
    records = [
        {"view_id": "u1-task", "image_id": "image-a", "prompt": "Name the synthetic tone.",
         "target": " gray", "unit": "u1", "endpoint": "task"},
        {"view_id": "u1-context", "image_id": "image-a",
         "prompt": "Return synthetic modality and pattern as JSON.",
         "target": ' {"modality":"synthetic","pattern":"monochrome"}', "unit": "u1", "endpoint": "context"},
        {"view_id": "u2-task", "image_id": "image-b",
         "prompt": "Name this synthetic channel pattern briefly.", "target": " alpha",
         "unit": "u2", "endpoint": "task"},
    ]
    batches_by_view = {}
    labels_by_view = {}
    counts = []
    for record in records:
        batch, singleton_labels = _encode_views(processor, b1_native, torch, [record], images_by_id)
        batches_by_view[record["view_id"]] = batch
        labels_by_view[record["view_id"]] = singleton_labels[0]
        counts.append(sum(token != -100 for token in singleton_labels[0][1:]))
    rows = [
        exposure_row("u1", "task", "u1-task", Fraction(3, 4), Fraction(3, 4), counts[0], records[0]["target"]),
        exposure_row("u1", "context", "u1-context", Fraction(1, 4), Fraction(1, 4), counts[1],
                     records[1]["target"], ("modality", "pattern")),
        exposure_row("u2", "task", "u2-task", Fraction(1), Fraction(1), counts[2], records[2]["target"]),
    ]
    plan = dual_objective.compile_plan(rows, labels_by_view)

    targets = b1_native.exact_lora_targets(name for name, _ in model.named_modules())
    base_projector = sorted(name for name, _ in model.named_parameters() if name.startswith("model.visual.merger."))
    adapter = LoraConfig(r=2, lora_alpha=4, lora_dropout=0, bias="none", target_modules=targets,
                         modules_to_save=["visual.merger"], task_type="CAUSAL_LM")
    model = get_peft_model(model, adapter)
    declared = sorted(name for name, parameter in model.named_parameters() if parameter.requires_grad)
    scope = b2_native.validate_trainable_scope(declared, targets, base_projector)
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=0.01, weight_decay=0)
    before = {name: parameter.detach().cpu().clone() for name, parameter in model.named_parameters()
              if parameter.requires_grad}
    objective = config["objective"]
    f.literal(objective["microbatch_size"], "objective.microbatch_size", 1)
    global_denominator = float(plan["total_mass"])

    def accumulate(order):
        optimizer.zero_grad(set_to_none=True)
        total_numerator = 0.0
        receipts = []
        for index, view_id in enumerate(order):
            inputs = b1_native._device_batch(batches_by_view[view_id], device)
            output = model(**inputs, use_cache=False, return_dict=True)
            weights = dual_objective.runtime_float_weights(
                plan, [view_id], [labels_by_view[view_id]]
            )
            _, numerator, denominator = _weighted_loss(
                torch, functional, output.logits, inputs["labels"], weights
            )
            (numerator / global_denominator).backward()
            total_numerator += float(numerator.detach().item())
            receipts.append({"index": index, "view_id": view_id,
                             "mass": float(denominator.detach().item()),
                             "weighted_numerator": float(numerator.detach().item()),
                             "ordinary_token_mean_loss": float(output.loss.detach().float().item())})
        gradients = {name: parameter.grad.detach().float().cpu().clone()
                     for name, parameter in model.named_parameters() if parameter.requires_grad}
        return total_numerator / global_denominator, gradients, receipts

    model.train()
    reference_order, reversed_order = objective["comparison_orders"]
    reference_loss, reference_gradients, reference_receipts = accumulate(reference_order)
    reversed_loss, _, reversed_receipts = accumulate(reversed_order)
    deltas, relative_l2, cosine = _gradient_comparison(torch, reference_gradients, model)
    prevalidation = {
        "schema": "mmbu.b2.dual_objective_prevalidation.v1",
        "status": "measurement_complete_validation_pending",
        "synthetic_only": True,
        "fixture_ids": [spec["id"] for spec in specs],
        "reference_order_weighted_loss": reference_loss,
        "reversed_order_weighted_loss": reversed_loss,
        "loss_abs_delta": abs(reference_loss - reversed_loss),
        "loss_abs_tolerance": objective["loss_abs_tolerance"],
        "gradient_max_abs": max(deltas.values()),
        "gradient_max_abs_tolerance": objective["gradient_max_abs_tolerance"],
        "gradient_relative_l2": relative_l2,
        "gradient_relative_l2_tolerance": objective["gradient_relative_l2_tolerance"],
        "gradient_cosine": cosine,
        "gradient_cosine_minimum": objective["gradient_cosine_minimum"],
    }
    (evidence_root / "prevalidation-measurement.json").write_bytes(canonical.dumps(prevalidation) + b"\n")
    equivalence = b1_native.validate_microbatch_equivalence(
        reference_loss, reversed_loss, deltas, relative_l2, cosine,
        objective["loss_abs_tolerance"], objective["gradient_max_abs_tolerance"],
        objective["gradient_relative_l2_tolerance"], objective["gradient_cosine_minimum"],
    )
    gradients = sorted(name for name, parameter in model.named_parameters() if parameter.requires_grad
                       and parameter.grad is not None and bool(torch.isfinite(parameter.grad).all().item()))
    f.literal(gradients, "gradients.finite", declared)
    optimizer.step()
    updated = sorted(name for name, parameter in model.named_parameters() if parameter.requires_grad
                     and not torch.equal(before[name], parameter.detach().cpu()))
    updates = b2_native.validate_update_inventory(
        declared, gradients, updated, scope["language_lora"], scope["projector"]
    )
    elapsed = time.monotonic() - started
    gpu = b1_native.parse_nvidia_smi_receipt(subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version,name,memory.total", "--format=csv,noheader,nounits", "-i", "0"],
        check=True, capture_output=True, text=True,
    ).stdout.strip())
    result = {
        "schema": "mmbu.b2.dual_objective_native_result.v1", "status": "passed",
        "synthetic_only": True, "optimizer_steps": 1, "seed": SEED,
        "claim_boundary": "engineering_preflight_not_biomedical_or_competition_performance",
        "fixtures": fixtures, "view_ids": [record["view_id"] for record in records],
        "target_token_counts": counts,
        "objective": {"id": objective["objective_id"], "reduction": objective["reduction"],
                      "total_mass": float(plan["total_mass"]),
                      "microbatch_size": objective["microbatch_size"],
                      "reference_order": reference_receipts,
                      "reversed_order": reversed_receipts,
                      "equivalence": equivalence},
        "parameters": {"trainable_scope": scope, "updates": updates},
        "resources": {"elapsed_seconds": elapsed,
                      "peak_cuda_allocated_bytes": int(torch.cuda.max_memory_allocated()),
                      "peak_cuda_reserved_bytes": int(torch.cuda.max_memory_reserved()), "gpu": gpu},
        "versions": {"python": platform.python_version(), "torch": importlib.metadata.version("torch"),
                     "transformers": importlib.metadata.version("transformers"),
                     "peft": importlib.metadata.version("peft")},
    }
    output_path.write_bytes(canonical.dumps(result) + b"\n")


if __name__ == "__main__":
    run()
