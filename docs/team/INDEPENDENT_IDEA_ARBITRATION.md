# Independent idea arbitration

**Arbitrated:** October 17, 2026  
**Evidence class:** design and literature review only; no model or biomedical result  
**Decision:** one competition flagship, no automatic novelty build, no novelty inflation

## Why this exists

Three independent reviews were commissioned with different incentives: maximize the official score, invent a genuinely
different mechanism, and try to reject the entire portfolio. They were not asked to agree. This document records the
conflicts and makes one binding decision before implementation or GPU use.

The challenge score is prospectively documented as
`S = (0.8T + 0.2C)(T - T_base)`. This makes answer-task improvement central, but it does not make biomedical-context
recognition optional. Novelty and architectural complexity have no documented score bonus.

Differentiating that score yields a state-dependent weighted sum of the ordinary task and context gradients; it does
not create a third update direction or a novel objective family. Direct minibatch-product training is rejected because
its context coefficient is negative while estimated task gain is below the base, and because batch covariance can
distort the metric surrogate. The score belongs in prospectively frozen selection after a positive task-gain floor,
not in a novelty claim.

## Review outcomes

| Review | Strongest recommendation | Competition value | Concept novelty | Evidence | Binding interpretation |
|---|---|---:|---:|---:|---|
| Score-maximizing review | Broad visual SFT, base-correct retention, and fixed weight interpolation | 8.6 | 3.0 | 7.2 from external literature, 0 locally | Retain the simple recipe; audit every extra mechanism against equal-budget B2 |
| Hostile review | Shared PEFT with co-primary answer and context objectives, unit-normalized exposure, exact serialization, and visual pairs | **9.0** | 3.5 | 0.5 | This replaces “B2 plus curriculum” as the flagship |
| Novel-mechanism search, corrected | Marked Random-Frequency Set Sketching (MRFSS), training-only auxiliary | 6.8 | **5.2** | 0.5 | Demoted after a direct frequency-domain counting collision; no automatic implementation |
| Remaining novelty hypothesis, corrected | Withheld Region-Lattice Valuation Training (WRLVT) | 6.5 | **4.8** | 0.5 | Demoted after direct region-additivity/inclusion–exclusion counting antecedents; hold |
| Hostile review of MOSAIC | Current source-adjusted grid is non-identifiable | 4.5 current | 5.5 current | 0.5 | Freeze biomedical training; a crossed grid may be reconsidered from zero evidence |

## Binding flagship: B2 dual-objective answer-and-context adaptation

The primary candidate is one base-architecture-preserving shared adapter, pending official loader/package
confirmation, trained on admitted external records with:

1. co-primary answer-task and authoritative biomedical-context targets;
2. explicit masks for unknown context fields—no label may be inferred from dataset name, prompt wording, or file path;
3. total optimizer mass normalized per independent unit before balancing source/task/context strata;
4. geometry-derived views only when the source annotation authorizes the derivation;
5. exact output serialization plus lineage-disjoint prompt families;
6. answer-changing visual pairs and answer-preserving interventions where source authority supports them;
7. held-out source families and group-level uncertainty; and
8. conservative base-retention and weight interpolation only as separately gated post-B2 ablations.

Curriculum order is not the idea. Static, forward, reverse, and shuffled schedules must receive the same units, views,
tokens, optimizer steps, and per-unit loss mass. If forward ordering does not beat static and shuffled controls under a
prospective margin, delete the curriculum claim and keep only the useful multi-view supervision.

### Flagship falsification gates

On a prospectively frozen 0–100 proxy scale, reject an intervention unless all applicable conditions hold:

- the paired source-group bootstrap 95% lower bound is above zero and the point improvement is at least 1.5 points on
  the organizer-compatible composite proxy;
- task and context components each improve by at least 0.5 points as a conservative team safety policy, not as a
  consequence of the official formula, which uses adapted absolute context performance rather than context gain;
- no task or context field drops by more than 1.0 point;
- malformed committed output stays below 0.5% and does not worsen;
- authoritative answer-changing target tracking improves by at least 2.0 points with a positive 95% lower bound;
- the result survives one held-out source family and lineage-disjoint prompt templates; and
- independently obtained contributing-source training splits follow the October 14 organizer ruling: they are allowed
  with full dataset disclosure, but exact version/split/lineage, known-public exclusion, duplicate checks, source-family
  grouping, rights, and generalization slices remain mandatory because no hidden-overlap service exists.

