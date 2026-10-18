# QUILT design: quotienting interface gradients for loader-safe tuning

**Date:** October 17, 2026  
**Status:** adversely reviewed, unimplemented diagnostic hypothesis; no model-quality claim  
**Primary role:** gated negative-result/mechanism branch that still exports as an ordinary LoRA/merged checkpoint; not
the flagship competition idea

The binding portfolio disposition is recorded in
[QUILT_ADVERSE_REVIEW.md](../../team/QUILT_ADVERSE_REVIEW.md). This specification is preserved because its failure
tests remain useful, not because the original novelty score survived review.

## One-sentence hypothesis

When approved prompt presentations express the same verified medical annotation atom with the same image, grounding
carrier, and serialized target, the directions in which their adapter gradients disagree may contain prompt-interface
nuisance; estimating that subspace from complete same-fact prompt panels and removing it from subsequent biomedical updates may improve
unseen-template transfer without a custom inference architecture.

QUILT expands to **QUotienting Interface gradients for Loader-safe Tuning**. The name is provisional and carries no
novelty claim.

## Why this is a different bet

MOSAIC bets that the best inductive bias is a routed set of semantic residual experts. Recent work makes that crowded:
routed, spectral, and biologically factorized LoRA experts already exist. QUILT instead changes the optimization
geometry during training and disappears at inference. The submitted artifact remains the same class of ordinary adapter
or merged checkpoint as the loader-safe B2 baseline.

The benchmark fit is direct. MMBU asks related medical facts through ungrounded classification, region-grounded
classification, localization, and open/closed answer forms. A model can learn the source label yet overfit the wording,
coordinate serializer, option structure, or grounding carrier. QUILT tries to quotient those interface-specific update
directions while retaining the update shared by equivalent views of the same source fact.

## Prior-art boundary

QUILT does **not** claim to invent multi-task gradient manipulation, cross-task consistency, gradient subspaces, or
projected LoRA.

