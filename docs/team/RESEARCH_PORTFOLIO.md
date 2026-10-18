# MMBU Track 2 research portfolio

**Date:** October 18, 2026  
**Decision:** protect one competition lane and gate two higher-risk novelty lanes independently

## Why the plan changed

The expanded prior-art audit found that routed medical LoRA experts already have a strong CVPR 2026 reference,
Sparse Spectral LoRA/MedQwen. A competition plan that ignores it is weaker; a novelty claim that quietly reproduces it
is dishonest. The project therefore uses one admitted dataset/protocol and compares increasingly risky methods rather
than committing the entire schedule to one acronym.

## Lane 1: strongest reliable entrant

Purpose: maximize the chance of a valid, loadable improvement over the frozen base. The binding idea is dual-objective
answer-and-context adaptation; curriculum ordering is only an ablation.

The binding execution specification is [the competition-first recipe](COMPETITION_FIRST_RECIPE.md). Research branches
cannot delay this lane or weaken its optimizer, packaging, visual-dependence, or preservation controls.

Before B0 is fixed, use the [base-selection adaptation frontier](BASE_SELECTION_FRONTIER.md) and its binding
[red-team](BASE_SELECTION_REDTEAM.md). Untouched base strength alone cannot select the entrant because the challenge
score depends on adapted performance and base-relative gain. This screen is competition strategy, not a novelty claim.

1. B0: untouched pinned base under the exact same prompt, image, decoding, runtime, and judge contract.
2. B1: language-only shared LoRA for formatting and biomedical vocabulary.
3. B2-P/B2-F: shared projector plus late-language LoRA with parameter- and active-FLOP-matched profiles.
4. B4: Sparse Spectral LoRA/MedQwen reproduction on the same admitted records, only if its official method can be
   independently implemented and packaged under the challenge loader.

Training data should exploit source annotations across the task forms MMBU actually measures: ungrounded
classification, box/mask-grounded classification, and coordinate localization, plus authoritative values for the
versioned requested fields in the [context objective contract](CONTEXT_OBJECTIVE_CONTRACT.md). Deterministic conversions
may create multiple supervision views from one admitted annotation, but all views share the same independent-unit ID,
may not inflate sample independence, and receive no extra total loss mass from annotation density. Open/closed wording is a secondary paper-motivated robustness condition because the
visible current card withholds the separate `options` field from model input. Answer serialization, image-absent
diagnostics, and base-preservation losses are supporting techniques, not novelty claims.

Promote the simplest method whose lower paired group-bootstrap bound exceeds the frozen practical margin, survives the
held-out source, introduces no material classification/context regression, fresh-loads without a network, and meets
runtime/packaging limits. If B2 wins, submit B2. Complexity has no bonus in the challenge score.

## Lane 2: MOSAIC research branch

Purpose: test whether semantically factorized residual bases improve unseen-combination transfer beyond strong routed
and shared controls.

MOSAIC may start biomedical training only after G-1 in [the data-identifiability gate](MOSAIC_DATA_GATE.md) passes. The
[source–factor incidence audit](SOURCE_FACTOR_INCIDENCE_AUDIT.md) now records a provisional portfolio-structure fail:
even an optimistic scaffold aliases modality with specimen and remains rank deficient after source controls. It
must beat the stronger B2 control and B4 on held-out combinations and source-balanced scoring. It must also beat uniform
routing and shuffled-factor negative controls, and its route logits must not encode residual source identity beyond the
within-factor permutation envelope.

If those conditions fail, MOSAIC becomes a retained negative result and Lane 1 continues. No public MMBU output may be
used to rescue it.

## Lane 3: QUILT diagnostic branch

Purpose: test, primarily as a possible negative result, whether strictly controlled prompt-presentation changes can
identify a removable nuisance at training time without introducing a custom inference architecture. It is no longer a
flagship competition idea after the [independent adverse review](QUILT_ADVERSE_REVIEW.md).

