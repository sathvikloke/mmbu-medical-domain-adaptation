# Base-selection frontier red-team

**Date:** October 17, 2026  
**Scope:** prospective design logic; no model or candidate conclusion

## Disposition

The adaptation-frontier screen repairs the base-only ranking defect, but its result is narrower than “the most adaptable
model.” It can select the best response to one frozen, challenge-relevant micro-adaptation screen under one external
population and resource envelope. The repairs below are binding.

| Severity | Finding | Binding repair |
|---|---|---|
| Critical | Unknown context performance can reverse the official `S` ranking | When `C` is unavailable, compute a partial-identification interval for positive task gain: `S(C=0)=0.8T(T-B)` through `S(C=1)=(0.8T+0.2)(T-B)`. Select only under frozen robust-dominance/sensitivity rules; otherwise the base decision remains provisional |
| High | One shared LoRA screen is not intrinsic adaptability | Name the estimand “response to the frozen screen.” Do not claim a model would win after candidate-specific tuning or under every PEFT method |
| High | Tokenizers and image processors make equal examples/steps unequal exposure | Bind independent units, model-visible images, visual tokens, supervised target tokens, optimizer updates, active FLOPs, wall time, and peak memory; use exposure-matched primary plus compute-matched sensitivity |
| High | Configuration effort can favor familiar architectures | Freeze per-candidate troubleshooting attempts/time and mechanical-failure rules before F0. A later fix creates a new screen revision; it cannot selectively rescue a losing candidate |
| High | Selecting on one seed and confirming only the winner creates a winner's-curse risk | Prefer the same fixed seed set for every candidate. If resources force one screening seed plus a second selected-base confirmation, freeze that two-stage rule and population first; confirmation failure yields no selection, not promotion of the runner-up on the reused cohort |
| Critical | F1 base characterization and F2 checkpoint tuning can reuse the base-decision population | Freeze disjoint `frontier_train`, `frontier_tuning`, and untouched `frontier_decision` roles by independent group/source. Commit every F2 checkpoint and artifact before jointly opening sealed base/adapted decision outputs once |
| Medium | A gain threshold can contradict the actual score objective | Require only a prospectively justified positive/practical `T-B` floor for stability, then rank on the registered score-proxy contrast; never replace the score with raw gain |
| Medium | The proxy population can reward source-specific fit | Require held-out source families, macro-source/task and natural-mixture sensitivity, and unresolved disposition on material rank reversal |

## Context-uncertainty decision

For each base/adapted pair with `T-B > 0`, report `[S_min,S_max]` over the authoritative feasible context range. The
default range is `[0,1]`; it may be narrowed only by an independently frozen, source-authorized context proxy with its
own uncertainty. A candidate cannot be declared robustly superior if another eligible candidate's simultaneous score
interval overlaps inside the practical-equivalence margin. Point estimates from an unofficial context prompt are
descriptive only.

For `T-B <= 0`, the candidate fails the positive-adaptation gate; do not exploit multiplication by a guessed context
value or reinterpret a negative score as uncertainty. If no candidate is robustly selectable, retain the smallest
mechanically viable set and wait for authoritative context evidence or a new independent decision population.

## Claim boundary

A successful screen supports: “under the frozen external population, recipe, seeds, and resource envelope, this base
had the strongest robust adaptation-response evidence.” It does not support: “this is the best base,” “this will win the
private set,” or “this architecture is inherently more adaptable.”