| Prior work | What already exists | What QUILT would still have to distinguish |
|---|---|---|
| [PCGrad](https://papers.neurips.cc/paper_files/paper/2020/file/3fe78a8acf5fda99de95303940a2420c-Paper.pdf) | Projects conflicting task gradients | QUILT estimates nuisance from within-fact interface differences rather than treating all task conflict as harmful |
| [CAGrad](https://proceedings.neurips.cc/paper/2021/hash/9d27fdf2477ffbff837d73ef7ae23db9-Abstract.html) | Optimizes average loss while protecting worst local task improvement | CAGrad is a required optimizer control; it does not define same-fact interface equivalence classes |
| [CocoCon](https://arxiv.org/abs/2303.16133) | Measures and trains cross-task consistency in unified vision-language models | QUILT acts on adapter-gradient difference subspaces and tests held-out medical task interfaces |
| [SOrT VQA](https://aclanthology.org/2021.naacl-main.248/) | Aligns explanation gradients across related VQA questions | Its Grad-CAM contrastive objective is not a PEFT nuisance quotient, but defeats any broad “first gradient consistency” claim |
| [SubPT](https://arxiv.org/abs/2211.02219) | Projects prompt-tuning gradients onto early gradient-flow subspaces | QUILT removes a paired interface-difference subspace instead of retaining a generic early-training subspace |
| [ProGrad](https://openaccess.thecvf.com/content/ICCV2023/html/Zhu_Prompt-aligned_Gradient_for_Prompt_Tuning_ICCV_2023_paper.html) | Keeps prompt-tuning updates aligned with gradients representing pretrained general knowledge | Prompt-specific gradient regulation is established; QUILT must distinguish paired nuisance identification from generic alignment/preservation |
| [Gradient-Regulated Meta-Prompt Learning](https://openaccess.thecvf.com/content/ICCV2023/html/Li_Gradient-Regulated_Meta-Prompt_Learning_for_Generalizable_Vision-Language_Models_ICCV_2023_paper.html) | Meta-learns a gradient regulator for cross-domain VLM prompt generalization | Gradient regulation for prompt robustness/generalization is not new, even though its learned regulator is not QUILT's paired quotient |
| [Latent Adversarial Paraphrasing](https://aclanthology.org/2025.emnlp-main.1595/) | Trains robustness to semantically preserving prompt variants through a dual-loop latent paraphrase method | Leave-one-paraphrase-out robustness is an established target; QUILT must beat a faithful paraphrase-robustness control, not only ordinary consistency |
| [Understanding the Prompt Sensitivity](https://aclanthology.org/2026.acl-long.2053/) | Relates meaning-preserving prompts, gradients, and next-token log-probability sensitivity through first-order analysis | Gradient-based analysis of prompt sensitivity is established; QUILT's distinction is parameter-update subspace identification, not the observation that prompt gradients explain sensitivity |
| [Recover-to-Forget](https://openreview.net/forum?id=n7peBaPUmk) | Computes LoRA gradients over multiple paraphrases of one target fact and averages them to reduce single-wording sensitivity before reconstructing an unlearning gradient | Same-fact multi-view paraphrase LoRA gradients and their aggregation are established; QUILT must beat a matched mean-gradient condition and claim only centered nuisance identification/removal |
| [LoRA-FA](https://arxiv.org/abs/2308.03303) | Freezes LoRA's down-projection `A` and trains `B` for memory-efficient tuning | Fixed-`A` coordinates are an identifiability device and control, not a novel adapter claim |
| [GPM](https://openreview.net/pdf?id=3AOj0RCNC2) and [InfLoRA](https://openaccess.thecvf.com/content/CVPR2024/html/Liang_InfLoRA_Interference-Free_Low-Rank_Adaptation_for_Continual_Learning_CVPR_2024_paper.html) | Use SVD-derived subspaces and orthogonal update constraints, including in low-rank adaptation | Fixed-basis orthogonal gradient updates are structurally established; QUILT can claim only a different basis source and prediction |
| [AND-mask](https://openreview.net/pdf?id=hb1sDDSLbV), [Fish](https://openreview.net/pdf?id=vDwBW49HmO), and [Fishr](https://proceedings.mlr.press/v162/rame22a.html) | Promote gradient agreement or match gradient statistics across environments for invariance/domain generalization | Treating prompt templates as environments and suppressing disagreement is established |
| [INLP](https://aclanthology.org/2020.acl-main.647/) | Removes linearly decodable protected information by repeated null-space projection in representation space | Null-space nuisance removal is established; parameter-space placement is not itself novelty |
| [Mechanistically Guided LoRA for Medical VLM Consistency](https://proceedings.mlr.press/v333/sadanandan26a.html) | Trains medical-VLM LoRA with paraphrase-consistency and supervised accuracy losses | Medical-VLM paraphrase consistency is a direct antecedent, not an untouched problem |
| [Consistent but Dangerous](https://arxiv.org/abs/2603.20985) | Shows that lower medical-VLM paraphrase flip rates can coexist with loss of image reliance | Prompt consistency cannot serve as a safety or grounding proxy; image-dependence gates are mandatory |
| [Categorical Atlas of PEFT](https://arxiv.org/abs/2610.12728) | Formalizes PEFT maps, fibres/gauges, expressivity obstructions, composition behavior, and optimizer-dependent LoRA symmetries; Adam generally preserves only signed-permutation gauge symmetry | Gauge and optimizer non-invariance are established; QUILT's basis-rotation tests are correctness checks, not novelty |
| [GRAM](https://www.medrxiv.org/content/10.64898/2026.07.18.26358397v1.full) | Uses gradient criteria, subspace-constrained LoRA, and adapter merging for neuroimaging VQA | This is the closest medical warning; QUILT must beat a layer-selection/subspace control and cannot claim first projected medical LoRA |
| [DOME](https://arxiv.org/abs/2507.03545) | Estimates nuisance directions from stochastic-gradient covariance and filters them | QUILT's nuisance label comes from controlled same-fact interface interventions, not generic sharp/noisy directions |
| [GERNE](https://openaccess.thecvf.com/content/ICCV2025/html/Asaad_Gradient_Extrapolation_for_Debiased_Representation_Learning_ICCV_2025_paper.html) | Uses gradients from batches with different spurious-correlation levels and treats their difference as a debiasing direction | “Gradient differences reveal nuisance and can guide debiasing” is not new; paired subspace identification and projection must provide the distinction |
| [iGSP](https://arxiv.org/abs/2605.19301) | Implicit gradient-subspace projection for continual VLM adaptation | QUILT is not continual routing; it must show that paired interfaces identify a different, useful subspace |
| [GRIT](https://arxiv.org/abs/2601.00231) and [FoRA](https://arxiv.org/abs/2605.29317) | Use K-FAC/Fisher geometry, Fisher-guided reprojection or selection, and orthogonality constraints in PEFT | A Fisher-metric QUILT extension is not a clean novelty escape and adds compute; keep it rejected unless it yields a separately derived prediction |
| [Cross-modal task vectors](https://proceedings.mlr.press/v267/luo25c.html) | Finds task representations invariant to modality and format in autoregressive VLMs | Provides a mechanistic motivation, not evidence that QUILT's gradient quotient works |

The defensible contribution, if successful, is narrow: **controlled same-fact prompt presentations with identical
targets identify a removable gradient nuisance subspace for medical-VLM PEFT, improving leave-one-template-out transfer
while retaining ordinary inference packaging**. Without the negative controls and held-out transfer, QUILT is only an
application of projected multi-task optimization.

## Eligible equivalence families

The [annotation-to-task lattice](../../team/ANNOTATION_TASK_LATTICE.md) supplies source facts and derivations. QUILT may
compare gradients only when two views conserve the same target atom.

| Conserved atom | Candidate family members; pair class must be assigned below | Not equivalent |
|---|---|---|
| Source class ID | prompt paraphrases with identical label target; open label; closed option; ungrounded label; box-grounded label; mask-grounded label | Class label versus coordinate target |
| Source or mask-derived box | alternate approved coordinate serialization; localization wording | Box versus mask when their geometries disagree |
| Complete instance set cardinality | count answer; cardinality of a complete localization list | Count from an incomplete annotation set |
| Binary source proposition | open yes/no; closed yes/no with counterbalanced order | Absence inferred from missing annotation |

Membership in one row does not make two views primary-basis eligible. The three-class rule below is binding and only
strict presentation-equivalent pairs enter the confirmatory primary basis. Pairs are prohibited when a view invents a
diagnosis, changes clinical meaning, uses a different source fact, crosses
an independent-unit group, or originates from MMBU public data. Equivalent wording alone is insufficient: both targets
must round-trip to the identical frozen source atom.

The design distinguishes three pair classes:

- **Strict presentation-equivalent pairs** keep image pixels, grounding carrier, source atom, requested semantic answer,
  and exact serialized target-token sequence fixed while changing only an approved prompt template or paraphrase. These
  are the only pairs eligible for the primary nuisance basis.
- **Answer-interface-equivalent pairs** keep the source atom fixed but change the supervised target serialization, such
  as an open label versus a closed option letter. Their differences contain answer-generation semantics and are a
  separately named secondary condition, not primary nuisance evidence.
- **Carrier-equivalent pairs** keep the source atom fixed but change visual grounding carrier or output family, such as
  box-grounded versus mask-grounded classification. Their differences can contain legitimate visual computation. They
  are diagnostics and a separately named exploratory condition, never silently pooled into the primary basis.

This restriction makes QUILT narrower but falsifiable. A result using carrier-equivalent or answer-interface-equivalent
pairs cannot support the claim that superficial task-interface directions were removed unless an independent analysis
proves that target-semantic directions were preserved.

## Parameter geometry

Raw LoRA-factor gradients are not a stable geometry. If `delta_W = B A`, transformations such as `B C` and
`C^-1 A` describe the same effective update but change the factor-coordinate gradients. QUILT must not project arbitrary
`A/B` coordinates and call the result intrinsic.

The first executable version therefore uses a **fixed-basis LoRA** condition:

1. Each adapted matrix receives a deterministically generated or prospectively selected orthonormal down basis `A`.
2. `A` remains frozen for the entire condition; only coefficient matrix `B` is trainable.
3. Every comparison using QUILT uses the same `A`, target modules, rank, alpha, initialization, and training budget.
4. A standard trainable-`A/B` B2 remains an external performance control but is not used to interpret subspace angles.
5. The saved artifact contains ordinary `A` and `B` tensors and must pass the same offline reload gate.

An effective-weight tangent implementation may replace fixed-basis LoRA later only after a gauge-invariance proof and
synthetic reparameterization test. It is not silently interchangeable with this design.

## Calibration algorithm

Let `theta` denote the concatenated trainable `B` coefficients under a fixed parameter ordering. For independent unit
`z`, conserved atom `a`, and eligible interface `v`, define the target-token-normalized teacher-forcing loss
`L(z,a,v; theta)` and its gradient `g_zav`.

For the scientific development study, source-group splitting occurs before prompt expansion and creates disjoint
`basis_fit`, `basis_audit`, `adapter_train`, and `validation` units. `basis_fit` estimates `U`; `basis_audit` tests its
rank, angles, template/source stability, and overlap without changing it; `adapter_train` supplies biomedical updates;
and `validation` evaluates frozen promotion rules. No independent unit or duplicate group crosses these roles. A later
competition refit may combine admitted non-evaluation units only after the condition and hyperparameters are frozen,
but that refit cannot support the scientific mechanism claim.

Template lineage is split independently from units. Paraphrases descended from the same canonical wording/generator
seed family are grouped before assignment to `basis_templates`, `audit_templates`, `train_templates`, or
`validation_templates`; no family crosses roles. `basis_templates` alone estimate `U`. On disjoint `basis_audit` units,
`audit_templates` test whether never-fitted strict presentations produce centered gradients captured by the frozen `U`.
They cannot change `U`, rank, modules, thresholds, or prompts. `train_templates` alone supply biomedical training views,
and `validation_templates` remain untouched until the one-time validation opening. Thus an audit-template pass is a
pretraining mechanism gate, not the final transfer result.

### Step 1: complete-panel centered gradients

The confirmatory estimator requires every admitted `(z, a)` calibration unit to appear under the same complete set of
`m >= 3` strict prompt templates. For each unit:

1. compute every `g_zav` at the frozen calibration checkpoint;
2. reject the entire unit—not an individual template—when any view violates a predeclared zero, nonfinite, execution,
   or extreme-norm rule;
3. compute the within-unit mean `g_bar_za = (1/m) * sum_v g_zav`;
4. form `h_zav = g_zav - g_bar_za` before any norm normalization; and
5. optionally apply one common positive unit scale to all `h_zav`, for example
   `c_za = sqrt((1/m) * sum_v ||g_zav||^2 + epsilon)` and `d_zav = h_zav / c_za`.

Within-unit centering cancels the shared fact term under the additive model without creating dependent pair rows or
letting the chosen edge graph rotate a truncated basis. Per-view normalization is prohibited: centering
`unit(s+n_v)` does not cancel `s` in general. The exact unit scale and epsilon are frozen, and an unscaled-centered
condition shows whether the result depends on unit reweighting. Independent units receive equal total mass; each of the
`m` templates receives equal mass within a unit.

The primary estimator does **not** stack every `d_zav` as an independent covariance row. Let `s` index the frozen
independent source groups. For each template, first compute a within-source centroid
`q_sv = (1/n_s) * sum_(z,a in s) d_zav`, then compute the source-balanced centroid
`q_v = (1/|S|) * sum_s q_sv`. Every admitted source receives equal total mass and units receive equal mass within their
source; a high-volume source therefore cannot define the purportedly shared interface direction. Form the module-local
matrix whose `m` rows are the `q_v`. Because every panel is centered and balanced, `sum_v q_v = 0`; this centroid
matrix has rank at most `m-1` without pretending that source- or unit-by-template interactions are shared interface
effects.

Define source deviation `u_sv = q_sv - q_v` and unit residual `r_zav = d_zav - q_sv`. Their energy, source
predictability, and spectra are diagnostics: large or structured deviations falsify the shared additive-interface model
rather than silently enlarging the primary nuisance basis. A separately named interaction-basis condition may stack
these deviations, but it has no `m-1` rank claim and cannot support the confirmatory shared-interface interpretation.

Pairwise differences remain diagnostics and shuffled/between-fact controls, not confirmatory covariance rows. An
incomplete prompt panel is excluded from the primary estimator. A separately named incomplete-panel experiment may
reconstruct centered interface effects with a preregistered graph least-squares estimator, but must prove invariance to
edge duplication and connected graph topology on synthetic fixtures before use.

### Step 2: nuisance basis

Calibration runs with stochastic layers disabled while preserving gradients. Every view in a unit uses identical image
tensors, padding, non-interface context, and deterministic execution state. This prevents dropout, augmentation, or
batching noise from being mislabeled as interface structure.

Compute the SVD/covariance of the `m` source-balanced template centroids `q_v` separately for every adapted module in a
deterministic sketch or exact module-local representation. Individual `d_zav` rows and interaction residuals may be
used only for diagnostics and the separately named interaction-basis condition. A single global sketch is prohibited
because module scale and dimensionality would make its geometry arbitrary. Estimate an orthonormal top-`k_l` basis
`U_l` for module `l`. The sketch seed, dimensionality, SVD backend, precision, sign convention, tie handling, and
module ordering are frozen in the condition.

`k_l` is not chosen from MMBU results. Candidate ranks and the selection statistic are fixed before calibration and use
only admitted training/development units. Source-grouped bootstrap intervals report the stability of principal angles.

With `m` complete-panel interfaces, the balanced centroid matrix has structural rank at most `m-1`; `k_l > m-1` is
invalid for the primary estimator regardless of the empirical spectrum. This ceiling does not apply to stacked
unit-by-template interaction residuals, which are not the primary estimator. For the optional incomplete-panel experiment, the observed
interface-pair graph must be connected over every interface claimed by the basis. Disconnected components are estimated
and named separately or rejected, and graph topology may not define the claimed leading directions.

### Step 3: frozen projection

Freeze every `U_l`. For each subsequent biomedical training gradient `g_l`, first compute the diagnostic projection

`g_quilt,l = g_l - lambda_l * U_l (U_l^T g_l)`

The confirmatory QUILT condition fixes `lambda_l = 1` for every admitted module. Values in `[0,1)` are permitted only in
a separately named dose-response ablation; they deliberately retain nuisance-span energy, cannot satisfy the complement
invariant below, and cannot support a quotient claim. This equation alone is not the applied-update rule. A
coordinate-wise preconditioner such as AdamW can rotate `g_quilt` back into `span(U_l)`.

The confirmatory optimizer is therefore projected SGD or linear scalar-momentum SGD. Its momentum state starts at zero,
is updated only from the fully projected gradient, and is projected before use; the final clipped/regularized parameter
step is projected again before application. Scalar global clipping and scalar weight decay preserve the complement.
Per-coordinate clipping, coordinate-wise decay, and unprojected auxiliary steps do not.

Post-projecting an Adam-style final step is not sufficient for the confirmatory quotient claim. Even if the applied
step lies in the complement, nuisance components can alter coordinate-wise first/second moments and thereby change the
allowed component of future steps. An Adam-style condition is exploratory, must separately receipt raw and projected
moment updates, and cannot support nuisance-independence or frozen-basis rotation-invariance. The optimizer state, raw
gradient, diagnostic projected gradient, preconditioned step, final projected step, and applied parameter delta are
separately receipted in every condition.

Every confirmatory `B_l` begins in the allowed complement and a post-step validator checks `U_l^T B_l` against the
registered numeric tolerance. A partial-`lambda` ablation instead reports its expected and observed nuisance energy and
does not run this pass/fail invariant. Optimizer moments may not be used as evidence that the parameter stayed in the complement. No nuisance basis
is recomputed after observing model-selection results. A frozen training-only probe measures basis drift; drift can
falsify the fixed-basis assumption but cannot trigger an adaptive refresh in the confirmatory run.

### Step 4: diagnostics

At each logged checkpoint report:

- per-module interface energy in the raw gradient and in the actual applied step;
- the ratio of shared-template-centroid energy to source-template-deviation and unit-template-residual energy,
  including source-group bootstrap intervals;
- retained gradient norm and cosine with the original gradient;
- per-module energy and update norm;
- calibration-to-training basis drift on a frozen training-only probe;
- source, class, and task-interface predictability from nuisance coefficients; and
- normal loss, not merely projected-gradient diagnostics.

Target-token normalization does not remove tokenizer or answer-length effects. The audit therefore includes
length-matched pairs, alternative approved serializers, and cross-source tests. If the learned basis is primarily
predicted by answer length, option position, or tokenizer segmentation, that is a diagnosed formatting basis—not yet
evidence of improved medical reasoning.

## Why interface differences are not automatically nuisance

The central assumption can be false. Grounding changes what the model must attend to; open and closed answers have
different uncertainty; coordinate generation and classification are genuinely different computations. QUILT therefore
uses “candidate interface nuisance” until four pre-training gates pass. It never assumes every paired difference should
be removed.

## Identifiability model and its limit

### Population identification proposition

The synthetic proof obligation starts from an additive local tangent model, not from a claim that neural networks obey
it globally. Let `s` identify a frozen independent source group. For unit/fact `(z,a)`, presentation interface `v`,
and module `l`, suppose

`g_szav,l = f_sza,l + n_v,l + u_sv,l + epsilon_szav,l`,

where `f` is the fact-bearing gradient, `n` is the shared interface component, `u` is a source-by-interface deviation,
and `epsilon` is a unit residual. Within-panel centering cancels `f`. The source-balanced template centroid equals

`q_v,l = (n_v,l - n_bar,l) + (1/|S|) sum_s (u_sv,l - u_bar_s,l) + e_v,l`,

where `e_v` is the equal-source average of within-source residual means. Therefore, under exact additive separation,
complete balanced panels, zero mean centered source deviations, and zero residual means, the row space of `Q = [q_v]`
is exactly the row space of the centered shared-interface matrix `N_c = [n_v - n_bar]`. This is the primary
identification statement; individual centered gradients need not have rank at most `m-1`.

The proof is the construction: within-panel centering removes `f`; equal unique-unit averaging produces each `q_sv`;
equal-source averaging produces `q_v`; and the two zero-mean assumptions remove the remaining source and residual
terms. The primary right-singular subspace is then the row space of `N_c` whenever its registered rank is correct.

### Approximate recovery and failure boundary

For approximate data, write `Q = N_c + E`, where `E` contains source deviations, residual means, and numeric/sketch
error. Recovery is stable only when `E` is small relative to the registered nonzero singular-value gap of `N_c`.
The implementation must report `||E||` proxies, the smallest retained singular value, and source-bootstrap projector
variation; it must reject rather than claim recovery when the preregistered perturbation bound is not met. The exact
finite-dimensional bound and norm are part of the synthetic proof and cannot be chosen after observing biomedical
gradients.

Projection onto the recovered row-space complement removes only the identified shared interface component. Source- or
unit-specific interactions are not automatically nuisance and are not promoted into the primary basis.

This does **not** prove recovery of the full medical signal. QUILT preserves only `P_N_perp f`. It is justified only if
the fact-bearing directions have bounded overlap with nuisance span `N`. The design must report principal angles and
energy overlap between same-fact mean-gradient directions, between-fact contrast directions, and candidate nuisance
directions on training-only probes.

The method is not identifiable from panels alone in either of these countermodels:

- **overlap:** a clinically useful fact direction lies inside `N`; projection necessarily deletes it;
- **interaction:** `g_szav = A_v f_sza + n_v`, so changing interface rotates or scales the fact gradient rather than adding
  separable nuisance.

Synthetic fixtures must demonstrate both failures. Biomedical execution must stop when overlap exceeds the registered
ceiling, template-centroid projectors are not stable across sources, or a multiplicative interaction model explains the
observations as well as the additive model. Held-out transfer is the final mechanism test; subspace recovery statistics
alone cannot validate the assumption.

## Pre-training gates

### QG-0: semantic equivalence

- Every primary calibration panel resolves to the same source atom and independent unit and contains the identical
  registered set of at least three strict prompt templates.
- Calibration/training and held-out-evaluation template identities are authored, medically reviewed where needed,
  frozen, and separated before any model run; no held-out template or paraphrase derivative enters basis estimation or
  biomedical training.
- Canonical prompt ancestors and paraphrase-generator lineage are grouped before the independent assignment of
  `basis_templates`, `audit_templates`, `train_templates`, and `validation_templates`; surface strings from one family
  cannot cross roles.
- Every audit unit has the same complete audit-template set, with at least one plus the largest prospectively permitted
  module rank in lineage-disjoint templates before any gradient is observed; otherwise cross-template subspace
  transport is underidentified and QUILT stops.
- Independent-unit and source-group assignment to `basis_fit`, `basis_audit`, `adapter_train`, and `validation` is
  frozen before any prompt view is generated; duplicate groups never cross roles.
- The admitted-data inventory contains enough complete panels and independent source groups to meet a prospectively
  justified precision plan; missing templates remove the whole unit rather than changing its weight.
- Human review of a prospectively sampled set finds no meaning change.
- Geometry pairs satisfy the frozen compatibility rule.
- Incomplete annotations never create count or absence equivalence.

Failure ends QUILT for the affected family.

### QG-1: low-dimensionality and stability

- Source-balanced template centroids, not stacked unit-level centered rows, define the primary spectrum; their projector is
  stable across source-group bootstrap samples.
- Source-by-template deviation and unit-by-template residual energy remain below their registered ceilings.
- Principal-angle stability exceeds the predeclared threshold across independent sources.
- On disjoint `basis_audit` units, centered gradients from never-fitted `audit_templates` meet the registered frozen-`U`
  energy-coverage floor while their mean fact-gradient overlap remains below the registered ceiling. No audit result
  may tune the basis or thresholds.
- The result is not explained by one prompt template, source, class, answer length, or target-token count.

Failure means there is no defensible nuisance subspace to quotient.

For every prospectively admitted module `l`, let `P_l = U_l U_l^T`. Apply the same complete-panel centering,
equal-unique-unit-within-source weighting, and equal-source weighting to the lineage-disjoint audit templates, producing
source-balanced audit centroids `q_audit,v,l`. Define

`coverage_l = sum_v ||q_audit,v,l P_l||_F^2 / sum_v ||q_audit,v,l||_F^2`.

Let `f_bar,sza,l` be each audit unit's mean gradient across its complete audit panel. Define the source-balanced
fact-overlap ratio

`overlap_l = mean_source(mean_unit(||f_bar,sza,l P_l||_F^2 / ||f_bar,sza,l||_F^2))`.

Zero or nonfinite denominators reject. Coverage floors, overlap ceilings, module inclusion, and the rule for combining
module decisions are frozen before audit gradients exist; a strong module cannot average away a failed required
module. The same ratios for rank- and removed-energy-matched random bases are mandatory QG-2 controls. These ratios
test transport and preservation only—they are not performance results and cannot tune `U`.

### QG-2: intervention specificity

The real complete-panel basis must differ from all of:

- a same-rank random orthonormal basis;
- a basis from shuffled independent-unit panels;
- a basis from between-fact pairs;
- a generic stochastic-gradient covariance basis; and
- a source-discrimination basis.

The random control is matched twice: once by per-module rank and once by expected removed-gradient energy. A scalar
gradient-shrinkage control matches QUILT's retained update norm without using any subspace. These distinguish interface
identification from generic regularization or a smaller effective learning rate.

If shuffled or between-fact controls perform equally, the method has not identified prompt-interface nuisance.

### QG-3: synthetic identifiability

On a synthetic model with known fact and interface features, QUILT must recover the planted interface subspace within a
registered principal-angle tolerance, preserve the fact direction, and remain invariant under permitted basis sign and
ordering changes. Adversarial fixtures include correlated fact/interface features, rank misspecification, unequal loss
lengths, zero gradients, and LoRA reparameterization attempts.

Only after QG-0 through QG-3 pass may any biomedical QUILT training run start.

## Comparator matrix

All conditions use the identical admitted units, views, fixed basis where applicable, target modules, rank, active
parameter count, optimizer budget, seeds, and evaluator.

| ID | Condition | Purpose |
|---|---|---|
| Q0 | Pooled fixed-basis LoRA with ordinary independently sampled view batches | Direct no-projection control |
| Q1 | Fixed-basis LoRA + PCGrad | Conflict-projection control |
| Q2 | Fixed-basis LoRA + CAGrad | Strong multi-objective control |
| Q3 | Fixed-basis LoRA + output/logit consistency | Cross-task consistency control |
| Q3-MV | Fixed-basis LoRA + synchronized equal mean of every view gradient in one unit's complete panel before each optimizer update | Direct R2F-style multi-view aggregation control; tests whether synchronized paraphrase averaging, without nuisance removal, explains transfer |
| Q3-P | Budget-matched paraphrase-robustness training, including a faithful LAP-style condition if implementable | Tests whether ordinary/adversarial paraphrase robustness explains held-out-template transfer without a gradient quotient |
| Q3-G | Fixed-basis LoRA + GERNE-style extrapolation where a valid less-biased ordering exists | Gradient-difference debiasing control |
| Q4-R | Fixed-basis LoRA + random same-rank projection | Rank-matched projection control |
| Q4-E | Fixed-basis LoRA + random energy-matched projection | Removed-energy control |
| Q4-S | Fixed-basis LoRA + scalar gradient shrinkage | Effective-step-size control |
| Q5 | Fixed-basis LoRA + shuffled-panel nuisance basis | Unit/panel-specificity control |
| Q6 | QUILT | Proposed condition |
| Q6-L | QUILT partial-projection dose response with prospectively fixed `lambda < 1` | Sensitivity analysis only; not a quotient or complement-preserving condition |
| Q6-A | QUILT basis + Adam-style state with final-step projection | Exploratory optimizer control; complement-preserving delta is not evidence of quotient or rotation invariance |
| B2 | Standard trainable-`A/B` shared LoRA | Competition-strength external control |
| B4 | MedQwen-style independent reproduction if feasible | Routed medical PEFT control |

Add Q4-E, an energy-matched random projection, and Q4-S, a scalar shrinkage condition with QUILT-matched retained update
norm. Match post-projection update norm only in those separately named controls; silently renormalizing QUILT would
change the method. Report wall time and peak memory because multiple per-view backward passes can erase its practical
value.

Q0 and Q3-MV use the same number of view-level forward/backward evaluations, target-token exposure, optimizer updates,
and total batch mass. Each Q0 update averages an independently sampled, source-balanced set of views; each Q3-MV update
uses the complete strict prompt panel for the same independent unit. If the sampler, loss, optimizer, or linear fixture
makes these two procedures exactly equivalent, the runner must report equality rather than count Q3-MV as an extra
winning/losing control. Q3-MV contains no gradient decoder and is called `R2F-style`, not a reproduction of R2F's
unlearning system.

## Evaluation

Primary scientific estimand: paired change on **held-out prompt templates for seen source-atom families with identical
target serialization**, using independent-unit group bootstrap and macro-source aggregation. “Held out” means the
medical training condition does not see that prompt mapping. If a preliminary serializer stage saw it, report that fact
and call the estimand held-out medical content, not held-out interface.

Mechanism evidence additionally requires that `U` fitted on `basis_fit` passes the frozen QG-1 diagnostics on disjoint
`basis_audit` units, including never-fitted `audit_templates`, and improves untouched `validation_templates` after being
applied only to `adapter_train` updates using `train_templates`. Results from a
full-admitted-data competition refit are submission evidence only, not independent validation of QUILT.

Open-to-closed, ungrounded-to-grounded, and box-to-mask transfer are secondary estimands because their targets or visual
carriers differ. They may be more competition-relevant, but they do not validate the strict additive nuisance claim.

Required secondary slices:

- held-out source;
- held-out source-interface combination;
- open versus closed and their paired delta;
- normal versus question-only, image swap, and geometry perturbation;
- malformed-output rate;
- base-relative negative flips on a separately admitted preservation set;
- per-task ordinary accuracy/score so consistency cannot hide consistently wrong predictions;
- calibration-basis source/class predictability; and
- parameters, active FLOPs, peak memory, step time, export bytes, and offline reload time.

No score from MMBU public data may choose `k`, `lambda`, modules, prompts, checkpoint, or condition.

### Validation access and multiplicity

Before any `validation` output is generated, freeze the complete confirmatory condition universe, eligible comparator
set, primary contrast vector, practical superiority/noninferiority margins, endpoint hierarchy, resampling units,
familywise confidence level, bootstrap count/seeds, missing/failure treatment, and deterministic decision function.
Faithful-but-unavailable comparators are marked `not implementable` with evidence before this freeze; they cannot be
dropped after results are seen. Q6-L, Q6-A, secondary transfer estimands, and descriptive slices are exploratory and
cannot rescue a failed confirmatory family.

Validation is opened once. One paired source-group bootstrap resample index is shared across every condition and
confirmatory endpoint so covariance is preserved. The preregistered max-statistic procedure produces simultaneous
familywise bounds for the complete contrast vector; a pointwise interval, the empirically strongest control, or a
post-hoc subset is not a promotion rule. Candidate labels supplied to the analysis step are masked, and the frozen
decision script emits the promotion decision before labels and descriptive outputs are unsealed.

Any model, checkpoint, margin, endpoint, comparator, rank, prompt, exclusion, resampling, or decision change after the
opening converts that validation population into development evidence. A new independent validation population is then
required for another confirmation claim. Re-reading the same validation outputs under a revised story is not a new
experiment.

## Promotion and falsification

QUILT is promoted over B2 only if all of the following hold under frozen rules:

1. QG-0 through QG-3 pass before biomedical training.
2. Its simultaneous lower paired source-group-bootstrap bounds exceed the practical margin over Q0, Q1, Q2, Q3,
   Q3-MV, and every frozen implementable Q3-P/Q3-G condition on the held-out-interface primary estimand.
3. Its simultaneous bound also exceeds or noninferiorly matches B2 on the competition-aligned aggregate under the
   registered rule.
4. The real complete-panel basis simultaneously beats Q4-R, Q4-E, Q4-S, and Q5; otherwise the causal interpretation
   fails.
5. Gains span multiple independent sources and are not confined to closed answers.
6. Visual dependence improves or remains within the registered noninferiority margin.
7. No material source, class, open-answer, context, malformed-output, or preservation regression occurs.
8. The artifact fresh-loads offline with no custom inference code and meets runtime limits.

Failure of items 2–4 retires the novelty claim even if an isolated score rises. Failure of item 8 retires QUILT as a
competition candidate but may leave a scientific negative result.

## Feasibility risks

- Complete-panel calibration requires at least `m` backward passes per admitted unit; whole-panel subsampling and the
  calibration compute ceiling must be frozen before gradients are observed.
- Gradient sketches may erase the very structure being estimated.
- Fixed-basis LoRA may be weaker than ordinary LoRA.
- Strict prompt-only equivalence may be too narrow to improve MMBU's larger open/closed and grounding gaps.
- Interface gradients may be entangled with legitimate visual reasoning rather than superficial formatting.
- A stable nuisance basis at initialization may drift during training.
- Teacher-forcing gradient agreement may not predict autoregressive inference behavior.
- Exact equivalent views may be too sparse after source admission.
- Strong generic controls may match QUILT, reducing novelty to a negative diagnostic result.

The first feasibility probe is therefore synthetic and CPU-sized. No full model is needed to learn whether the
estimator is algebraically correct and resistant to shuffled-panel controls.

## Honest prospective ratings

These ratings describe the design after the prior-art search, not achieved evidence.

| Dimension | Score / 10 | Ceiling reason |
|---|---:|---|
| Challenge fit | 4.0 | Prompt variation is secondary to the benchmark's visual grounding, localization, source shift, and image-reliance failures |
| Competition feasibility | 6.8 | Ordinary packaging is safe, but training overhead, fixed-basis capacity, and the optimizer handicap are unresolved |
| Competition-concept novelty | 3.5 | The basis-construction recipe is specific; the operator, adapter geometry, invariance logic, and paraphrase target have close antecedents |
| Paper-method novelty | 3.0 | Best framed as a rigorous negative/workshop study unless it produces a distinct image-reliant transfer result |
| Current evidence | 0.5 | Design and adverse search only; no estimator or model result |
| Package safety | 9.2 | Training-only method exports ordinary LoRA, pending actual loader test |

This is not the portfolio's stronger novelty candidate. It remains loader-safe and scientifically falsifiable, but the
exact mechanism must survive the QG controls before even a diagnostic biomedical run.

## Immediate no-training work order

1. Preserve the independent adverse review and literature map.
2. Add a multiplicative difficulty-scaling fixture and centroid-noise power check before any model execution.
3. Add supervised paraphrase-consistency, GPM/InfLoRA-style projection, and image-reliance controls.
4. Run only the CPU synthetic conformance suite after implementation review.
5. Do not schedule biomedical QUILT training unless every rejection gate passes and a higher-priority competition lane
   is already operational.
7. Do not implement or train until this design is reviewed against the Phase 1 contract.
