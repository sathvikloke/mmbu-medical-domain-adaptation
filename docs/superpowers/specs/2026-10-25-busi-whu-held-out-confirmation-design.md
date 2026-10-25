# BUSI-WHU held-out Track 2 confirmation design

**Date:** October 25, 2026  
**Status:** accepted design direction, blocked from execution until every admission and freeze input exists  
**Purpose:** turn the replicated Qwen3.5-9B development response into one honest, prospectively sealed held-out-source Track 2 test

## Intent

The replicated BUS-BRA plus PathMNIST development screen found a large base-relative task response for Qwen3.5-9B and no stable response for Qwen3.5-4B. The next useful result is not another development run. It is a prospectively frozen test on a source family that did not train or select the recipe.

BUSI-WHU v3, DOI `10.17632/k6cpmwybk3.3`, is the preferred confirmation prospect. Public metadata reports 927 benign or malignant breast-ultrasound images, segmentation data, a patient-information workbook, and CC BY 4.0. Its archive, patient rows, images, labels, and masks have not been acquired or opened in this project. Public metadata is identity evidence only and cannot establish admission.

BUS-UCLM is rejected as the clean confirmation family because its `INFO.csv`, label totals, 38 patient identifiers, and label-set frequencies were opened and recorded before this design. It can support later metadata-aware exploratory work, but not the sealed claim below.

This design does not admit BUSI-WHU, approve its labels, authorize acquisition, or authorize execution. It defines what must be frozen if every gate passes.

## Claim boundary

The only primary scientific claim is:

> For the three fixed training seeds named here, the frozen Qwen3.5-9B dual-objective family improves patient-balanced BUSI-WHU task accuracy over the unchanged Qwen3.5-9B base by more than five percentage points at the frozen one-sided 90% patient-resampling bound.

This claim is conditional on these three fixed seeds. Patient resampling does not establish generalization over arbitrary training seeds.

Allowed secondary claims are limited to source-specific task accuracy, strict context validity, context-field score, `Q = 0.8T + 0.2C`, per-seed task delta, class-conditioned diagnostics, output-failure rate, runtime, and memory on this exact source and condition.

The result cannot establish MMBU performance, official-harness equivalence, clinical utility, calibration, localization quality, cross-modality generalization, or a final winning checkpoint. BUSI-WHU masks are not used in the primary task or context score.

## Frozen candidate family

- Base: `Qwen/Qwen3.5-9B` at revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
- Recipe: the exact dual-objective language-LoRA recipe from `config/phase1/replicated-response-screen-2026-10-25.json`.
- Replication seeds: `20261025`, `20261026`, and `20261027`.
- Trainable scope: language-model `q_proj` and `v_proj` only, rank 8, alpha 16, dropout 0.
- Training exposure: 1,024 optimizer updates per seed using only the frozen BUS-BRA and PathMNIST training roles.
- Base and adapted inference use the same processor, prompt, decoding, batching, precision, device class, and evaluator.

The adapters produced by the October 25 response screen remain exploratory because their source-admission flags are false. They cannot enter confirmation or release. After BUS-BRA and PathMNIST are validly admitted for `train`, the three checkpoints must be trained again from the pinned base under new authorized experiments using the unchanged recipe, seeds, ordered training population, and update count. Those runs must emit complete model lineage and reproducibility evidence. Matching the old development scores is not required, and the old checkpoints cannot substitute for a failed replay.

The newly authorized checkpoints form one fixed recipe family. No best seed is chosen from confirmation. Seed `20261025` is the prospectively designated release candidate if and only if the family-level confirmation passes. Seeds `20261026` and `20261027` support the fixed-family claim and can never replace it based on confirmation performance.

Qwen3.5-9B also requires a reviewed successor native-model/runtime gate. The binding B1 runtime gate names Qwen2.5-VL-7B and cannot be reused by analogy.

If any model revision, recipe literal, training population, record order, update count, seed, prompt, evaluator, or runtime changes, this design no longer applies.

## Protected source intake

Before archive acquisition, a BUSI-WHU-specific acquisition authorization, inventory rule, converter, exclusion rule, grouping rule, and custody lock must be frozen under the Phase 1 contracts. Protected inventory opening then emits the exact eligible-population manifest. Only after that manifest exists may the immutable QA sampling plan be derived from its named population and frozen. A separate QA lock and opening receipt must exist before any sampled content is reviewed.

The deterministic exclusion rule is fixed before protected access:

- reject a record with no immutable image identity;
- reject a record with no workbook-linked patient parent;
- reject a record whose source label is not exactly benign or malignant under the reviewed ontology;
- reject an ambiguous image-to-patient or image-to-label join;
- quarantine every unresolved exact or perceptual cross-source collision group;
- reject unreadable or dimension-invalid image bytes;
- never require a mask for the classification endpoint and never infer a task label from a mask.

