# Amended competition direction decision

**Decision date:** October 25, 2026

**Status:** binding design review for the bounded F0 screen; no full training, public-set evaluation, upload, or submission
**Supersedes:** the Track-2-only version of this memo at commit `855e45c`

## Decision

Treat **Track 3 as the provisional primary**, **Track 2 as the serious backup and possible second entry**, and Track 1 as inactive. Do not make a final track commitment from prose or smoke tests. Run the same generated-only F0 mechanics screen across the frozen small and medium candidates, then request approval for the first decision-bearing biomedical experiment.

This amendment corrects the previous memo's central error: it optimized within Track 2 before comparing Track 2 and Track 3 under their actual score incentives. It also withdraws the earlier numeric readiness estimate and fixed compute ceiling. Neither was calibrated evidence.

## Evidence hierarchy

1. Current formal rules and scope-specific written organizer clarifications.
2. The published challenge brief and current official site where they do not conflict.
3. Authenticated, dated organizer Discord captures at the exact scope they state.
4. Model-card metadata for engineering feasibility only.
5. Local shakedowns for mechanics and resource measurement only.

Unknown facts stay unknown. Public model metadata can change and is frozen by exact revision below. No MMBU example, label, derivative, output, or statistic informs this decision.

## Verified competition facts

The common quality term is:

`Q = 0.8T + 0.2C`

where `T` is task performance and `C` is biomedical-context performance.

| Track | Score | Verified eligibility point | Consequence |
|---|---|---|---|
| 1, frontier | `Q` | The model must be pretrained, mid-trained, and post-trained by the same organization | Inactive for this team because the plan starts from third-party weights |
| 2, medical adaptation | `Q * (T - T_base)` | The exact starting base is disclosed; no size cap is stated | Both strong final quality and reproducible positive task gain are necessary |
| 3, efficiency | `Q * (Pmax / P)^0.1` | At most 4B active parameters; MoE may have at most 12B total; all active inference components and adapters count | Final quality dominates because the size exponent is only `0.1` |

One checkpoint may enter only one track. The brief permits a team to enter multiple tracks using distinct eligible checkpoints when its registration is approved for them, and the October 18 organizer Discord clarification says the checkpoints must be separately trained and distinct. One frozen final model is designated per entered track before the deadline.

The best currently recorded deadline evidence is December 31, 2026 at 23:30 PST. The final submission destination and displayed receipt still require verification.

## Unresolved organizer questions

These are recorded rather than guessed:

1. Is this team's accepted registration approved for both Tracks 2 and 3, or is an update required?
2. May two separately trained checkpoints derived from the same public base be entered in Tracks 2 and 3?
3. May one team win awards in more than one track?
4. Before the deadline, may a designated checkpoint be replaced, and are validation attempts limited?
5. For `Qwen/Qwen3.5-4B`, does Track 3 use its exact 4,659,865,088 serialized parameters as `P`, and what exact value is `Pmax`?
6. Is the organizer's stated acceptance of the Qwen3.5 4B class a named exception only, or a general treatment of nominal 4B models above four billion exact parameters?
7. How must an already medically adapted Track 2 base such as OctoMed be disclosed and loaded?

The directly recorded organizer statement accepts the Qwen3.5 4B class, approximately 4.6B actual parameters, as the maximum in this category. That statement is not generalized to other nominal 4B checkpoints.

## Why Track 3 is the provisional primary

Track 2's multiplier is fragile. A good adapted model can still score poorly when its improvement over the disclosed base is small:

| Adapted `T` | `C` | `T_base` | `Q` | Track 2 score |
|---:|---:|---:|---:|---:|
| 0.60 | 0.50 | 0.55 | 0.58 | 0.0290 |
| 0.65 | 0.55 | 0.50 | 0.63 | 0.0945 |
| 0.70 | 0.60 | 0.65 | 0.68 | 0.0340 |
| 0.70 | 0.60 | 0.50 | 0.68 | 0.1360 |

Track 3's size multiplier is meaningful but modest. Using the literal `Pmax=4B` interpretation only for sensitivity analysis:

| Active parameters `P` | Multiplier | Raw-Q fraction that ties a 4B model |
|---:|---:|---:|
| 4.0000B | 1.0000 | 100.0% |
| 3.7546B | 1.0064 | 99.4% |
| 2.3483B | 1.0547 | 94.8% |
| 2.1275B | 1.0652 | 93.9% |
| 2.0000B | 1.0718 | 93.3% |
| 1.0000B | 1.1487 | 87.1% |

