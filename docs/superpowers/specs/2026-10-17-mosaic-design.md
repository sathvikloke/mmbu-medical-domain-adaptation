# MOSAIC: metadata-factorized compositional adaptation for MMBU Track 2

**Status:** research design v1.1 for review, not an implemented or validated method  
**Date:** October 17, 2026  
**Primary claim type:** external-data domain adaptation with held-out-combination generalization  
**Prohibited claim:** improved MMBU or hidden-set performance before a frozen eligible model is evaluated

> **Current disposition:** frozen on the current source grid. The later source-incidence audit found the design
> non-identifiable before biomedical training. This file preserves the hypothesis and controls; it is not the active
> flagship. A genuinely crossed future grid must pass G-1 and receive a fresh adverse score.

## Decision

Replace the vague “medical LoRA plus a visual probe” idea with one falsifiable primary hypothesis:

> A single VLM whose lightweight adaptation is composed from reusable biomedical factors will generalize to unseen
> modality–specimen–task combinations better than an equal-parameter shared adapter or flat modality-expert model,
> while region-supervised training improves localization without sacrificing classification or output validity.

The proposed method is **MOSAIC**, short for **Metadata-factorized Orthogonal Spatial Adaptation for Image
Compositionality**. It is a single end-to-end VLM. It performs no retrieval, external tool call, auxiliary-model
inference, repeated sampling, crop-and-retry, or test-time update. All extra supervision and counterfactual checks are
training-time or offline diagnostics.

Historically, MOSAIC was the lead research branch after a standard shared-adapter baseline. It is now frozen on the
current grid. If a future G-1-passing design is revived and dynamic composition is not
accepted by the organizer loader, fails fresh reload, or does not beat both the parameter-matched and active-FLOP-matched
shared-adapter controls, the project falls back to the shared adapter. The name is not the contribution; the controlled
comparison is.

## Why this is the right problem