Every exclusion and its reason remain in the eligible-population manifest. No observed class count, patient count, image appearance, model output, or score may change these rules.

## Confirmation population

The population is every eligible BUSI-WHU v3 patient admitted to the `confirmation` role. Each patient is one independent unit. Every eligible image for that patient stays attached to the patient and contributes to the patient-level mean. Patients, not images, receive equal primary weight.

The final population digest, patient count, record count, patient-to-record map, source artifact manifest, exclusions, and duplicate disposition must be frozen before the first model output. At least 60 independent eligible patients are required. This conservative operational floor is fixed while the patient count remains unknown; it prevents a degenerate few-parent bootstrap but is not represented as a formal power guarantee. A CPU-only sensitivity artifact using synthetic paired outcomes must be frozen before protected acquisition and record how the interval behaves at the 60-patient floor across prespecified effect and variance scenarios. If fewer than 60 eligible patients remain, the result is `underpowered` and exploratory only. The project may not search for or substitute another confirmation source in response.

The population cannot include BUS-BRA, MedMNIST, MMBU, a BUSI-WHU derivative used for development, or any patient whose role or label was changed after the lock.

## Exact prompt and parser contract

Task prompt bytes are the UTF-8 encoding of:

```text
What is the breast ultrasound classification? Respond with exactly one label: benign or malignant.
```

Task parsing removes only Unicode whitespace at the two ends and applies Unicode case folding. The result must be exactly `benign` or `malignant`. No prefix removal, punctuation removal, synonym mapping, answer extraction, JSON repair, fuzzy matching, or retry is allowed.

Context prompt bytes are the UTF-8 encoding of:

```text
Return one raw JSON object with exactly these keys in this order: body_part, medical_domain, modality. Use lowercase strings and no other text.
```

The sole valid context object is:

```json
{"body_part":"breast","medical_domain":"breast imaging","modality":"ultrasound"}
```

The parser rejects duplicate keys, unknown keys, missing keys, alternate key order, non-string values, alternate capitalization, Markdown fences, commentary, trailing text, leading text, and multiple objects. There is no value normalization.

These coarse source-level context fields test the output contract. They do not establish lesion grounding or clinical reasoning.

Task and context inference are separate fresh calls. They never share conversation state, KV cache, output text, grade, target, or hidden metadata.

## Primary estimand

For each patient and condition, compute the exact mean task grade across that patient's retained images. For each adapted seed, subtract the unchanged-base patient mean from that seed's adapted patient mean. The primary point estimate is the equal-weight mean of those paired patient deltas across all patients and the three fixed seeds.

All divisions use the repository's canonical reduced rational representation. Every output failure stays in the denominator as zero. No failed image, patient, seed, or condition is retried, replaced, or dropped.

## Frozen patient-resampling calculation

- Resampling unit: patient.
- Pairing: base and all three adapted seeds use the same patient draw indices.
- Draw count: 10,000.
- Bootstrap seed: `20261025`.
- PRNG: Python `random.Random`, with the exact interpreter version and implementation digest frozen in the runtime contract.
- Patient order: ascending UTF-8 bytes of the immutable patient ID.
- Each draw samples the original patient count with replacement from integer positions in that order.
- Record-level images are never independently resampled.
- The 10,000-by-N integer index matrix is generated and RFC 8785 serialized before any model output, hash-bound into the confirmation lock, and reused unchanged for every condition and endpoint.
- Each draw's statistic is the equal-patient, equal-seed mean paired task delta using exact rational arithmetic.
- Sort the 10,000 exact draw estimates by rational value, retaining generation order for ties.
- The one-sided 90% lower bound is the zero-based element at index `999`, equivalent to the nearest-rank 0.10 quantile for 10,000 draws.

No binary floating-point interpolation enters the primary estimate, bound, comparison, or decision.

## Frozen sensitivity analysis

A paired sign-randomization check is diagnostic and cannot rescue the primary rule:

- use the same patient-level seed-mean paired deltas;
- generate 10,000 independent patient sign vectors with `random.Random(20261026)`;
- serialize and hash the sign matrix before model output;
- compute the exact mean signed delta for every vector;
- report one-sided `p = (1 + count(null_statistic >= observed_statistic)) / 10001` as a canonical rational.

## Decision rule

The family passes only if all of these are true:

