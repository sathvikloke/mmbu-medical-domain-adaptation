# Research-portfolio novelty audit

**Date:** October 18, 2026  
**Status:** adverse prior-art update; literature screen, not a claim of exhaustive novelty search

## Superseding disposition

The later [source–factor incidence audit](SOURCE_FACTOR_INCIDENCE_AUDIT.md) proved that the current optimistic
source-adjusted grid is rank deficient and aliases the claimed factors with source. The subsequent three-way
[independent arbitration](INDEPENDENT_IDEA_ARBITRATION.md) therefore supersedes the MOSAIC headline scores below:

- MOSAIC on the current grid: **4.5/10 competition value, 5.5/10 concept novelty, 0.5/10 evidence**;
- WRLVT after direct regional inclusion–exclusion counting antecedents: **4.8/10 concept novelty and 4.0/10 paper novelty**;
- MRFSS after the direct CVPR 2022 frequency-counting collision: **5.2/10 concept novelty and 4.5/10 paper novelty**;
- dual-objective B2, the competition flagship: **8.4/10 prospective competition value**; the earlier 9.0 estimate was
  superseded by the October 18 executability audit;
- active integrated project: **4.2/10 subjective pre-result competition-system innovation, 3.5/10 system novelty,
  2.0/10 learner-method novelty, and 3.0/10 pre-result paper novelty**; and
- the second orthogonal search found zero surviving new learner mechanisms in its scoped search. It did not test every
  possible system, data-objective, or evaluation contribution.

The older MOSAIC scores are retained below only as the literature-only judgment made before the identifiability audit.
A future genuinely crossed grid is a new evidence state and must be rescored; it may not inherit 7.2/5.4 by name.

The four novelty axes are not interchangeable. Competition value estimates usefulness; competition-system innovation asks
how unusually the system is tailored to this benchmark; system novelty asks whether the complete integration has a
distinct interaction beyond a checklist bundle; learner-method novelty asks whether the update rule or architecture is
new; paper novelty may include an isolated system, data-objective, or evaluation contribution. The current system is
an unexecuted bundle, not an isolated interaction; system novelty cannot reach 5.0 before matched component ablations.

## Historical pre-identifiability verdict

The original 8.1/10 novelty estimate was too high. A broader search found direct 2026 antecedents that were not in the
first pass. Routed LoRA experts for medical VLMs, biologically supervised factorized medical experts, dynamic LoRA
composition, and element-specific low-rank VLM adaptation already exist. MOSAIC remains a coherent competition
hypothesis, but it is not a revolution merely because its experts have modality/specimen/task names.

At that earlier stage, the revised literature-only scores were:

- competition-concept novelty: **7.2/10**;
- paper-level method novelty: **5.4/10**;
- benchmark/problem fit: **9.4/10**;
- overall research idea before experiments: **7.8/10**.

These numbers are now superseded. They never were model evidence and may not be used as the current score.

## Direct antecedents

