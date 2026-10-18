# Base-conditional preservation ablation

**Date:** October 17, 2026  
**Role:** optional B2 ablation; not a flagship novelty claim  
**Decision:** test only after the ordinary B2 and no-KL controls are frozen

## Hypothesis

Unconditional behavior retention can preserve base-model errors, while ordinary supervised fine-tuning can overwrite
responses the base already gets right. On admitted external training records, condition the target on a frozen base
receipt:

- if the base response is deterministically judged correct and valid, preserve its output distribution or canonical
  valid response within a small registered coefficient;
- otherwise, train on the authoritative source target; and
- never infer correctness from confidence, fluency, a rationale, or agreement with another model.

The hoped-for competition effect is fewer negative flips without suppressing useful adaptation. This is a testable
recipe choice, not a claim that base correctness transfers to MMBU.

## Prior-art boundary

This direction is not highly novel. [S3FT](https://aclanthology.org/2025.findings-naacl.349/) already selects a model's
correct responses as self-supervised targets and uses gold targets otherwise. [Positive-Congruent Training](https://openaccess.thecvf.com/content/CVPR2021/papers/Yan_Positive-Congruent_Training_Towards_Regression-Free_Model_Updates_CVPR_2021_paper.pdf)
directly targets negative flips during model updates, while [Margin Preserving Training](https://doi.org/10.1609/aaai.v40i11.37825)
uses margin calibration and distillation. [Every Sample Counts](https://arxiv.org/abs/2607.08968) imposes pointwise
fine-tuning constraints with learned sample-dependent relaxation, and [Beyond Average Safety](https://arxiv.org/abs/2609.29960)
uses reference-relative chance constraints to control tail regressions. Ordinary knowledge distillation and learning-
without-forgetting are broader antecedents.

The MMBU-specific contribution, if useful, is only the controlled combination of typed task judges, visual-dependence
eligibility, exact serializer validity, and a base-relative promotion objective. Rate this as competition engineering,
not paper-method novelty.

## Frozen partition

For every admitted external training record, run the pinned B0 once under the exact prompt, image, serializer, and
decoding contract. Store immutable raw output, parsed output, validity diagnostics, judge version, and hashes. Assign:

- `PRESERVE_ELIGIBLE`: valid and source-authoritatively correct;
- `LEARN_TARGET`: valid or invalid but source-authoritatively incorrect;
- `UNJUDGED`: no deterministic task judge or ambiguous authoritative target; and
- `REJECTED`: invalid source/purpose/geometry/grouping record.

Open-ended semantic equivalence is not guessed. An `UNJUDGED` record follows ordinary supervised B2 or is excluded by
the frozen manifest; it never enters the preserve set.

## Visual-dependence eligibility

A correct answer can be a language shortcut. Preservation is allowed only when the source contract supports the
applicable normal-image and answer-changing paired-image check. Blank-image degradation alone is insufficient. Where
per-record visual dependence cannot be established without an invalid intervention, preservation remains a named
ablation and cannot be described as preserving grounded competence.

## Conditions

All conditions use the same B2 profile, draw budget, task/source mass, optimizer family, checkpoint openings, and
compute accounting:

| ID | Correct-base records | Incorrect-base records | Purpose |
|---|---|---|---|
| P0 | authoritative target | authoritative target | Ordinary B2 |
| P1 | unconditional frozen-base KL | authoritative target plus same KL rule | Existing generic retention control |
| P2 | frozen-base token distribution or valid base response | authoritative target | Base-conditional preservation |
| P3 | randomly permuted preserve/learn flag within source × task | authoritative target under permuted flag | Tests whether gating or sample weighting explains a gain |

P2 must have a target-token-loss-matched control if replacing a shorter gold response with a longer base response
changes supervised-token exposure. If native logits cannot be stored safely and reproducibly, use canonical valid text
targets and label the condition self-targeting rather than logit preservation.

## Promotion and kill rule

P2 is eligible only if, on frozen held-out sources and shared paired group-bootstrap resamples, it:

1. reduces base-relative negative flips versus P0;
2. does not reduce positive flips or total task score beyond the frozen practical margin;
3. beats P1 and P3, not merely P0;
4. preserves normal competence and answer-changing visual target tracking;
5. introduces no task/source/open-answer regression, malformed output, or package/runtime failure; and
6. survives the one-time untouched confirmation rule already bound for B2.

Failure on any conjunct retains P0/P1 and rejects the mechanism story. No public MMBU response can define the
partition, coefficient, checkpoint, or promotion decision.

## Honest rating

| Dimension | Score / 10 | Reason |
|---|---:|---|
| Competition upside | 8.4 | Directly targets regressions that reduce base-relative adaptation value |
| Current readiness | 6.0 | Judges and receipt concepts exist, but no native B0 partition or logits exist |
| Implementation feasibility | 7.8 | Loader-safe training-only change, but teacher storage and token exposure need care |
| Method novelty | 2.5 | S3FT, positive-congruent/margin training, pointwise constraints, chance constraints, and distillation own the central idea |

This ablation strengthens B2's decision quality. It does not raise the project's novelty score.