1. each of the three seed-specific patient-balanced task deltas is strictly positive;
2. the primary point estimate is strictly greater than `0.05` absolute accuracy;
3. the one-sided 90% patient-resampling lower bound is strictly greater than `0.05`;
4. the paired sign-randomization diagnostic is reported unchanged but does not alter the decision;
5. the base condition and every adapted condition complete exactly once, preserve every row, and pass fresh-process offline equality;
6. no source, population, prompt, target, model, adapter, runtime, seed, resample matrix, or evaluator identity drifts.

Failure of any decision-bearing item records `confirmation_failed`. It cannot be rescued by another seed, checkpoint, threshold, source, prompt, parser, bootstrap choice, or retry.

## Base and adapted execution

The unchanged base is evaluated once because greedy decoding, requests, processor state, and runtime condition are identical across the three paired comparisons. A second fresh process must reproduce every base raw prediction byte-for-byte before the base becomes eligible.

Each adapted seed is evaluated once, exported, and reloaded in a fresh offline process. Its complete raw prediction set must match byte-for-byte after reload. The same single eligible base output is paired with each seed. A per-seed base rerun is prohibited because it would add attempts without changing the frozen deterministic condition.

## Secondary outputs

Secondary interpretation occurs only if the primary rule passes. For each condition, `T` is the exact equal-patient mean task grade. For each image, the context grade is the exact mean of the three binary field grades; `C` is the exact mean of those image context grades within each patient and then the exact equal-patient mean across patients. The adapted family reports the exact equal-seed mean of each endpoint. `Q = (4/5)T + (1/5)C` is computed only from those exact rational endpoints.

1. report whether dual-objective mean `Q` exceeds unchanged-base mean `Q`;
2. strict context validity and each requested-field score are reported per seed and in the seed mean;
3. for each class, compute image correctness within every patient containing at least one image of that class, then equally average those patient-class means;
4. report contributing patient and image counts for benign and malignant separately;
5. report class-balanced accuracy as the exact mean of the two class-conditioned patient scores.

These secondary outputs are descriptive. They cannot rescue or block the primary result. The multiplicity family contains one hypothesis, so its method is `none` at alpha 0.10.

## One-opening and failure policy

The confirmation lock, resample-index artifact, sign-index artifact, execution condition, and opening receipt must exist before the first BUSI-WHU model output. There is one attempt per condition. Scheduler rejection before process start does not consume an attempt. A started process consumes its attempt.

No automatic retry is permitted. Mechanical failures remain evidence. A repair after opening creates a new exploratory lineage and cannot preserve the confirmation claim. Confirmation data cannot return to development, recipe selection, threshold setting, prompt revision, or seed selection.

## Admission and execution gates

Execution is blocked until all of these are real, validated records rather than prose:

1. BUS-BRA and PathMNIST are approved for `train`, with active purpose authorizations, exact split manifests, and complete lineage for every training record;
2. the Qwen3.5-9B successor runtime contract is reviewed and passes its native load, training, save, reload, and offline gates;
3. the three adapted checkpoints are replayed from the pinned base after authorization and receive complete model-lineage records whose effective purpose survives into confirmation;
4. immutable BUSI-WHU v3 acquisition authorization, artifact manifest, and checksums;
5. human rights review for acquisition, confirmation, challenge use, disclosure, and trained-weight release;
6. complete patient grouping and image-label join;
7. clinical and visual QA under a sampling plan derived from the closed eligible-population manifest, then frozen under a separate QA lock before sampled content review;
8. cross-source exact and perceptual duplicate review;
9. approved BUSI-WHU source record whose allowed purposes include `confirmation`;
10. active BUSI-WHU confirmation purpose authorization and registry head;
11. closed eligible-population and confirmation split manifests;
12. hermetic decision receipt selecting this exact recipe and designated release seed without MMBU content;
13. prospective lock, opening receipt, resample/sign artifacts, execution condition, and reproducibility identities.

Any missing or blocked gate stops execution. The system must name the exact absent record. It must never replace a missing value with a guess.

## Implementation boundary

The next software package implements only:

- a closed confirmation-manifest validator;
- exact patient-balanced grading and the frozen resampling estimator;
- the sign-randomization diagnostic;
- the deterministic decision function;
- synthetic positive and adversarial fixtures;
- a readiness command that reports exact missing records in deterministic order;
- an execution-envelope validator that refuses protected access or inference unless every gate validates.

It does not acquire BUSI-WHU, open biomedical content, load model weights, submit a scheduler job, train, produce confirmation output, upload, or submit to MMBU.

## Why this is the right next move

The development evidence already separates the 9B and 4B routes. More BUS-BRA or PathMNIST development training would measure the same source mixture again. A sealed BUSI-WHU patient population tests the failure mode that matters: whether the gain survives a new clinical collection instead of source-specific regularities.

A preserved failure would be useful. It would stop a weak Track 2 story before submission and prevent us from confusing a large development delta with generalization.
