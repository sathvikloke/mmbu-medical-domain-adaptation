# B2 dual-objective native preflight trace

**Date:** October 23, 2026

**Scope:** synthetic engineering evidence only

**Claim boundary:** no biomedical data, MMBU example, model-quality result, clinical claim, upload, or submission

## Question

Can the verified Qwen2.5-VL B2-P language-LoRA plus visual-merger path consume separate answer and context calls
while preserving prospectively declared independent-unit mass, target-length normalization, and a global weighted
numerator/denominator across gradient accumulation?

## Frozen objective

The synthetic slice contains two independent units. Unit `u1` assigns `3/4` mass to an answer call and `1/4` to a
separate context call; unit `u2` has no applicable context target and assigns all mass to its answer call under the
registered reallocation rule. Each view divides its mass uniformly across its shifted assistant-target tokens. Prompt,
image, and padding positions have zero loss weight. The optimizer consumes the sum of weighted token-loss numerators
divided by the total unit mass; it never averages view or microbatch means.

## Attempt ledger

| Attempt | Native condition | Result | Interpretation |
|---|---|---|---|
| 1, job `85468` | Three-view concatenated batch versus unequal `1 + 2` microbatch partition; fixtures 0 and 2 | Failed before optimizer: loss drift `0.012437820434570312` exceeded frozen `0.00390625` | The exact arithmetic passed on CPU, but native BF16 output changed with batch shape |
| 2, job `85469` | Untouched fixtures 1 and 3; same concatenated-versus-partitioned test; BF16-derived `0.03125` loss tolerance | Failed before optimizer: loss drift `0.0949854850769043`, gradient max drift `0.0390625`, relative L2 `0.0663016`, cosine `0.9982267` | Independent confirmation rejected a tolerance-only repair; batch-shape invariance is not established |
| 3, job `85472` | Untouched fixtures 4 and 5; fixed singleton microbatches; forward versus reverse accumulation order | Passed: zero loss drift, gradient max drift `0.00048828125`, relative L2 `0.0023840`, cosine `0.9999972` | The frozen singleton execution path preserves the objective and is order-stable within the original strict bounds |

Attempts 1 and 2 are retained as failures. Attempt 3 is a successor execution condition, not a relabelled retry and
not evidence that arbitrary batch shapes are interchangeable.

## Successful native receipt

- GPU: one NVIDIA A100 80 GB PCIe; job `85472`; scheduler elapsed 23 seconds.
- Measured native section: `13.1422` seconds.
- Peak CUDA allocated: `17,326,376,960` bytes; peak reserved: `17,890,803,712` bytes.
- Target tokens: answer `2`, context `13`, answer `2`; total objective mass exactly `2`.
- Forward and reverse weighted loss: `9.540764033794403` in both orders.
- All 117 declared trainable tensors had finite gradients.
- The one optimizer step updated exactly 56 language LoRA-B tensors plus all five visual-merger tensors.
- Network remained disabled and the pinned model/runtime cache was reused; no acquisition occurred.

Primary receipts:

- [successful native record](../../outputs/b2-dual-objective-preflight/attempt-3/native-dual-objective.json)
- [prevalidation measurement](../../outputs/b2-dual-objective-preflight/attempt-3/prevalidation-measurement.json)
- [terminal record](../../outputs/b2-dual-objective-preflight/attempt-3/terminal-run.json)
- [first failed terminal record](../../outputs/b2-dual-objective-preflight/attempt-1/terminal-run.json)
- [second failed measurement](../../outputs/b2-dual-objective-preflight/attempt-2/prevalidation-measurement.json)

## Decision and remaining blocker

The executable reference condition is temporarily **microbatch size one with complete-cycle stopping**. This is a
correctness reference, not a throughput recommendation. The concatenated-batch trap remains failed for heterogeneous
sequence/image shapes, so a later trainer must either retain the fixed singleton condition or prospectively validate a
shape-bucketed/matched-padding successor before claiming larger-batch equivalence. This preflight raises engineering
readiness only; it does not raise learner novelty or empirical biomedical evidence.