[QUILT](../superpowers/specs/2026-10-17-quilt-design.md) estimates a fixed-basis LoRA gradient subspace from
source-balanced template centroids over complete, within-unit-centered strict prompt panels with identical image,
grounding, semantic answer, and target tokens; freezes that basis; and removes its component from later biomedical updates. Source- and unit-level template interactions are falsification diagnostics, not primary covariance rows. The final transformed optimizer step—not merely the raw
gradient—must remain in the allowed complement. QUILT is allowed past design review only after semantic-equivalence,
low-dimensionality, intervention-specificity, optimizer-geometry, and synthetic-identifiability gates pass. PCGrad,
CAGrad, ordinary output consistency, R2F-style equal mean-gradient aggregation, budget-matched paraphrase-robustness
training, random projection, shuffled pairing, B2, and B4 are required controls.

QUILT is intended to preserve the base architecture but lacks organizer loader evidence; it is a diagnostic candidate,
not the higher-novelty centerpiece. It does not replace Lane 1 and does
not make MOSAIC more novel. If the real complete-panel basis fails to beat supervised consistency, mean-gradient,
GPM/InfLoRA-style projection, shuffled/random controls, or visual-dependence gates, the claimed mechanism is rejected.

## Candidate portfolio ratings

These are prospective judgments, not measured performance.

| Candidate | Competition fit | Implementation feasibility | Compliance/package risk | Method novelty | Current evidence |
|---|---:|---:|---:|---:|---:|
| B2 dual-objective answer/context PEFT | **8.4** | 8.6 | 9.3 | 2.3 | 0.5 |
| Conditional B2 composite protocol (separate H1 `SYS-A0`–`SYS-A3` and H2 frontier isolation) | 8.4 | 6.8 | 9.0 | 3.8 system / 2.3 learner | 0.5 |
| B4 Sparse Spectral LoRA reproduction | 9.2 | 5.8 | 6.5 | 1.0 for us | 2.5 from the paper, 0 locally |
| MOSAIC v1.1 on current rank-deficient grid | 4.5 | 6.3 | 6.8 | 5.5 | 0.5 |
| Annotation-view/task-consistency training on B2/B4 | 8.5 | 8.4 | 9.0 | 3.0 | 0.5 |
| MRFSS frequency-set auxiliary, demoted | 6.8 | 6.4 | 9.0 | 5.2 | 0.5 |
| WRLVT withheld region-lattice hypothesis, demoted | 6.5 | 5.4 | 8.5 | 4.8 | 0.5 |
| QUILT interface-gradient quotient | 4.0 | 6.8 | 9.2 | 3.5 | 0.5 |
| Factorial-update decomposition diagnostic | 5.2 | 5.0 | 9.0 | 5.8 | 0.5 |
| Frozen dual-vision-encoder ablation | 7.4 upside / 5.6 readiness | 4.8 | 4.5 | 2.6 | 0.5 |
| Base-conditional preservation ablation | 8.4 upside / 6.0 readiness | 7.8 | 9.2 | 2.5 | 0.5 |

The annotation-view/task-consistency row is a training/data strategy, not a new architecture or core curriculum claim.
Cross-task consistency and grounded multi-task training already exist. Its value is close alignment with the current
card's ungrounded, region-grounded, localization, and counting routes; the paper's closed-to-open gap motivates a
separately labeled robustness condition rather than an official-input claim. Static, forward, reverse, and shuffled
schedules require identical exposure. The [independent arbitration](INDEPENDENT_IDEA_ARBITRATION.md) records the direct
frequency-domain counting collision that demotes MRFSS and the region inclusion–exclusion collision that demotes
WRLVT. Neither may delay Lane 1 or claim method novelty. QUILT remains diagnostic.

The conditional [system-interaction hypothesis](SYSTEM_INTERACTION_HYPOTHESIS.md) is not a fourth lane and does not
raise the current novelty score. It prospectively separates (a) whether authoritative answer/context co-training
interacts with independent-unit mass normalization from (b) whether adaptation-response base selection beats
untouched-base selection on a second untouched cohort. `SYS-A0`–`SYS-A3`, an exposure-equalization null/equivalence
check, the strongest faithfully matched complete-system comparator, replication across independently governed source
parents, and the frozen kill rule are mandatory. Until those results exist, this remains a 3.8/10 system hypothesis and
established shared PEFT remains the learner.