MMBU spans 410 datasets, 35 submodalities, 20 specimens, and multiple classification and localization tasks. Its paper
reports that no model dominates across domains, medical adaptation gains are heterogeneous, and all tested VLMs are
weak at object detection. It explicitly identifies stronger spatial modeling and adaptation beyond established
datasets as open directions. ([MMBU](https://arxiv.org/abs/2606.06696))

Existing medical adaptation is often organized by dataset, task, or modality. That is poorly matched to a hidden set
made from new combinations. A retinal classification expert cannot automatically help retinal localization; a
radiology expert cannot automatically contribute its detection skill to microscopy. The project should learn reusable
factors rather than memorize source identities.

The Modality–Anatomy–Task (MAT) literature gives direct evidence that medical VLMs can generalize compositionally and
that leaving out any axis causes material degradation, but it primarily studies data composition and benchmarks rather
than a factor-composed adapter for a generative VLM. ([Med-MAT / ACL
2025](https://aclanthology.org/2025.acl-long.639.pdf), [CrossMed](https://arxiv.org/abs/2511.11034))

## What is and is not novel

The following are **not** novel and must never be marketed as our invention:

- medical LoRA or projector tuning;
- modality- or task-routed mixture-of-experts;
- counterfactual blank, shuffled, absent, or hard-negative image training;
- localization supervision or coordinate-token generation;
- multi-task or modality-balanced sampling;
- base-model anchoring to reduce forgetting.

Those areas already include Med-MoE, Sparse Spectral LoRA/MedQwen, BioFact-MoE, LoRA-Mixer,
modality-specialized MedMoE, Two-Stage Mixture-of-LoRA, CORAL hard-negative grounding,
localization-grounded supervision, MEDALIGN, and bounded-forgetting adaptation. ([Med-MoE](https://aclanthology.org/2024.findings-emnlp.221/),
[Sparse Spectral LoRA](https://arxiv.org/abs/2604.01310),
[BioFact-MoE](https://arxiv.org/abs/2605.26376),
[LoRA-Mixer](https://arxiv.org/abs/2507.00029),
[Two-Stage Mixture-of-LoRA](https://arxiv.org/abs/2609.14350),
[CORAL](https://arxiv.org/abs/2607.03647),
[Localization-Grounded Supervision](https://papers.miccai.org/miccai-2026/0588-Paper3411.html),
[MEDALIGN](https://arxiv.org/abs/2512.18554),
[CADRE](https://papers.miccai.org/miccai-2026-sat/SAFER_022.html))

The candidate contribution is narrower:

1. Decompose adaptation into independently supervised **modality**, **specimen/biological-scale**, and **task-geometry**
   low-rank bases instead of one adapter per dataset or one flat expert per modality.
2. Compose those bases per input using a small router trained from pixels and the allowed question prompt, while
   randomly withholding metadata supervision so inference never needs privileged metadata.
3. Train and select on **held-out factor combinations and held-out source families**, not random examples from the same
   combination.
4. Couple the task-geometry factor to region/box supervision so localization skill is reusable across modalities.
5. Bound interference with a shared residual path, base-anchor loss, and explicit gradient-conflict reporting.

> **Superseding status (October 17, 2026):** the later source–factor incidence audit found the current optimistic grid
> rank deficient and non-identifiable. The 7.2/5.4 literature-only scores below are historical. Current-grid MOSAIC is
> rated 4.5 competition value and 5.5 concept novelty with 0.5 evidence, and biomedical training is frozen. A future
> crossed grid must pass G-1 and be rescored; see the
> [independent arbitration](../../team/INDEPENDENT_IDEA_ARBITRATION.md).

The expanded literature search found direct work on MAT compositional generalization, routed LoRA experts for medical
VLMs, biologically factorized medical LoRA pathways, dynamic LoRA composition, factor-specific VLM adapters, and
localization supervision. It did **not** establish that this exact three-axis residual design and control protocol are
new, and the direct antecedents make a broad method claim indefensible. The current honest novelty score is **7.2/10 as
a competition concept and approximately 5.4/10 as a paper claim**. See the adverse [novelty
audit](../../team/NOVELTY_AUDIT.md). Never make a “first” claim from the current evidence.

## Model design

### Backbone

Start with one feasible open-weight VLM after E01 resource measurement. The current compatibility baseline is
Qwen2.5-VL-7B-Instruct. Qwen3-VL-8B-Instruct is a candidate only if its native loading, image path, official prompt,
non-quantized export, and measured cost pass. Model choice is not part of the MOSAIC contribution.

### Adapter placement

Use low-rank updates in:

- the multimodal projector or merger;
- the last small block of vision-transformer layers only if the projector-only baseline saturates;
- selected late language attention/MLP projections needed for output conventions.

Do not start by adapting the full vision encoder. Every promoted configuration must record the exact trainable module
set, parameter count, dtype, optimizer state, and saved keys.

### Factor composition

For an adapted linear map, the residual is:

`ΔW(x,q) = ΔW_shared + Σ α_m(x,q)ΔW_modality,m + Σ β_s(x,q)ΔW_specimen,s + Σ γ_t(x,q)ΔW_task,t`

where `x` is the native image representation and `q` is the official-style question. The task factor may use allowed
question semantics. Modality and specimen factors must be predicted from visual tokens and may not receive dataset IDs,
reference labels, MMBU metadata, or another inference pass.

The first draft left a circularity: a router cannot depend on the output of a dynamically adapted layer before choosing
that layer's route. Version 1.1 fixes the computation order. The visual router input is a stop-gradient pooled summary
from a frozen early vision stage, before every dynamically adapted vision block. The question input is pooled from the
base token embeddings before every dynamically adapted language block. One small router computes one coefficient vector
per example; that vector is reused for the rest of the single forward pass. Version 1 therefore may adapt only vision
blocks after the routing tap. Adapting an earlier vision block requires a new non-circular design and is out of scope.

Implement composition on residual outputs rather than materializing a different dense weight for each example. For a
batched hidden state `h`, compute each low-rank `B_k(A_k(h))`, weight that residual by the example's route coefficient,
and add the shared residual. This makes batched execution, dtype/device behavior, active-FLOP accounting, and saved state
keys explicit. It does not add a second model call or a pre-inference classifier.

Keep the first implementation deliberately small:

- one shared residual;
- 4 modality bases;
- 4 specimen/scale bases;
- 3 task-geometry bases: global recognition, region-conditioned recognition, and coordinate localization;
- soft normalized routing with a fixed temperature and load-balance penalty;
- identical active parameter and FLOP accounting for every comparison.

These are starting values, not tuned truths. Change them only on external development data under a new recorded
experiment.

### Router supervision

External training records may provide modality, submodality, specimen, stain, scale, and task tags. Map them into a
versioned coarse taxonomy with an explicit `unknown` state. Supervise routing when a tag is reliable; otherwise mask its
loss. Randomly mask available router labels during training, and include an image-only routing consistency loss, so the
model cannot require metadata at evaluation.

The router must be audited on held-out source families. High training accuracy with poor held-out routing is a failed
mechanism, even if aggregate task accuracy rises.

### Spatial curriculum

Use three external-data stages while keeping one final model:

1. global classification and applicable context metadata;
2. classification inside supplied regions or regions derived from permitted source annotations;
3. direct coordinate generation from detection boxes and segmentation-derived boxes.

Segmentation masks may create boxes only through a frozen, versioned conversion. A mask class is not automatically a
diagnostic label. The final target format must match the organizer’s confirmed pixel `xywh` convention; internal
normalized coordinates, if used by the backbone, must be inverted exactly and tested.

### Loss

The initial objective is a declared weighted sum of:

- autoregressive answer/coordinate loss;
- applicable context-field loss;
- factor-routing supervision;
- image-only route consistency;
- load-balance and route-entropy regularization;
- base-anchor KL on a fixed, eligible anchor set;
- optional region-token alignment where a source provides trustworthy spatial annotation.

CORAL-style hard negatives may be included only as a named ablation because that contribution already exists. It must
not be bundled into MOSAIC without showing which component caused the gain.

## Data design

Every real source remains ineligible until acquisition, rights, grouping, conversion, QA, and purpose records pass the
repository’s admission contract. Independent training splits from datasets contributing to MMBU are allowed by the
October 14 organizer response, but no organizer overlap checker exists. We therefore retain the stronger controls:

- no MMBU public example, label, annotation, model output, crop, embedding, or derivative in training;
- no model or recipe selection from MMBU public results;
- source, release, item, image, and parent hashes retained;
- exact and perceptual cross-source duplicate review;
- patient/study/slide/volume/experiment grouping where available;
- dataset/source-family holdouts and factor-combination holdouts created before training.

The minimum pilot needs at least two independently cleared source families and coverage of at least two values on each
factor axis. A single radiology collection cannot validate the MOSAIC claim.

### Gate G-1: factor identifiability before training

No MOSAIC mechanism run is authorized until a source-by-factor incidence audit proves that the factors are not aliases
for datasets. At minimum:

- every held-out combination contains only factor values individually observed in training;
- every task-geometry value used in the claim appears in at least two modality classes and two source families;
- every modality value used in the claim appears with at least two task-geometry values;
- the additive one-hot design matrix for modality, specimen/scale, and task geometry has full column rank after the
  declared reference levels are removed;
- no factor level maps one-to-one to a source family;
- independent-unit counts, not transformed-row counts, support every reported cell; and
- held-out cells and source families are frozen before any comparative model result is opened.

If this gate fails, shared-adapter work may continue, but factor routing is only an engineering probe and cannot support
the MOSAIC compositional-generalization claim.

Current evidence fails G-1. BBBC039 supplies microscopy geometry from one BBBC family. ROCO and PMC-VQA share a
PMC-literature family and do not create independent families by being separate releases. They do not form a sufficiently
crossed modality × specimen × geometry design. MedMNIST+ is a promising classification-only candidate, while BBBC038
could broaden microscopy geometry and VinDr-CXR could add radiology boxes; none is admitted, and the latter is
credentialed. These candidates require their own version, rights, lineage, overlap, QA, grouping, purpose, and release
review. No download or training is authorized by naming them here.

### Split construction

Construct a bipartite coverage table before splitting:

- rows: source families;
- columns: coarse modality × specimen/scale × task-geometry combinations.

Then freeze:

- training combinations;
- external development combinations;
- a **held-out-combination** set whose individual factors appear in training but whose joint combination does not;
- a **held-out-source** confirmation set;
- one small output/judge calibration set disjoint from all selection scores.

If the available data cannot create both held-out-combination and held-out-source evaluation, the compositional claim is
blocked; do not replace it with a random-row split and keep the same claim.

## Comparisons

All primary comparisons use the same base checkpoint, eligible records, number of optimizer updates, effective examples,
image-token budget, and target-token budget. A single shared-adapter comparator cannot generally match both MOSAIC's
total stored parameters and its conditionally active FLOPs, so the original phrase “matched cost” was underspecified.
Use two shared controls: a parameter-matched control and an active-FLOP-matched control. Promotion must beat the stronger
of the two, and every table must report total parameters, trainable parameters, active parameters, measured latency,
peak memory, and checkpoint bytes separately.

| ID | Condition | Purpose |
|---|---|---|
| B0 | untouched base | establishes adaptation delta |
| B1 | language-only shared LoRA | measures formatting and medical-language gains |
| B2-P | shared projector + late-language LoRA, rank chosen to match total trainable parameters | rules out gains from greater stored capacity |
| B2-F | shared projector + late-language LoRA, rank chosen to match active adapter FLOPs | rules out gains from greater per-example compute |
| B3 | flat modality-expert LoRA | tests whether factorization beats a conventional expert bank |
| B4 | independently reproduced Sparse Spectral LoRA/MedQwen | strong published medical routed-LoRA baseline; conditional on code/license/resource/packaging verification |
| M1 | MOSAIC without spatial curriculum | isolates factor composition |
| M2 | full MOSAIC | tests the complete hypothesis |
| A1 | M2 without base anchoring | measures forgetting control |
| A2 | M2 with shuffled factor labels | negative control for factor semantics |
| A3 | M2 with uniform routing | tests whether the learned router matters |

B3 is optional if it cannot be implemented under both declared comparison profiles before the decision deadline. B0,
B1, B2-P, B2-F, M1, M2, and the shuffled-label negative control are mandatory for a mechanism claim. B4 is mandatory
before any claim that MOSAIC advances medical routed adaptation, but not before the initial feasibility probe if its
official implementation is unavailable. Do not infer performance from the paper or call an unverified reimplementation
equivalent.

## Metrics and success gates

Report task accuracy/F1 as appropriate, context score, malformed-output rate, coordinate IoU success, task-change score,
per-source and per-factor-combination results, worst-decile combination performance, route entropy, route accuracy,
trainable/active parameters, peak memory, tokens, GPU-hours, and wall time.

### Gate G0: feasibility

- native base inference succeeds;
- one synthetic optimizer step updates every declared module and no undeclared module;
- save, network-denied fresh reload, and interrupted resume reproduce the declared state;
- non-quantized BF16/FP16 artifact fits the evaluation envelope;
- dynamic router export is accepted by the loader or the MOSAIC branch stops.

G-1 must pass before G0 can authorize a biomedical mechanism experiment. G0 may be exercised first on synthetic tensors
only to test the implementation.

### Gate G1: mechanism pilot

On external development data, M1 must beat the stronger of B2-P and B2-F on held-out combinations, not only the natural mixture. Routing must beat
uniform and shuffled-label controls. A gain caused only by easier output formatting or source identity fails this gate.

The primary endpoint is macro performance over prospectively held-out factor combinations at the independent-group
level. Use a paired group bootstrap. The practical superiority margin and bootstrap repetitions are fixed from a blind
variance pilot before comparative outputs are opened; the lower confidence bound must exceed that margin. Worst-decile
combination performance is a mandatory safety endpoint. For M2 versus M1, classification/context performance also has a
prospectively fixed non-inferiority margin. Do not invent numerical margins after seeing an effect.

### Gate G2: spatial value

M2 must improve localization over M1 without a material classification/context regression. Region supervision must
improve a held-out modality or held-out source, not just the source providing boxes.

### Gate G3: replication

The retained recipe must reproduce on a second prospectively registered seed and survive the one-time held-out-source
confirmation. Exact practical thresholds and multiplicity handling must be locked after the variance pilot and before
comparative scoring.

### Stop rules

Stop or demote MOSAIC when any of the following is true:

- it does not beat the stronger of B2-P and B2-F on held-out combinations in two properly completed attempts;
- gains disappear under source-balanced scoring;
- the router learns dataset/source identity rather than factors;
- classification gains occur unchanged with mismatched or absent images;
- localization improves only on seen annotation pipelines;
- custom loading, export, or runtime cannot be made organizer-compatible;
- peak memory or throughput makes replication infeasible;
- a simpler baseline is statistically and practically indistinguishable.

Source-identity failure is tested, not judged by intuition. Fit a frozen linear source probe to route logits on held-out
groups and compare it with a factor-label-only probe under within-factor-cell source permutation. Source predictability
above the prospectively frozen permutation envelope is evidence of residual source encoding. Report this even when task
performance improves.

Negative results are a successful falsification of the method, not permission to tune on MMBU public data.

## Compute feasibility

UTC’s published Slurm resources include 16 `epyc` nodes with two A100 80 GB GPUs each, plus V100 and P100 nodes.
([UTC HPC](https://www.utc.edu/research/quantum-center/infrastructure/high-performance-computing)) This establishes
institutional hardware availability, not the user’s allocation, queue limits, software environment, or measured
throughput.

Design for one A100 80 GB first:

- 7B–9B backbone;
- BF16 where supported;
- gradient checkpointing;
- LoRA/projector adaptation before any broader unfreeze;
- small per-device batch with recorded accumulation;
- no multi-node dependency for the pilot;
- resumable checkpoints and a 15% compute reserve.

Five concurrent job slots should be used for independent CPU/data checks and bounded sweeps only after one end-to-end
job is measured. Never launch five expensive training jobs before the first job supplies peak memory, examples/second,
tokens/second, checkpoint size, and restart evidence.

## Competition compliance

- One frozen, end-to-end submitted VLM.
- No ensemble or external expert model; adapter bases and router are components of the one checkpoint.
- No external retrieval, API, database, OCR model, calculator, code execution, or tools at evaluation.
- One native model call for each organizer task/context prompt; no state sharing.
- No test-time learning, adapter swapping from an external service, repeated sampling, or self-consistency.
- Raw outputs are preserved; local policy treats malformed committed JSON as incorrect and never repairs it. The
  current card's raw-reply fallback conflicts with the direct organizer email and remains unresolved for
  official-equivalent scoring.
- “Any one” detection emits one box and uses the organizer-confirmed IoU ≥ 0.5 rule.
- Only requested context fields are emitted.
- Full training-dataset and model-component disclosure.
- Public MMBU remains outside optimization despite organizer permission to use it for selection.

The unresolved compliance gate is whether the final loader permits a custom dynamic adapter/router module and how it
must be packaged. Until answered, B2 is the guaranteed-compatible fallback.

## Claude implementation work order

Claude should not start model training from this document. Its first task is a read-only design/compatibility pass:

1. Identify the exact base model modules for the frozen early-vision routing tap, projector/merger, eligible post-tap
   vision blocks, and late language projections. Reject any circular route dependency.
2. Produce a table of tensor shapes, candidate LoRA targets, trainable counts, expected BF16 memory, and standard
   Hugging Face save/load behavior.
3. Prototype the smallest residual-output factor-composition layer on synthetic tensors only. It must support batched
   routing without per-example dense-weight materialization, preserve dtype/device/autocast, expose deterministic state
   dict keys, and reload without network access.
4. Prove that uniform routing reproduces the declared algebra and that shuffled factor labels are representable as a
   negative control.
5. Build no biomedical dataset and download no model weights until the user approves the design and the repository’s
   model/data authority gates allow it.
6. Return a risk register covering custom-code loading, `trust_remote_code`, mergeability, distributed training,
   checkpoint size, inference latency, and failure fallback to B2.
7. Produce separate parameter-matched and active-FLOP-matched B2 designs; do not call one comparison “matched” to both.
8. Run no biomedical mechanism experiment until the G-1 incidence audit passes.

Only after that review, one measured native-load smoke test, and eligible data admission should an implementation plan
authorize training.

## Historical ratings before the source-incidence failure

These rows are retained to preserve the design's review history. They are superseded by the status note above and must
not be quoted as current ratings.

| Dimension | Score | Ceiling and next falsifiable gate |
|---|---:|---|
| Problem–benchmark fit | 9.4/10 | 9.7 after final context prompt and loader are pinned |
| Competition compliance | 9.1/10 | 9.7 after custom-module packaging is confirmed |
| Competition-concept novelty | 7.2/10 | Direct medical routed/factorized antecedents found; a genuinely distinct mechanism and ablations are required |
| Paper-level novelty | 5.4/10 | Current design is an integration-level distinction, not a defensible broad method novelty claim |
| Falsifiability | 9.7/10 | Architecture, identifiability, confounding, and dual-cost controls are now explicit; numerical margins still require a blind variance pilot |
| Compute feasibility | 8.3/10 | 9.5 after one measured A100 load/train/export/restart probe |
| Data feasibility | 5.0/10 | 9+ only after two source families and held-out combinations pass admission/QA |
| Current empirical evidence | 0.5/10 | No native model, training, or biomedical performance run exists |
| Overall research idea today | 7.8/10 | High benchmark fit but medium novelty; 9+ requires a distinct mechanism plus G-1 and successful B2-P/B2-F/B4/M1/M2 comparisons |

The project should optimize for the strongest surviving evidence, not for keeping the MOSAIC name alive.