A roughly 2.13B candidate can therefore be only about 6.1% relatively worse in raw `Q` than a 4B candidate and still tie. This argues for strong small models, not for minimizing size at any cost. Track 3 avoids Track 2's requirement that a strong base also show a robust positive delta.

Official score magnitudes across Track 2 and Track 3 are separate leaderboards and must not be compared directly. The tables describe incentives only.

## Track 3 shortlist

| Candidate and frozen revision | Observed parameter count | Why screened | Blocking risk |
|---|---:|---|---|
| `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | 4,659,865,088 | Highest-ceiling organizer-recognized 4B-class candidate; Apache-2.0; native multimodal model | Exact `P/Pmax`, adapter counting, and hybrid-layer LoRA mechanics need confirmation |
| `Qwen/Qwen3-VL-2B-Instruct` @ `89644892e4d85e24eaac8bacfd4f463576704203` | 2,127,532,032 | Strong efficiency multiplier, Apache-2.0, native Transformers path | Lower raw quality ceiling |
| `OpenGVLab/InternVL3_5-2B-HF` @ `3f301ffcf3dcbb47893afae6650ea3e78d96fb6d` | 2,348,347,392 | Family-diverse challenger; Apache-2.0 | Processor/tiling and custom-code behavior |
| `HuggingFaceTB/SmolVLM2-2.2B-Instruct` @ current screened card revision | 2,246,784,880 | Apache-2.0 fallback with a simple public path | Uncertain biomedical ceiling; not in tonight's five-model F0 |

Rejected or pending for Track 3 under the literal exact-count rule: Qwen3-VL-4B (4,437,815,808), InternVL3.5-4B-HF (4,732,489,216), OctoMed-4B (4,826,771,968), Gemma/MedGemma 4B (4,300,079,472 and gated), Phi-4 multimodal (5,574,460,384), and MiniCPM-V-4.5 (8,695,895,280). Qwen2.5-VL-3B is not preferred because its research license requires separate release/legal review.

## Track 2 shortlist

| Candidate and frozen revision | Observed parameter count | Why screened | Main risk |
|---|---:|---|---|
| `Qwen/Qwen3.5-9B` @ `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | 9,653,104,368 | Likely strong final ceiling; Apache-2.0; current native VLM | Small adaptation headroom; hybrid training mechanics |
| `Qwen/Qwen3-VL-8B-Instruct` @ `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` | 8,767,123,696 | Strong current general VLM; Apache-2.0 | Positive delta may be hard to establish |
| `OpenGVLab/InternVL3_5-8B-HF` @ `741a7d03020411e666c6109218ab71e08151ef86` | 8,528,318,464 | Family-diverse 8B challenger | Custom-code/tiling risk; deferred from tonight's five-model F0 |
| `Qwen/Qwen3.5-4B` @ revision above | 4,659,865,088 | Shared small Track 2 comparator | Lower raw ceiling than 8–9B candidates |
| `Qwen/Qwen2.5-VL-7B-Instruct` @ `cc594898137f460bfe9f0759e9844b3ce807cfb5` | 8,292,166,656 | Only locally proven training/export control | Older model; prior work cannot make it the incumbent |
| `OctoMed/OctoMed-8B` @ `f5d8be54bd5170bf3824782a6f39f4dafe525d83` | 8,767,123,696 | Tests a medically adapted starting base | Reduced headroom, multiple-choice/long-think bias, disclosure risk |

An already medically adapted starting checkpoint is eligible in principle for Track 2, with improvement measured from that exact starting checkpoint. OctoMed remains a later diagnostic control, not tonight's priority.

## Invalid context evidence and required repair

The completed Lane 1 shakedown asked for `bbox_xywh`, `birads`, `image_size`, and `side`. Those are not the six published context field classes. Original `image_size` was also impossible to infer reliably after processor resizing; the scorer returned zero before partial fields could earn credit; and strict parsing conflated Markdown fences with biomedical correctness.

The historical zero results remain immutable but cannot select a model, arm, objective, or track. The successor evaluator must:

- request a dynamic applicable subset of `modality`, `submodality`, `specimen`, `body_part`, `stain`, and `medical_domain`;
- use source-authoritative values only and omit fields without defensible authority;
- require exactly one raw JSON object with exactly those keys;
- report strict validity separately;
- give field-level mean credit only after validity; and
- remain labeled `brief_snapshot`, not official-harness-equivalent.