The factorial-update candidate is also not a fourth competition lane. Its
[adverse review](FACTORIAL_UPDATE_ADVERSE_REVIEW.md) found that missing-cell prediction is substantially task-vector
analogy with structured contrasts. Retain only its gauge-safe interaction audit and synthetic kill test as a way to
reject MOSAIC's compositional assumption before biomedical training.

The rules-permitted frozen [multi-encoder branch](MULTI_ENCODER_BRANCH.md) is a post-B2 score experiment, not another
research lane. LEO, MoVE-KD, METEOR, MedPLIB, and Anatomy-VLM eliminate a broad novelty claim. It is eligible only with
a duplicate-native control, full active-parameter and resource accounting, one-model loader closure, and a gain beyond
the single-encoder B2 under both real-cost and compute-matched reporting.

The [base-conditional preservation ablation](BASE_CONDITIONAL_PRESERVATION.md) is a base-architecture-preserving attempt to reduce
negative flips after B2 exists. S3FT and Margin Preserving Training prevent a novelty claim. Its value is a cleaner
competition decision: it must beat ordinary B2, unconditional KL, and a shuffled-gate control without suppressing
positive flips or visual target tracking.

The [weight-interpolation branch](WEIGHT_INTERPOLATION_BRANCH.md) is a post-B2 closed comparison at fixed coefficients,
not a research claim. It is eligible only after effective-delta/export equivalence and must beat ordinary B2 without
trading away either the answer or context endpoint.

## New evidence from the MMBU paper

The current MMBU v2 paper reports:

- 410 source datasets, 35 submodalities, 20 specimens, and ungrounded classification, two grounded-classification
  routes, and object detection;
- weak object detection across models;
- large closed-to-open performance drops;
- medically adapted models that can lose to their general-purpose bases; and
- meaningful text-only performance, showing that language shortcuts remain possible.

Those observations prioritize spatial supervision, open-answer instruction quality, visual-reliance controls, and
base-relative negative-flip reporting. They do not justify using the MMBU public examples for training or selection.
Source: [MMBU v2](https://arxiv.org/html/2606.06696v2).

## B4 feasibility facts

The [official MedQwen repository](https://github.com/IMPACT-L/MedQwen) currently exposes only a README and one commit in
the inspected public state. No implementation or checkpoint was established by this audit. The paper is sufficient to
make B4 a mandatory literature comparator, not sufficient to claim a reproducible local baseline.

Before implementation, record:

- repository commit and license;
- whether code and weights actually exist;
- exact Qwen base revision and adapted module set;
- total/trainable/active parameters and SVD cost;
- image/token preprocessing and dataset mixture;
- custom loader and `trust_remote_code` requirements;
- BF16/FP16 export behavior, checkpoint bytes, and measured latency; and
- which paper details are insufficient for independent reproduction.

## Next no-training work order

1. Review and maintain the completed [MedQwen reproduction-gap audit](MEDQWEN_REPRODUCTION_GAP.md); do not invent
   missing hyperparameters.
2. Build the source-factor incidence table required by G-1 from admitted metadata only; current candidates remain
   unapproved.
3. Implement the reviewed [annotation-to-task lattice](ANNOTATION_TASK_LATTICE.md) with synthetic golden fixtures,
   including per-unit loss-mass normalization and unknown-context masking;
   do not create biomedical labels or emit real training views before source admission.
4. Measure one native base load/forward/export/reload on the authorized MOCS allocation before planning a sweep.
5. Ask the organizer how ordinary adapters and custom modules are packaged; retain B2 as the lowest-complexity branch,
   pending actual loader confirmation.

No model download, source acquisition, training job, upload, or public-set evaluation is authorized by this portfolio.
