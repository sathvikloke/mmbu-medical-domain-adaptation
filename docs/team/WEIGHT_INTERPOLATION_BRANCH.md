# Post-B2 weight-interpolation branch

**Status:** optional competition ablation; no model/result claim  
**Priority:** after ordinary B2 and preservation controls  
**Novelty:** established technique, not a project contribution

## Hypothesis

If a fully adapted B2 checkpoint gains task performance but loses useful base behavior, interpolating the learned
parameter delta toward the frozen base may recover a better base-relative score than either endpoint. This is adjacent
to [WiSE-FT](https://arxiv.org/abs/2109.01903) and model-soup/interpolation work; the only project-specific value is a
prospectively bounded competition decision.

For compatible tensors, form `theta(alpha) = theta_base + alpha * (theta_adapted - theta_base)`. When B2 is represented
as an adapter, interpolation must operate on the effective update actually applied at inference, not on mismatched LoRA
factor gauges. The exported candidate must be one merged, fresh-loadable checkpoint or one organizer-approved native
adapter artifact. No runtime ensemble or multiple test call is allowed.

## Frozen candidate set

The only eligible coefficients are `alpha in {0.60, 0.80, 1.00}`. They are declared before checkpoint results are
opened. `alpha=1.00` is ordinary B2 and is not duplicated as a new condition. No coefficient may be added after viewing
development or validation results.

Run interpolation only for:

- the selected ordinary B2 checkpoint; and
- at most one base-conditional-preservation checkpoint if that branch already passed its own gate.

Every coefficient uses identical prompts, decoding, evaluator, data roles, and paired resamples. The branch receives no
additional training budget.

## Required checks

1. Prove tensor-name, shape, dtype, tied-weight, embedding, and processor compatibility against the pinned base.
2. Prove equivalence between effective adapter-delta interpolation and the exported artifact on deterministic synthetic
   inputs within a registered numeric tolerance.
3. Report task, context, source, output validity, positive/negative flips, and visual target tracking separately.
4. Report measured latency, peak memory, artifact bytes, and active FLOPs; do not call interpolation efficient from
   trainable-parameter counts.
5. Fresh-load the selected artifact twice without a network and reproduce its deterministic forward receipt.

## Promotion and kill rule

Promote an interpolated point only if it clears the same flagship gates as ordinary B2, has a positive paired lower
bound against `alpha=1.00` on the organizer-compatible composite proxy, and does not trade away either task or context
minimums. If no interpolated point dominates under the frozen rule, retain ordinary B2. Nonlinear function behavior,
normalization statistics, quantization, and tied parameters can make weight-space interpolation fail even when the
arithmetic is correct.

## Ratings

| Axis | Score / 10 | Reason |
|---|---:|---|
| Competition upside | 8.0 | Directly targets the gain-versus-retention tradeoff with no extra training |
| Feasibility | 8.0 | Small closed candidate set, but export equivalence and adapter gauge must be proven |
| Method novelty | 1.5 | Weight interpolation is established |
| Current local evidence | 0.5 | No native B2 checkpoint or interpolation result exists |