## Frozen bounded F0 screen

Tonight's F0 checks only engineering feasibility for:

1. Qwen3.5-9B;
2. Qwen3-VL-8B-Instruct;
3. Qwen3.5-4B;
4. Qwen3-VL-2B-Instruct; and
5. InternVL3.5-2B-HF.

Each gets one generated-only image/text fixture, the same functional LoRA scope/rank/alpha/dropout and optimizer, one forward/backward pass, one optimizer update, adapter save, fresh-process offline reload, deterministic prediction check, and resource receipt. Each job is capped at one A100-hour. A failure is preserved and not rescued automatically.

F0 cannot rank model quality or select a winner. It only tells us which frozen candidates can enter a later fair experiment and supplies measured memory/runtime for that experiment.

## Resource estimate grounded in measured evidence

The completed 7B biomedical shakedown took 5:13–6:52 per adapted 128-unit arm and peaked around 19.5–20.2 GB allocated. Linear scaling of the same path to 1,024 units is roughly 42–55 minutes per run. Fifteen matched adapted runs would therefore use about 10.5–13.8 A100-hours before base evaluations, cold loads, exports, and architecture uncertainty.

The current planning range for a later five-candidate, three-seed 1,024-unit screen is **16–32 A100-hours**, to be replaced by F0 measurements. It is a range, not a budget commitment. No later screen is authorized by this memo.

## Evidence that changes the track priority

After tonight, the next requested experiment should compare unchanged and adapted candidates on one frozen external-biomedical development population with identical prompts, data, exposure, LoRA scope, and three seeds.

Track 2 becomes primary only when both are true:

1. the best medium model's base-relative task gain is positive in every seed and its paired lower confidence bound is above zero; and
2. the best small model's Track 3 adjusted `Q` is separated below the medium model's raw final quality beyond joint uncertainty.

Track 3 stays primary when the best small adjusted score is practically indistinguishable from or better than the medium route, or when medium-model adaptation gain is unstable or nonpositive.

These rules allocate team effort; they do not compare official scores across separate leaderboards.

### October 25 response-screen update

The completed matched response screen materially changed the evidence, but not yet the binding final-track decision:

- Qwen3.5-9B improved over its unchanged base in all six adapted seed/profile conditions. Its post-output group-aware 90% intervals were [+18.099, +27.344] percentage points for task-only and [+18.750, +27.995] points for dual.
- Qwen3.5-4B showed no stable base-relative response. Its corresponding intervals crossed zero for both profiles.
- The 4B route failed the predeclared raw-`Q` competitiveness check. The unresolved official Track 3 parameter treatment still prevents the required adjusted-`Q` comparison.
- The original design did not freeze the bootstrap draw count or random seed, so the intervals are exploratory and cannot retroactively promote Track 2.

Accordingly, Track 3 remains the provisional administrative primary, but the **next decision-bearing experiment is now the 9B Track 2 confirmation**, not another model search or smoke test. If a fully frozen, source-admitted confirmation again produces an all-seed positive task gain with a lower bound above zero, and the organizer resolves the Track 3 multiplier, this memo can make the final track choice from evidence instead of speculation.

## Stopping point

Stop after the decision, evaluator repair, frozen manifest, and one-attempt F0 receipts. Do not launch full training, a multi-seed campaign, MMBU public evaluation, upload, or submission. The next decision-bearing experiment requires explicit user approval.

## Public references

- Official challenge site: https://akiranishii.github.io/mmbu-challenge/
- Official challenge brief: https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf
- Official rules: https://akiranishii.github.io/mmbu-challenge/documents/mmbu-challenge-official-rules.pdf
- Qwen3.5-4B: https://huggingface.co/Qwen/Qwen3.5-4B
- Qwen3.5-9B: https://huggingface.co/Qwen/Qwen3.5-9B
- Qwen3-VL-2B: https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct
- Qwen3-VL-8B: https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct
- InternVL3.5-2B-HF: https://huggingface.co/OpenGVLab/InternVL3_5-2B-HF
- InternVL3.5-8B-HF: https://huggingface.co/OpenGVLab/InternVL3_5-8B-HF
- OctoMed-8B: https://huggingface.co/OctoMed/OctoMed-8B
