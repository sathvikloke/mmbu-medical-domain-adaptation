# QUILT independent adverse review and disposition

**Reviewed:** October 17, 2026  
**Decision:** remove QUILT from flagship status; retain only as a gated diagnostic/negative-result branch

## Why the decision changed

An independent Claude Opus review was asked to reject rather than encourage the method. Its claims were then checked
against the written QUILT specification and primary literature. The review did not discover that the specification had
ignored multiplicative interactions, task-gradient overlap, consistency training, or basis drift: those were already
explicit rejection gates or controls. It did, however, expose a more important portfolio error. A method whose most
likely honest outcome is to trigger its own rejection gates is not a strong flagship competition idea merely because
those gates are rigorous.

The closest-work search also found a direct 2026 medical-VLM antecedent that the prior audit had missed:
[Mechanistically Guided LoRA Improves Paraphrase Consistency in Medical Vision-Language Models](https://proceedings.mlr.press/v333/sadanandan26a.html).
It trains medical-VLM LoRA with paraphrase consistency plus supervised accuracy. Its companion analysis,
[Consistent but Dangerous](https://arxiv.org/abs/2603.20985), reports that lower paraphrase flip rates can coincide with
loss of image reliance. Prompt consistency is therefore neither a new medical-VLM target nor a safe proxy for visual
medical competence.

## Findings accepted as material

1. **Definitional identification is not causal nuisance identification.** Under the stated additive decomposition,
   centering recovers the template main effect because the model defines that effect as the centered template mean.
   This does not establish that the recovered direction is dispensable rather than task-bearing.
2. **Loss-scale interactions can contaminate the basis.** For cross-entropy, prompt-specific confidence can scale a
   unit's task gradient. After within-unit centering, this multiplicative component can remain aligned with the fact
   gradient. The existing interaction and overlap gates catch this only by stopping QUILT; they do not repair it.
3. **On complete training panels, the incremental mechanism is weak.** Synchronized mean-gradient training already
   averages the prompt views. QUILT adds a fixed orthogonal constraint whose benefit must come from transfer to
   unpaired, lineage-disjoint train/validation templates. That is an unproved extrapolation, not a consequence of the
   additive proposition.
4. **Fixed projection is parameter-space and trajectory local.** The frozen complement constraint is exact in the
   selected LoRA-FA coordinates, but it is not function-space prompt invariance. A basis estimated at initialization can
   become stale along training.
5. **The prior-art bundle is closer than previously scored.** Freezing `A` and training `B` is
   [LoRA-FA](https://arxiv.org/abs/2308.03303); fixed SVD-basis orthogonal updates are structurally adjacent to
   [GPM](https://openreview.net/pdf?id=3AOj0RCNC2) and
   [InfLoRA](https://openaccess.thecvf.com/content/CVPR2024/html/Liang_InfLoRA_Interference-Free_Low-Rank_Adaptation_for_Continual_Learning_CVPR_2024_paper.html);
   gradient agreement/invariance is established by
   [AND-mask](https://openreview.net/pdf?id=hb1sDDSLbV),
   [Fish](https://openreview.net/pdf?id=vDwBW49HmO), and
   [Fishr](https://proceedings.mlr.press/v162/rame22a.html); null-space removal is established by
   [INLP](https://aclanthology.org/2020.acl-main.647/); and same-fact paraphrase-gradient aggregation is already present
   in R2F. QUILT's remaining distinction is the controlled basis-construction recipe, not the optimizer operator.
6. **Competition targeting is secondary.** The current MMBU evidence prioritizes visual grounding, localization,
   source/modality shift, open-answer behavior, and text-only shortcuts. QUILT primarily attacks strict wording changes.

## Review claims not accepted without qualification

- The additive countermodel, task-overlap check, basis drift probe, output-consistency baseline, and lineage-transfer
  test were already present. Their absence is not a defect in the document.
- Re-estimating the basis every `K` steps would destroy the clean frozen-basis claim and introduce an adaptive choice;
  it is not adopted as an automatic repair.
- Cosine-normalizing every view before centering can itself prevent cancellation of the shared fact direction. It may be
  studied only as a separately named condition, not silently substituted into the estimator.
- AdamW plus final-step projection does not reproduce quotient-independent optimizer state. It may be a competition
  control, not evidence for the original mechanism.

## Binding disposition

- QUILT is no longer the primary novelty branch or the best-current-idea entry in the scorecard.
- No biomedical QUILT run starts before the existing synthetic and interaction gates, a registered centroid-noise power
  check, and a direct comparison against paraphrase augmentation plus supervised consistency.
- A QUILT result must include normal-image, image-absent, and image-swap dependence. Improved prompt consistency with
  unchanged or worse image reliance is a failure.
- PCGrad/CAGrad remain optional context controls; GPM/InfLoRA-style projection, supervised consistency, and R2F-style
  mean gradients are the stronger mechanism controls.
- The branch is valuable as a rigorous negative study of whether prompt-gradient nuisance transports across template
  families. It is not currently justified as the competition centerpiece.

## Revised evidence scores

| Axis | Score / 10 | Reason |
|---|---:|---|
| Competition idea | **4.0** | Loader-safe and falsifiable, but aimed at a likely secondary failure mode and liable to reject itself |
| Concept novelty | **3.5** | The basis recipe is specific; the operator, adapter geometry, invariance logic, and paraphrase objective have close antecedents |
| Paper-method novelty | **3.0** | Could support a rigorous negative/workshop study, not presently a distinct methods-paper contribution |

These scores are judgments under current evidence, not Claude's scores copied into the project. They can rise only after
a preregistered result demonstrates image-reliant held-out-template benefit beyond the stronger direct controls.
