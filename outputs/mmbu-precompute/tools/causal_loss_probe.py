#!/usr/bin/env python3
"""Synthetic CPU loss/gradient arithmetic; no model, weights, forward pass or GPU.

One unequal-target-count microbatch fixture is checked against a combined batch
and independent scalar/analytical references. This is not a production trainer.
The output path must be new. No downloads, installs or external data are used.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys


IGNORE_INDEX = -100
PAD_TOKEN_ID = 0
EOS_TOKEN_ID = 1
VOCABULARY_SIZE = 7
SEQUENCE_LENGTH = 8
PROMPT_LENGTHS = [2, 4, 2]
TOKENS = [[2, 3, 4, 5, 1], [3, 4, 2, 5, 6, 1], [4, 2, 5, 6, 2, 4, 1]]
MICROBATCHES = [[0], [1, 2]]
TOLERANCE = 1e-12


def shifted_cross_entropy_sum(logits, labels):
    """Return unweighted CE sum and count over nonignored causal targets.

This deliberately small probe helper rejects zero-target calls. It is not a
distributed reducer or data collator. Labels refer to tokens at input positions;
logit at t predicts label at t+1. All data must be explicit CPU tensors.
"""
    import torch
    import torch.nn.functional as functional
    if logits.device.type != "cpu" or labels.device.type != "cpu":
        raise ValueError("probe tensors must be on CPU")
    if logits.ndim != 3 or labels.ndim != 2 or tuple(logits.shape[:2]) != tuple(labels.shape):
        raise ValueError("expected logits [batch,sequence,vocabulary] and matching labels")
    if labels.dtype != torch.long or not logits.is_floating_point() or logits.shape[1] < 2:
        raise ValueError("long labels, floating logits, and sequence length >=2 required")
    targets = labels[:, 1:]
    valid = targets != IGNORE_INDEX
    count = int(valid.sum().item())
    if count == 0:
        raise ValueError("zero nonignored shifted targets; loss denominator is undefined")
    if bool(((targets[valid] < 0) | (targets[valid] >= logits.shape[-1])).any()):
        raise ValueError("target ID outside the synthetic vocabulary")
    total = functional.cross_entropy(logits[:, :-1, :].reshape(-1, logits.shape[-1]),
                                     targets.reshape(-1), ignore_index=IGNORE_INDEX, reduction="sum")
    return total, count


def scalar_reference(values, labels):
    """Independent stdlib log-sum-exp CE and analytical dL/dlogits."""
    contributions = []
    gradients = [[[0.0 for _ in row] for row in example] for example in values]
    for example, matrix in enumerate(values):
        for predictor in range(len(matrix) - 1):
            target = labels[example][predictor + 1]
            if target == IGNORE_INDEX:
                continue
            vector = matrix[predictor]
            maximum = max(vector)
            exp = [math.exp(value - maximum) for value in vector]
            denominator = math.fsum(exp)
            contributions.append(maximum + math.log(denominator) - vector[target])
            gradients[example][predictor] = [item / denominator - int(k == target)
                                              for k, item in enumerate(exp)]
    if not contributions:
        raise ValueError("scalar reference has no valid targets")
    count = len(contributions)
    gradients = [[[value / count for value in row] for row in example] for example in gradients]
    return math.fsum(contributions) / count, gradients


def run_probe():
    import torch
    torch.set_num_threads(1)
    input_ids, attention_mask, labels = [], [], []
    for tokens, prompt in zip(TOKENS, PROMPT_LENGTHS):
        padding = SEQUENCE_LENGTH - len(tokens)
        input_ids.append(tokens + [PAD_TOKEN_ID] * padding)
        attention_mask.append([1] * len(tokens) + [0] * padding)
        labels.append([IGNORE_INDEX] * prompt + tokens[prompt:] + [IGNORE_INDEX] * padding)
    # Deterministic scalar construction: no RNG, token embedding or model layer.
    values = [[[math.sin((row + 1) * (position + 1) * (token + 1) * .17)
                + .07 * token * token - .2 * row * token
                for token in range(VOCABULARY_SIZE)]
               for position in range(SEQUENCE_LENGTH)] for row in range(len(TOKENS))]
    label_tensor = torch.tensor(labels, dtype=torch.long, device="cpu")

    def leaf():
        return torch.tensor(values, dtype=torch.float64, device="cpu", requires_grad=True)

    combined_logits = leaf()
    combined_sum, target_count = shifted_cross_entropy_sum(combined_logits, label_tensor)
    combined_loss = combined_sum / target_count
    combined_loss.backward()
    combined_gradient = combined_logits.grad.detach().clone()

    accumulated_logits = leaf()
    micro_results = []
    correct_loss_parts = []
    for indices in MICROBATCHES:
        total, count = shifted_cross_entropy_sum(accumulated_logits[indices], label_tensor[indices])
        scaled = total / target_count
        scaled.backward()
        correct_loss_parts.append(float(scaled.detach()))
        micro_results.append({"example_indices": indices, "valid_shifted_targets": count,
                              "cross_entropy_sum": float(total.detach()),
                              "microbatch_mean": float(total.detach()) / count,
                              "correct_global_denominator": target_count,
                              "correct_loss_contribution": float(scaled.detach())})
    accumulated_loss = math.fsum(correct_loss_parts)
    accumulated_gradient = accumulated_logits.grad.detach().clone()

    naive_logits = leaf()
    naive_loss_parts = []
    for indices in MICROBATCHES:
        total, count = shifted_cross_entropy_sum(naive_logits[indices], label_tensor[indices])
        scaled = total / count / len(MICROBATCHES)
        scaled.backward()
        naive_loss_parts.append(float(scaled.detach()))
    naive_loss = math.fsum(naive_loss_parts)
    naive_gradient = naive_logits.grad.detach().clone()

    reference_loss, reference_gradient_values = scalar_reference(values, labels)
    reference_gradient = torch.tensor(reference_gradient_values, dtype=torch.float64, device="cpu")
    valid = label_tensor[:, 1:] != IGNORE_INDEX
    ignored_gradient_max = float(combined_gradient[:, :-1, :][~valid].abs().max())
    last_gradient_max = float(combined_gradient[:, -1, :].abs().max())
    boundary_checks = []
    eos_checks = []
    for row, tokens in enumerate(TOKENS):
        boundary = PROMPT_LENGTHS[row] - 1
        eos_label_position = len(tokens) - 1
        boundary_checks.append({"example_index": row, "last_prompt_logit_position": boundary,
            "first_assistant_label_position": boundary + 1,
            "target_id": labels[row][boundary + 1],
            "gradient_l1": float(combined_gradient[row, boundary].abs().sum())})
        eos_checks.append({"example_index": row, "eos_label_position": eos_label_position,
            "predicting_logit_position": eos_label_position - 1,
            "target_id": labels[row][eos_label_position],
            "gradient_l1": float(combined_gradient[row, eos_label_position - 1].abs().sum())})
    try:
        shifted_cross_entropy_sum(leaf(), torch.full_like(label_tensor, IGNORE_INDEX))
    except ValueError as error:
        zero_target = {"rejected": True, "error": str(error)}
    else:
        zero_target = {"rejected": False}
    loss_difference = abs(float(combined_loss.detach()) - accumulated_loss)
    gradient_difference = float((combined_gradient - accumulated_gradient).abs().max())
    naive_loss_difference = abs(float(combined_loss.detach()) - naive_loss)
    naive_gradient_difference = float((combined_gradient - naive_gradient).abs().max())
    analytical_difference = float((combined_gradient - reference_gradient).abs().max())
    checks = {
        "right_padding_has_ignored_labels": all(
            mask == [1] * len(tokens) + [0] * (SEQUENCE_LENGTH - len(tokens))
            and all(label == IGNORE_INDEX for label, active in zip(lab, mask) if not active)
            for tokens, mask, lab in zip(TOKENS, attention_mask, labels)),
        "unequal_microbatch_counts_are_3_and_7": [x["valid_shifted_targets"] for x in micro_results] == [3, 7],
        "counts_sum_to_combined_denominator": sum(x["valid_shifted_targets"] for x in micro_results) == target_count == 10,
        "combined_loss_matches_independent_scalar_reference": abs(float(combined_loss.detach()) - reference_loss) <= TOLERANCE,
        "combined_gradient_matches_analytical_reference": analytical_difference <= TOLERANCE,
        "token_normalized_accumulation_loss_matches_combined": loss_difference <= TOLERANCE,
        "token_normalized_accumulation_gradients_match_combined": gradient_difference <= TOLERANCE,
        "naive_microbatch_mean_loss_differs": naive_loss_difference > 1e-6,
        "naive_microbatch_mean_gradients_differ": naive_gradient_difference > 1e-6,
        "ignored_shifted_target_prediction_sites_have_zero_gradient": ignored_gradient_max == 0,
        "final_unshifted_logits_have_zero_gradient": last_gradient_max == 0,
        "last_prompt_logits_predict_first_assistant_tokens_with_gradient": all(x["gradient_l1"] > 0 for x in boundary_checks),
        "all_eos_targets_are_supervised_at_preceding_logits": all(
            x["target_id"] == EOS_TOKEN_ID and x["gradient_l1"] > 0 for x in eos_checks),
        "zero_target_denominator_rejected": zero_target["rejected"],
        "all_logits_and_gradients_are_finite_cpu_float64": all(
            x.device.type == "cpu" and x.dtype == torch.float64 and bool(torch.isfinite(x).all())
            for x in (combined_logits, combined_gradient, accumulated_gradient, naive_gradient, reference_gradient)),
    }
    return {
        "schema_version": 1, "kind": "synthetic_causal_loss_normalization_probe",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if all(checks.values()) else "failed", "checks": checks,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(), "torch": torch.__version__,
        "device": "cpu", "dtype": "float64", "torch_threads": 1,
        "absolute_tolerance": TOLERANCE, "model_executed": False, "model_weights_loaded": False,
        "gpu_used": False, "training_performed": False, "random_numbers_used": False,
        "fixture": {"vocabulary_size": VOCABULARY_SIZE, "ignore_index": IGNORE_INDEX,
                    "pad_token_id": PAD_TOKEN_ID, "eos_token_id": EOS_TOKEN_ID,
                    "prompt_lengths": PROMPT_LENGTHS, "input_ids": input_ids,
                    "attention_mask": attention_mask, "labels": labels, "logits": values,
                    "microbatches": MICROBATCHES},
        "target_count": target_count, "microbatch_results": micro_results,
        "combined_cross_entropy_sum": float(combined_sum.detach()),
        "combined_loss": float(combined_loss.detach()), "scalar_reference_loss": reference_loss,
        "token_normalized_accumulation_loss": accumulated_loss,
        "naive_equal_mean_accumulation_loss": naive_loss,
        "absolute_loss_difference_correct": loss_difference,
        "maximum_absolute_gradient_difference_correct": gradient_difference,
        "absolute_loss_difference_naive": naive_loss_difference,
        "maximum_absolute_gradient_difference_naive": naive_gradient_difference,
        "maximum_absolute_gradient_difference_analytical": analytical_difference,
        "maximum_gradient_at_ignored_prediction_sites": ignored_gradient_max,
        "maximum_gradient_at_final_logits": last_gradient_max,
        "prompt_assistant_boundary_checks": boundary_checks, "eos_checks": eos_checks,
        "zero_target_probe": zero_target,
        "gradients": {"combined": combined_gradient.tolist(),
                      "token_normalized_microbatches": accumulated_gradient.tolist(),
                      "naive_equal_microbatch_means": naive_gradient.tolist(),
                      "independent_analytical": reference_gradient_values},
        "limits": [
            "Synthetic logits are independent leaf tensors, not outputs of any model.",
            "Only unweighted, unsmoothed causal cross entropy with ignore_index=-100 is tested.",
            "Only logit derivatives are checked; prompt hidden states and model parameters can receive gradients in a real model.",
            "No mixed precision, optimizer step, distributed reduction, dropout, fused kernel, trainer integration, or GPU behavior is tested.",
            "A real accumulation window must count its actual valid shifted targets; this denominator is not a universal trainer scaling rule.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New JSON report path; parent must exist")
    args = parser.parse_args(argv)
    try:
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError("output already exists")
        report = run_probe()
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write("\n")
    except (ImportError, OSError, ValueError, RuntimeError) as error:
        print(json.dumps({"status": "unavailable_or_failed", "error_type": type(error).__name__,
                          "error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "checks": len(report["checks"]),
                      "combined_loss": report["combined_loss"],
                      "token_normalized_loss": report["token_normalized_accumulation_loss"],
                      "naive_equal_mean_loss": report["naive_equal_mean_accumulation_loss"],
                      "model_executed": False, "gpu_used": False}))
    return 0 if report["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