These numerical gates are prospective defaults, not observed results and not claims about the unreleased official
evaluator. If the executable metric scale differs, convert them before any result is opened and record the conversion.

## Demoted mechanism: MRFSS

For a complete class-marked instance set, define

`s(c,R,w) = sum_j 1[c_j=c, p_j in R] exp(i w^T p_j)`.

At zero frequency this is the exact count; low frequencies encode coarse location and multiplicity; additional
frequencies distinguish configurations sharing a count and centroid. A small training-only head predicts randomly
sampled real/imaginary sketch components from the answer-boundary hidden state. The head is removed before export, so
the submission remains one ordinary VLM with one native generation call.

The original safe-claim attempt was the exact use of randomly queried characteristic samples of a marked instance
measure as an auxiliary target for a generative VLM. A later exact search found a direct collision:
[Crowd Counting in the Frequency Domain, CVPR 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Shu_Crowd_Counting_in_the_Frequency_Domain_CVPR_2022_paper.html)
already transforms point-density supervision into the frequency domain, uses characteristic-function properties to
capture count and position, and derives subregion counting information. Class marks, random queries, and attaching the
loss to a VLM answer state are integration differences, not a new central principle.

Other close boundaries include [Point-Query Quadtree](https://arxiv.org/abs/2308.13814),
[point-based counting/localization](https://openaccess.thecvf.com/content/ICCV2021/html/Song_Rethinking_Counting_and_Localization_in_Crowds_A_Purely_Point-Based_Framework_ICCV_2021_paper.html),
[EFDTR](https://proceedings.mlr.press/v267/cao25c.html),
[Neural Point Processes](https://proceedings.mlr.press/v258/shi25a.html),
[CF-GO-Net](https://arxiv.org/abs/2409.12610), and
[Fourier-VLM](https://arxiv.org/abs/2508.06038).

### Optional diagnostic only

Use 3,000–5,000 generated object scenes with complete instance truth. Equal-compute arms are ordinary multitask SFT,
count-plus-centroid moments, exact point-list auxiliary, random unrelated scalar auxiliary, and MRFSS. Hold out higher
counts, new textures, shifted phases, new region shapes, and unseen class/layout combinations.

Kill MRFSS if it fails to beat both ordinary SFT and the equal-information point-list arm across classification,
region recognition, localization, and count, or if its sketches cannot distinguish same-count/different-layout pairs.
Even a pass would establish an ablation result, not a high-novelty paper mechanism. Do not spend this budget before a
real shared-adapter baseline shows a spatial/counting failure that the direct controls do not solve.

## Demoted mechanism: WRLVT

WRLVT proposed additive/monotone laws over nested/disjoint regions, restriction consistency for localized instances,
one prospectively withheld task vertex, and a matched null incidence law. The later exact search found that
[Divide and Count](https://jvgemert.github.io/pub/stahlTIP18counting.pdf) already uses inclusion–exclusion over image
regions and enforces that regional object counts aggregate to the global count. Local-consistency counting and
[spatial divide-and-conquer counting](https://arxiv.org/abs/1908.06473) further occupy regional composition. The
withheld endpoint and null-law comparison remain good falsification design, but they no longer support a distinct core
method claim. Region/cycle grounding antecedents listed in the idea ledger narrow it further.

WRLVT is therefore **4.8/10 concept novelty, 4.0/10 paper novelty, 6.5/10 competition fit, 5.4/10 feasibility, and
0.5/10 local evidence**. It is not authorized for implementation.

## Rejected interpretations

- “Novel curriculum,” “first routed medical LoRA,” and “disentangled/causal factors” are deleted.
- Trainable-parameter efficiency is not inference efficiency without FLOPs, latency, memory, and artifact receipts.
- KL preserves behavior, including errors; it is not correctness preservation.
- Derived views are not independent examples and may not receive extra total loss mass merely because more views exist.
- A router that can read modality/task words from the prompt is not evidence of visual factorization.
- Current MOSAIC scores may not borrow credibility from a hypothetical crossed-source design.
- Unit-normalized exposure is confounding control and estimand discipline, not score-derived optimization novelty.

## Second-pass orthogonal learner-mechanism search: zero survivors

After the MRFSS and WRLVT collisions, an independent second pass excluded routing, Fourier/density/point-process
supervision, regional additivity, ordinary consistency, base preservation, attention alignment, multi-encoder fusion,
RL, and test-time adaptation. It searched for mechanisms broad enough to affect both task and context scores while
remaining one-pass and native-loadable. None survived:

| Attempt | Fatal collision | Concept / paper / fit / feasibility |
|---|---|---:|
| Latent medical scene-language compiler | Open-vocabulary scene graphs, Scene Language, MedCLM, region-grounded medical instruction tuning, and executable-program inference already occupy the mechanism | 3 / 3 / 7 / 7 |
| Acquisition-provenance factorization | BIOMEDICA, UniMed-CLIP, MCPL, MeDSLIP, Anatomy-VLM, and ordinary provenance auxiliary classification occupy the useful part; it does not inherently repair counting/localization | 4 / 3 / 5 / 6 |
| Redundant semantic codewords | Classical error-correcting output codes plus grounded/spatial tokens and unified task tokens occupy the idea; repair/majority decoding risks an extra inference component | 3 / 2 / 6 / 8 |

Representative primary boundaries: [From Pixels to Graphs, CVPR 2024](https://openaccess.thecvf.com/content/CVPR2024/papers/Li_From_Pixels_to_Graphs_Open-Vocabulary_Scene_Graph_Generation_with_Vision-Language_CVPR_2024_paper.pdf),
[BIOMEDICA, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/papers/Lozano_BIOMEDICA_An_Open_Biomedical_Image-Caption_Archive_Dataset_and_Vision-Language_Models_CVPR_2025_paper.pdf),
[MedRegA, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/414fd191b3246a19a55741b938380136-Paper-Conference.pdf),
and [Anatomy-VLM, WACV 2026](https://openaccess.thecvf.com/content/WACV2026/papers/Gu_Anatomy-VLM_A_Fine-grained_Vision-Language_Model_for_Medical_Interpretation_WACV_2026_paper.pdf).

This closes the scoped pre-evidence learner-mechanism search. Reopening costly mechanism work requires either a
prospectively frozen repeated B2/B4 residual on admitted, non-public external data, or a precisely cited independently replicated
residual matching the intended task, modality, and constraints with a predeclared reason B2 cannot address it. The
residual must identify a mechanism-sized bottleneck; otherwise another mechanism search is likely to rename an
established family. This result does not close low-cost system, data-objective, or evaluation-contribution searches,
which were excluded by the mechanism admission rule.

## Final disposition

The hostile review's initial 9.0 competition score is superseded by the October 18 executability audit. The best current
competition idea has **8.4/10 prospective competition value and 0.5/10 local evidence**. Those are not novelty scores.
For the integrated B2 project, the current pre-result axes are **5.8/10 competition-system innovation, 3.8/10 system
novelty, 2.3/10 learner-method novelty, and 3.2/10 paper novelty**. The first is a subjective pre-result estimate, not
admitted novelty evidence. System novelty cannot reach 5.0 until matched component ablations isolate an interaction
rather than more supervision, filtering, updates, compute, or evaluator tailoring.

The strongest rejected residual mechanism is MRFSS at **5.2/10 concept novelty and 4.5/10 prospective paper novelty**;
WRLVT falls to **4.8/4.0**. The factorial interaction audit remains 5.8 concept novelty as a diagnostic, not a learner or
submission method. There is no surviving new learner mechanism and no honest path to 9/10 method novelty before
empirical evidence reveals a new bottleneck. The scoped search does not prove that system, data-objective, or evaluation
contributions are exhausted.

This is not a reason to invent more machinery. Execute the score-aligned flagship first. A train-time novelty probe
becomes eligible only after a qualifying residual under the rule above identifies a mechanism-sized problem and a
fresh collision search supports the exact proposed repair. Low-cost system/data/evaluation audit may continue, but it
cannot delay Lane 1 or consume protected evidence.