| Prior work | What it already establishes | What it removes from our novelty claim |
|---|---|---|
| [Sparse Spectral LoRA / MedQwen, CVPR 2026](https://arxiv.org/abs/2604.01310) | Routed low-rank experts for medical VLMs across heterogeneous medical VQA, reporting, classification, and hallucination tasks, with explicit forgetting analysis | “Routed medical LoRA experts solve cross-dataset interference” is not new; this is now a mandatory strong baseline |
| [BioFact-MoE, 2026](https://arxiv.org/abs/2605.26376) | Biologically supervised factor-specific LoRA pathways and residual gating in a medical vision-language system | “Biomedical factors give experts meaningful specialization” is not new |
| [LoRA-Mixer, ICLR 2026](https://arxiv.org/abs/2507.00029) | Input-aware dynamic routing and composition of task LoRA experts inside attention projections | Dynamic LoRA routing/composition is not new |
| [Med-MAT, ACL 2025](https://aclanthology.org/2025.acl-long.639/) | Modality–anatomy–task decomposition and held-out compositional generalization across classification and detection | MAT factorization and unseen-combination evaluation are not new |
| [CrossMed, 2025](https://arxiv.org/abs/2511.11034) | MAT-structured cross-task medical VLM benchmarking with related, unrelated, and zero-overlap settings | A held-out MAT benchmark protocol is not new |
| [CCFT, 2026](https://arxiv.org/abs/2607.10797) | A Qwen2.5-VL method using semantic-element-specific low-rank adapters and compositional VQA supervision | Factor-specific low-rank VLM adaptation is not new outside medicine |
| [Two-Stage Mixture-of-LoRA, 2026](https://arxiv.org/abs/2609.14350) | Medical task routing with LoRA experts | A medical task router is not new |
| [CADRE, 2026](https://arxiv.org/abs/2606.23487) | Parameter-efficient medical VLM adaptation with bounded forgetting and prior drift | Base preservation/anchor regularization is not new |
| [Multimodal Medical Image Parsing with Task-Specific Low-Rank Adapters, 2026](https://arxiv.org/abs/2610.19901) | A frozen Qwen3.5-9B backbone with question-selected task-specific LoRA, task-dependent ranks/prompts/image budgets, six task families, seven modalities, hidden-organizer validation, and a reproducible container | Task-conditioned medical LoRA selection and task-specific adapter configuration are not new; B2's simpler shared-adapter route remains a competition-risk choice, not a novelty claim |
| [Every Sample Counts, 2026](https://arxiv.org/abs/2607.08968) | Per-sample constrained fine-tuning with learned sample-dependent relaxation and augmented-Lagrangian optimization | Per-example preservation constraints and learned relaxation are not unclaimed novelty space |
| [Beyond Average Safety, 2026](https://arxiv.org/abs/2609.29960) | Reference-relative chance constraints and tail-aware correction for fine-tuning regressions | Tail-aware reference-model preservation is already an explicit constrained-optimization mechanism |
| [DynaMiCS, 2026](https://arxiv.org/abs/2605.10770) | Dynamic data-mixture optimization from local cross-domain effect estimates under preservation constraints | Adaptive domain mixing under performance constraints is not a new learner claim |
| [Why Does Grounding Hurt Medical VQA?, 2026](https://arxiv.org/abs/2604.27720) | Directly separates answer-only degradation, shuffled-box format rehearsal, real grounding recovery, and oracle-crop failure | Broad answer/grounding co-training and formatting preservation are occupied |
| [Small-medical-VLM QLoRA comparison, 2026](https://arxiv.org/abs/2607.27122) and [joint VQA/explanation/grounding LoRA, 2025](https://arxiv.org/abs/2511.04384) | Matched VQA-only/multitask adaptation and joint grounded medical training | B2 is competition engineering, not a new multitask learner |
| [Which Model to Transfer?, CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Renggli_Which_Model_To_Transfer_Finding_the_Needle_in_the_Growing_Haystack_CVPR_2022_paper.html) and [Quick-Tune, ICLR 2024](https://openreview.net/forum?id=tqh1zdXIra) | Transfer-model choice and cheap adaptation-response prediction | H2 cannot claim the general principle of selection by micro-adaptation |

## Closest complete-system boundary

The system and paper axes require a different comparison from the learner-method search. These complete or broad
medical systems already combine several ingredients that B2 cannot claim individually:

| Complete-system antecedent | System-level scope already demonstrated | Boundary for B2 |
|---|---|---|
| [Multimodal Medical Image Parsing with Task-Specific Low-Rank Adapters, 2026](https://arxiv.org/abs/2610.19901) | Benchmark-specific Qwen adaptation with task-selected LoRA, task-dependent ranks/prompts/image budgets, class rebalancing, hidden-organizer validation, deterministic container checks, and runtime/artifact reporting | Benchmark-tailored medical adaptation and reproducible competition packaging are not new system claims |
| [Point, Detect, Count, 2025](https://arxiv.org/abs/2505.16647) | Qwen2.5-VL LoRA jointly instruction-tuned for medical detection, localization, and counting with structured outputs | Joint prompt-driven medical task adaptation and spatial/count outputs are not new |
| [MIMO, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Chen_MIMO_A_Medical_Vision_Language_Model_with_Visual_Referring_Multimodal_CVPR_2025_paper.html) | Unified visual referring input, pixel-grounded output, medical question answering, and multi-task evaluation | A unified grounded medical VLM is not new |
| [VividMed, NAACL 2025](https://aclanthology.org/2025.naacl-long.89/) | One medical VLM spanning 2D/3D data, segmentation masks, instance boxes, VQA, report generation, and an open-data synthesis pipeline | Versatile grounding plus ordinary medical tasks is not new system integration |
| [MedRegA, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/414fd191b3246a19a55741b938380136-Paper-Conference.pdf) | Region-grounded medical instruction tuning and grounded organ-level report generation | Region-grounded instruction and evidence-linked medical generation are not new |

B2's remaining possible system claim is a composite protocol with two separately isolated hypotheses: an
answer/context × unit-normalized-exposure interaction and an adaptation-response versus untouched-base selection
contrast. Source-held-out visual controls and preservation are common validity gates, not additional randomized factors.
That is currently a hypothesis, not an admitted contribution. Organizer-defined scoring and serialization, firewall
governance, and a long checklist do not by themselves establish innovation. The full-system/component ablation and
prospective decision objects in the scorecard are mandatory before system novelty can reach 5.0. The exact conditional
claims, factorial, exposure-mechanism checks, complete-system comparators, frontier-isolation test, replication rule, and
kill gate are frozen in the [system-interaction hypothesis](SYSTEM_INTERACTION_HYPOTHESIS.md). Passing both hypotheses
does not create conjunction novelty by addition.

## Non-learner search disposition

The October 18 search separately tested system, data-objective, and evaluation contribution classes:

| Claim class | Disposition | Strongest boundary | Honest pre-result score |
|---|---|---|---:|
| Competition system | Two separately isolated conditional hypotheses; no admitted contribution | FLARE task-specific LoRA, Two-Stage Mixture-of-LoRA, MedQwen, Point-Detect-Count, MIMO, VividMed, MedRegA, CADRE, direct answer/grounding co-training, and established transferability/model-selection methods occupy the components | 3.5 system novelty |
| Data objective | Zero standalone survivors | Split-before-expansion, grouped/view-averaged loss, partial-label masking, derived multi-task views, CocoCon, CORAL, and MedGround reduce the conjunction to careful grouped multitask ERM | 4.0 concept ceiling; 3.0 standalone paper/objective novelty |
| Evaluation contribution | Zero standalone survivors | MultiMedEval, MEGA-Bench, VHELM, SURE-VQA, CORAL, SI-VQA, positive-congruent updates, and structured-output benchmarks occupy the dashboard components | 3.5 concept; 3.0 paper novelty |

The data construction remains defensible as “leakage-safe, provenance-aware unit-normalized supervision,” and the
evaluation remains defensible as “a preregistered, source-macro, same-unit medical-VLM dashboard combining established
diagnostics.” Neither wording claims a new objective, estimand, or evaluator.

## Adverse search for a replacement mechanism

An October 17 follow-up specifically searched for a higher-novelty replacement based on visual grounding, causal
debiasing, structured supervision, and low-data medical PEFT. It found a crowded field rather than an unclaimed easy
mechanism:

- [CORAL](https://arxiv.org/abs/2607.03647) already combines counterfactual medical-VLM grounding diagnostics with
  hard-negative contrastive LoRA training;
- [DE-CaGI](https://doi.org/10.1016/j.media.2026.104226) already performs causal gradient intervention for evidence-
  grounded medical VQA;
- [CIMB-MVQA](https://doi.org/10.1016/j.media.2025.103850) already intervenes on modality-specific visual and language
  confounders;
- [ConceptVLM](https://doi.org/10.1038/s41746-026-02676-5) already uses concept-aware, data-efficient medical-VLM LoRA
  with general-capability preservation; and
- [MPA-VQA](https://doi.org/10.1016/j.engappai.2025.112866) already combines mask-prompt alignment, contrastive learning,
  and multitask object grounding.

These works do not prove that every possible replacement is exhausted. They do falsify the shortcut argument that
adding counterfactual images, a causal loss, concept weighting, or segmentation alignment would by itself create a
9/10-novel project. Those ingredients remain valid baselines or controls, not a flagship claim.

## What still differs

The exact combination not yet found in this screen is:

1. one generative VLM with separately supervised modality, specimen/scale, and task-geometry residual bases;
2. one-pass composition from pre-adapter visual/question summaries;
3. direct coordinate generation coupled to a reusable task-geometry factor;
4. a source-confounding rejection test plus held-out source and held-out joint-combination gates; and
5. simultaneous total-parameter- and active-FLOP-matched controls.

That is a useful experimental package. It is an integration-level distinction until results show a new mechanism. Do
not use “first,” “novel routed LoRA,” “novel biological experts,” or “novel MAT decomposition.”

## Competition decision

MOSAIC is no longer entitled to be the only advanced branch. Add Sparse Spectral LoRA as B4 after its implementation,
license, packaging, and resource requirements are independently verified. Compare on the same admitted records and
prospective splits. If B4 beats MOSAIC or is indistinguishable at lower complexity, use B4 or the strongest simpler
baseline for the competition and report MOSAIC as a negative result.

The competition objective is performance under the rules, not ownership of an acronym. A published strong method is a
better submission choice than an original weak method.

## Novelty-improvement gate

The historical pre-adverse-review ceiling at this stage was 7.3/10; it is obsolete. Before claiming method novelty
above the current active-project ceiling of 2.5/10, a successor design must:

- name a mechanism absent from every antecedent above;
- state which causal or statistical failure that mechanism corrects;
- include an ablation that isolates it from routing, more parameters, more compute, data mixture, and formatting;
- include Sparse Spectral LoRA, shared LoRA, and the strongest applicable factorized/routed control;
- survive source-balanced and held-out-combination scoring; and
- be described without “first” language unless a reproducible systematic search supports it.

Until then, MOSAIC remains frozen on the current grid and is not the final answer by declaration.

## Factorial-update successor search — adverse disposition

A later successor search tested whether factorial/Möbius decomposition of a crossed medical-adaptation grid could
replace MOSAIC. It cannot. Task Arithmetic already evaluates three-corner analogy completion; LoRA Soups, task-vector
bases, compositional-merging evaluations, and direct functional non-additivity studies cover the core operation.
Möbius notation makes main and interaction effects explicit but does not create a new learner.

The retained value is a source-balanced interaction audit: use effective `B @ A` updates, replicate seeds, hold out
whole cells, and ask whether a frozen interaction statistic predicts functional composition error beyond update norm
and ordinary task-vector similarity. This becomes a falsification gate for MOSAIC, not a new flagship. Scores are
competition idea **5.2**, concept novelty **5.8**, and paper-level method novelty **4.3**. The complete evidence and
kill test are in [FACTORIAL_UPDATE_ADVERSE_REVIEW.md](FACTORIAL_UPDATE_ADVERSE_REVIEW.md).

## QUILT adverse update — superseded disposition

The successor search produced [QUILT](../superpowers/specs/2026-10-17-quilt-design.md): estimate a candidate
prompt-interface nuisance subspace from source-balanced template centroids after within-unit centering over complete
presentation-equivalent prompt panels for the same verified source fact, then remove that component from a fixed-basis
LoRA update. It retains ordinary LoRA packaging and does not add an inference router. Source-by-template deviations and
unit-by-template residuals are falsification diagnostics rather than extra rows silently added to the primary basis.

The broader search also found strong adjacent work: PCGrad and CAGrad for conflicting gradients, CocoCon and SOrT for
cross-task/VQA consistency, SubPT for gradient-subspace prompt tuning, DOME for covariance-derived nuisance filtering,
[GERNE](https://openaccess.thecvf.com/content/ICCV2025/html/Asaad_Gradient_Extrapolation_for_Debiased_Representation_Learning_ICCV_2025_paper.html)
for gradient-difference debiasing, iGSP for projected VLM adaptation, and GRAM for projected LoRA in medical VQA.
[ProGrad](https://openaccess.thecvf.com/content/ICCV2023/html/Zhu_Prompt-aligned_Gradient_for_Prompt_Tuning_ICCV_2023_paper.html)
already regulates prompt updates using alignment with a general-knowledge gradient;
[Gradient-Regulated Meta-Prompt Learning](https://openaccess.thecvf.com/content/ICCV2023/html/Li_Gradient-Regulated_Meta-Prompt_Learning_for_Generalizable_Vision-Language_Models_ICCV_2023_paper.html)
learns a gradient regulator for cross-domain prompt generalization;
[Latent Adversarial Paraphrasing](https://aclanthology.org/2025.emnlp-main.1595/) directly trains robustness to
semantically preserving prompt variants; and
[Understanding the Prompt Sensitivity](https://aclanthology.org/2026.acl-long.2053/) gives a first-order gradient-based
analysis of meaning-preserving prompt sensitivity. These prevent claims that gradient projection, gradient consistency,
gradient-difference nuisance directions, prompt-gradient regulation, paraphrase robustness, nuisance filtering, or
medical subspace-constrained LoRA is new.
[Recover-to-Forget](https://openreview.net/forum?id=n7peBaPUmk) computes LoRA gradients for multiple paraphrases of the
same target fact and averages them before reconstructing a full unlearning gradient. This removes any claim that
same-fact multi-view paraphrase LoRA gradients or their aggregation are new; QUILT's remaining distinction must come
from source-balanced centering, nuisance-subspace identification, interaction rejection, and projected training.
[A Categorical Atlas of Parameter-Efficient Fine-Tuning](https://arxiv.org/abs/2610.12728) additionally formalizes
PEFT gauge fibres, expressivity obstructions, composition, and optimizer-dependent LoRA symmetry, including Adam's
restricted gauge invariance. QUILT's fixed-basis and optimizer-rotation analysis is therefore a correctness obligation,
not a novelty contribution.

What may still differ is the complete identification design:

1. same independent medical fact, image, grounding carrier, and semantic target;
2. a controlled change only in prompt presentation, with identical serialized targets;
3. module-local, source-balanced template-centroid SVD under deterministic execution, with source/unit interaction
   rejection;
4. a frozen quotient applied only in a fixed LoRA coordinate system;
5. random-rank, random-energy, scalar-shrinkage, shuffled-panel, PCGrad, CAGrad, and output-consistency controls; and
6. an R2F-style equal mean-gradient control plus leave-one-presentation-interface-out transfer with ordinary
   offline-loadable LoRA output.

The distinguishing prediction is prospective: a basis estimated from `basis_templates` must capture centered
gradients from a lineage-disjoint `audit_templates` family on disjoint units, without absorbing mean fact-gradient
energy, and then predict improvement on a separately untouched `validation_templates` family. Failure at the audit family
stops QUILT; success is still only mechanism eligibility, not performance evidence.

The later independent adverse review and additional primary-literature search supersede the earlier ratings below.
The missed evidence includes LoRA-FA, GPM/InfLoRA, AND-mask/Fish/Fishr, INLP, and direct 2026 medical-VLM
paraphrase-consistency training plus its image-reliance failure analysis. See
[QUILT_ADVERSE_REVIEW.md](QUILT_ADVERSE_REVIEW.md) for the binding disposition.

Obsolete historical QUILT ratings from the earlier pass:

- competition-concept novelty: ~~7.3/10~~, now **3.5/10**;
- paper-level method novelty: ~~6.1/10~~, now **3.0/10**;
- competition idea: ~~7.8/10~~, now **4.0/10**.

QUILT is no longer the current highest-novelty portfolio candidate. It is retained as a diagnostic/negative-result
branch because its controls can still answer a useful scientific question. It cannot regain flagship status merely by
passing algebraic synthetic fixtures; it would need image-reliant held-out-template benefit beyond direct supervised
consistency, mean-gradient, and GPM/InfLoRA-style controls.
