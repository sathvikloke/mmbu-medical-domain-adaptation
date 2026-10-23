# Conditional B2 system hypotheses

**Date:** October 18, 2026  
**Evidence class:** design and primary-literature collision search only  
**Status:** conditional survivor for preregistration; no admitted contribution, model result, or execution authority  
**Claim class:** competition system, not learner method

## Exact hypotheses

This design contains two separate prospective claims that may not be pooled into one interaction statistic:

1. **Training interaction:** on admitted, non-public heterogeneous biomedical sources with multiple authorized
   annotation views, source-authoritative answer/context co-training may interact positively with equal optimizer mass
   per underlying independent unit on separately frozen source-held-out task and context endpoints.
2. **Selection-protocol contrast:** prospective base selection by adaptation response may beat untouched-base selection
   on a second untouched cohort under a separately frozen decision function.

Visual-dependence and preservation requirements are conjunctive safety/promotion gates, not randomized factors and not
parts of a four-way causal interaction. The two claims require separate decisions; success on one cannot rescue failure
on the other or be averaged into a post-hoc system score.

This is the only surviving non-learner system package from the October 18 search, containing two separately tested
hypotheses. It is not a claim that shared LoRA,
multitask supervision, context targets, loss normalization, preservation, base comparison, or medical competition
packaging is new. Absence of the exact package from a scoped search does not support “first” language.

## Closest complete-system boundary

| Antecedent | What it already establishes | Remaining boundary |
|---|---|---|
| [FLARE task-specific LoRA](https://arxiv.org/abs/2610.19901) | Frozen quantized Qwen3.5-9B, question-selected task adapters, task-specific ranks/prompts/image budgets, class rebalancing, grouped internal holdout, hidden-organizer validation, deterministic container, and runtime/artifact reporting | Does not establish the exact training interaction or separate selection-protocol contrast below |
| [Two-Stage Mixture-of-LoRA](https://arxiv.org/abs/2609.14350) | One shared plus six task-specific LoRAs, joint then task-specific refinement, modality-balanced continuation for classification and regression, and heterogeneous medical outputs | Mandatory matched shared/specialist system comparator |
| [Sparse Spectral LoRA / MedQwen](https://arxiv.org/abs/2604.01310) | Routed spectral LoRA experts across 23 medical datasets with explicit cross-dataset interference and forgetting analysis | Strong comparator if faithful code/resource matching is possible |
| [Point, Detect, Count](https://arxiv.org/abs/2505.16647) | Qwen LoRA jointly instruction-tuned for medical detection, localization, and counting with structured outputs | Joint spatial/count medical adaptation is occupied |
| [MIMO](https://openaccess.thecvf.com/content/CVPR2025/html/Chen_MIMO_A_Medical_Vision_Language_Model_with_Visual_Referring_Multimodal_CVPR_2025_paper.html), [VividMed](https://aclanthology.org/2025.naacl-long.89/), and [MedRegA](https://proceedings.iclr.cc/paper_files/paper/2025/file/414fd191b3246a19a55741b938380136-Paper-Conference.pdf) | Unified or broad medical VLM systems with referring, grounding, boxes/masks, VQA, reports, or region-grounded instruction | Grounded multi-task medical integration is occupied |
| [CADRE](https://arxiv.org/abs/2606.23487) | Parameter-efficient medical adaptation with explicit forgetting and prior-drift controls | Preservation and base-relative stability are occupied |
| [Why Does Grounding Hurt Medical VQA?](https://arxiv.org/abs/2604.27720) | In one Qwen2.5-VL/data mix, answer-only SFT destroyed box emission; shuffled-box rehearsal restored format but not localization; limited grounding recovered IoU and retained SLAKE answer gains, while VQA-RAD and stated limitations preclude a universal preservation claim | The broad answer/grounding co-training motivation and formatting-versus-localization distinction are occupied |
| [Small-medical-VLM QLoRA study](https://arxiv.org/abs/2607.27122) and [joint VQA/explanation/grounding LoRA](https://arxiv.org/abs/2511.04384) | Backbone/recipe-matched VQA-only versus multitask comparison (not fixed-record/token/unit-mass matching) and joint medical grounding adaptation | Medical multitask co-training is not the residual novelty claim |
| [Which Model to Transfer?](https://openaccess.thecvf.com/content/CVPR2022/html/Renggli_Which_Model_To_Transfer_Finding_the_Needle_in_the_Growing_Haystack_CVPR_2022_paper.html) and [Quick-Tune](https://openreview.net/forum?id=tqh1zdXIra) | Transfer-model selection and low-budget learning-curve response prediction | Adaptation response as a general selection principle is occupied |

The audited residual system elements are:

1. separately reported and regression-gated answer plus independently source-authoritative context targets;
2. optimizer mass normalized by the underlying independent biomedical unit rather than generated rows/views;
3. base choice made by held-out base-to-adapted response rather than untouched-base performance; and
4. final selection constrained by source-held-out visual-dependence and preservation gates.

Only elements 1 and 2 form the crossed training interaction. Element 3 is the separate frontier claim. Element 4 is a
validity gate. The complete system may still be compared against complete-system baselines for competition value, but
that comparison does not identify a four-way interaction.

Public-firewall governance, exact serialization, disclosure, and deterministic release apply identically to every arm.
They are validity controls and cannot be counted as the differentiating scientific atom.

### Atom-level prior-art boundary

Neither isolated claim is a new objective or a new selection principle. Grouped/view-averaged loss already occupies
unit normalization; multitask supervision occupies answer/context co-training; [CORAL](https://arxiv.org/abs/2607.03647)
occupies counterfactual medical-VLM visual-reliance diagnostics and hard-negative training; and pretrained-model
selection is established by [LEEP](https://proceedings.mlr.press/v119/nguyen20b.html),
[LogME](https://proceedings.mlr.press/v139/you21b.html),
[TransRate](https://proceedings.mlr.press/v162/huang22d.html), and the
[downstream-free-energy checkpoint criterion](https://proceedings.mlr.press/v267/munn25a.html). H1 and H2 therefore
test competition utility and transportable system behavior, not a novel loss, optimizer, or general model-selection
principle. Passing both does not create conjunction novelty by addition.

The normalization boundary is also direct: [Yi et al.](https://arxiv.org/abs/2103.08933) group augmented views by
original sample and reweight within groups; [Wu et al.](https://proceedings.mlr.press/v121/wu20a.html) document unequal
learning dynamics across medical views; and [Vu et al.](https://proceedings.mlr.press/v149/vu21a.html) use
patient/study-aware medical multi-view pairing. These works do not test H1's exact MMBU-shaped interaction, but they
remove a general novelty claim for grouping, medical-view awareness, or per-origin normalization.

For H1, per-example/view normalization and answer/grounding/context multitask training are occupied. The only honest
pre-result residual is empirical: annotation multiplicity may confound the measured benefit of co-training. It survives
only if the `SYS-A0`–`SYS-A3` interaction, exposure-equalization collapse, and duplicate-view invariance all pass on two
independently governed source parents. For H2, the residual is likewise empirical: a frozen adaptation-response rule
may lower out-of-cohort selection regret relative to untouched ranking. It must also beat selection by highest absolute
post-micro-adaptation task/context score, delta-only response, early score/loss, and every feasible LEEP, LogME,
TransRate, SFDA, and free-energy control. Otherwise H2 is ordinary low-budget transfer selection.

## Training factorial

Use the same admitted external-only units, source roles, base, answer prompt/target bytes, evaluation prompts, serializer,
parameter budget, optimizer family, optimizer-step budget, compute envelope, seeds, and checkpoint-opening policy.
Freeze arm-specific context prompt/target bytes prospectively for `A1` and `A3`; `A0` and `A2` have no context training
target but must still be evaluated on the identical task and context endpoints. Use one explicit fixed-total-supervised-
token estimand: context displaces a frozen amount of a repeated-answer-loss schedule in `A1`/`A3`, while `A0`/`A2` retain
that answer allocation. Bind per-arm answer/context token exposure and match total supervised tokens, global summed
objective-loss/optimizer budget, optimizer updates, active FLOPs, and compute. Do not match the per-unit allocation
vector: row/view-uniform `A0`/`A1` assign unit mass in proportion to authorized row/view exposure, while normalized
`A2`/`A3` assign equal mass per independent unit. This estimates context allocation under a fixed budget and the effect
of redistributing that budget across units, not fixed answer exposure plus free context. If the global match is
infeasible, or if an arm does not realize its declared allocation vector, H1 is nonidentified; a post-hoc rule cannot
remove the confound.

| Arm | Answer objective | Authoritative context objective | Independent-unit mass normalization |
|---|---|---|---|
| `SYS-A0` | yes | no | no; row/view-uniform control |
| `SYS-A1` | yes | yes | no; row/view-uniform control |
| `SYS-A2` | yes | no | yes |
| `SYS-A3` | yes | yes | yes |

For each preregistered primary endpoint `E`, compute the interaction

```text
I_E = (E_A3 - E_A2) - (E_A1 - E_A0)
```

The decision object must name task and context primary estimands separately; it may not invent one post-hoc composite.
Promotion requires both frozen interaction conditions plus conjunctive nonregression in positive flips, negative flips,
normal-image competence, answer-changing target tracking, invalid-output rate, and cost. The exact minimum worthwhile
effects, noninferiority margins, independent unit, source-family resampling hierarchy, simultaneous error control,
replicate count, seeds, missing-stratum rule, and pass function must be frozen before any arm produces an output.

### Exposure-equalization mechanism check

Repeat the factorial after equalizing every optimizer-relevant exposure quantity per independent unit within each
context level: `A0` with `A2`, and separately `A1` with `A3`. Equalize authorized views, supervised target tokens,
objective-bearing fields, sampling probability, and update opportunity inside each pair while retaining the same units
and endpoint coverage. Do not equalize away the context factor between the two pairs. The preregistered prediction is
equivalence of `A0` with `A2`, equivalence of `A1` with `A3`, and therefore an interaction compatible with zero inside a
frozen equivalence margin. That collapse supports the interpretation that unit normalization acts through heterogeneous
exposure; it is not a failure of the natural unequal-view factorial. A persistent interaction falsifies that mechanism
or proves the equalization incomplete and must block the exposure-mechanism wording. The competition result may remain
useful, but broader system novelty requires the natural factorial, this mechanism check, and the complete-system
comparators to agree.

As a separate perturbation check, deterministically duplicate a frozen subset of existing authorized views while adding
no independent unit or semantic target. Use the identical duplication schedule in the corresponding normalization and
row-uniform arms, and match steps, total supervised tokens, and compute by a prospectively declared resampling rule.
Unit-normalized estimates should remain within a frozen invariance margin, while any row-uniform movement must match the
preregistered direction only when that direction was independently derived before outputs. Mechanically verify the
row-uniform optimizer-weight perturbation in every case. Failure of normalized-arm invariance blocks the view-multiplicity
mechanism claim; absent or opposite row-uniform endpoint movement weakens the utility hypothesis but is not by itself a
conformance failure.

## Strong complete-system comparators

At minimum include:

- ordinary shared answer-only LoRA;
- a parameter-, active-FLOP-, update-, token-, and compute-matched FLARE-style task-specific LoRA system;
- a matched Two-Stage Mixture-of-LoRA reproduction; and
- MedQwen only if its released implementation, license, module map, and resource envelope permit a faithful match.

An unavailable comparator is `not_implementable_from_available_evidence`; it is not replaced by an easier method under
the published name. Full B2 must beat the strongest faithfully matched complete-system comparator on untouched
source-held-out data. Beating only `SYS-A0` is insufficient.

## Base-frontier isolation

Across one frozen eligible base universe and identical micro-adaptation screen, compare:

- `FRONTIER-U`: select by untouched-base task score; and
- `FRONTIER-R`: select by the preregistered base-to-adapted response frontier.

The frontier claim is eligible only if `FRONTIER-R` selects a different immutable base and wins under the frozen
decision function on a second untouched, group/source-disjoint cohort. The second cohort may be opened once only after
both choices and artifacts are committed. Otherwise the frontier remains sound selection hygiene, not a contribution.

## Replication and separate kill rules

The training interaction must reproduce on confirmatory roles from at least two prospectively declared, independently
governed source parents that are disjoint from every training, tuning, and development role; development evidence does
not count toward this minimum. Each parent contributes its own task and context interaction estimate and decision
receipt. Neither modalities nor subsets split from one parent count as independent replication. Inference remains
conditional on those named parents. A population-of-source-families claim requires a larger prospectively justified
family count with family-level uncertainty. An externally generalizable system claim additionally requires external
replication or a separately governed independent implementation; this strengthens scope and credibility, not novelty by
itself.

H1, the training-interaction claim, is ineligible if any of the following occurs:

1. `SYS-A3` fails either frozen primary interaction condition;
2. the exposure-equalized arms fail the frozen equivalence/null prediction, or any optimizer-relevant exposure remains
   unequal;
3. context co-training causes a material task or preservation regression;
4. the effect is explained by extra records, labels, views, tokens, updates, parameters, compute, filtering, serializer,
   evaluator tailoring, or unequal troubleshooting; or
5. the effect does not replicate across the declared independently governed source parents.

H2, the selection-protocol claim, is independently ineligible if `FRONTIER-R` does not choose a different immutable base
or fails the frozen decision function on the one-opening second untouched cohort. H1 success cannot rescue H2 failure,
and H2 success cannot rescue H1 failure.

A composite-protocol or system-superiority claim additionally requires both H1 and H2 to remain eligible and the full
system to beat the strongest faithfully matched complete-system comparator. If the comparator is noninferior or better,
an isolated H1 result may still be reported as such, but not as complete-system superiority or as evidence for H2.

Failure of any scientific claim does not disqualify B2 as a competition recipe if it is strongest. The reported wording
must name exactly which of H1, H2, or composite-protocol eligibility failed; it may not collapse them into one verdict.

## Honest rating and authorization

| Dimension | Current | Conditional ceiling | Boundary |
|---|---:|---:|---|
| Competition value | 8.4 | evidence-dependent | Current prospective B2 value; not a result |
| Competition-system innovation | 4.2 | 4.5 before results | Subjective design estimate after direct co-training and transfer-selection collisions |
| System novelty | 3.5 | 5.0 after matched interaction evidence; about 5.5 only if independent replication also reveals a prospectively predicted transportable interaction not reducible to ordinary view balancing | Replication alone raises confidence, not conceptual novelty; no current contribution is admitted |
| Learner-method novelty | 2.0 | 2.5 without a different update rule | This design does not raise it |
| Paper novelty | 3.0 | 4.0 after an isolated system result; external replication strengthens credibility but does not automatically raise novelty | No current primary paper claim is admitted |

This document authorizes only schema design and synthetic decision fixtures under the existing handoff controls. It
does not authorize data download, model loading, training, public-set evaluation, confirmation opening, or GPU use. The
only allowed representation is the closed, disabled H1/H2/composite registry and negative-test matrix in
[COMPETITION_MANIFEST_SPEC.md](COMPETITION_MANIFEST_SPEC.md); passing those fixtures is not a scientific freeze or result.
