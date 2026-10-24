# Semantic-breadth source intake decision

**Date:** October 23, 2026
**Evidence class:** public primary metadata and repository review only
**Status:** prospective intake decision; no dataset archive, image, label row, model output, or MMBU example was opened

The MedMNIST repository resolved during this review to commit
`805b74237fb5bd2db376fd94e50646b6a8905d9d`. Zenodo record `10519652` reported version `3.0`, update time
`2024-11-28T10:48:59.998897+00:00`, and license identifier `cc-by-4.0`. Its public file metadata reported:

| File | Bytes | Published checksum |
| --- | ---: | --- |
| `pathmnist_224.npz` | 12,629,854,322 | `md5:2c51a510bcdc9cf8ddb2af93af1eadec` |
| `chestmnist_224.npz` | 3,889,293,042 | `md5:45bd33e6f06c3e8cdb481c74a89152aa` |
| `organamnist_224.npz` | 1,803,859,544 | `md5:50747347e05c87dd3aaf92c49f9f3170` |

These are identity candidates, not acquired artifacts. A future acquisition requires its own stronger authorization,
streamed SHA-256 receipt, byte cap, and exact active registry head. This prose file cannot substitute for a
`mmbu.phase1.decision_payload` or authorize any executable source priority.

## Decision

The next metadata-only source work should stop referring to “selected MedMNIST+ subsets” as one candidate. MedMNIST
is a wrapper over materially different upstream families, and wrapper membership cannot establish source
independence. The ordered intake frontier is:

1. **PathMNIST-224 / NCT-CRC** as the first non-ultrasound semantic-breadth candidate, conditional on recovering a
   slide- or patient-level parent for every retained patch;
2. **ChestMNIST-224 / NIH ChestX-ray14** as the fallback breadth candidate, conditional on patient-level grouping and
   a target policy that never treats absence of a text-mined label as a verified negative finding;
3. **OrganAMNIST-224 / LiTS-derived organ crops** as anatomy/context support only, conditional on CT-volume grouping
   and a shortcut audit; and
4. no other MedMNIST subset enters the first intake packet unless all three candidates above fail their declared
   gates and a successor decision documents why the replacement is stronger.

This ordering does not admit a source, authorize acquisition, grant a model-use purpose, or alter the requirement that
the first decision-bearing B1-L/B2-P portfolio contain BUS-BRA plus at least two independently admitted
semantic-breadth families. BUS-UCLM remains the preferred independent ultrasound replication candidate. PathMNIST is
the preferred modality-and-semantics breadth candidate. If either fails, the portfolio remains blocked rather than
silently counting the MedMNIST wrapper as a family.

## Why this is the smallest defensible portfolio

The answer-first competition ladder needs evidence that an adapter improves more than one acquisition source and does
not merely learn a breast-ultrasound shortcut. BUS-BRA supplies authoritative pathology, BI-RADS, and lesion geometry.
BUS-UCLM can test whether the learned behavior survives a separate breast-ultrasound collection. PathMNIST can add a
genuinely different modality and semantic vocabulary using native 224-pixel pathology patches.

That three-family structure is stronger than adding a second large but weakly grouped wrapper subset. It still cannot
identify the rejected broad MOSAIC factorization claim, and it does not prove hidden-benchmark generalization. Its job
is narrower: make the first B1-L/B2-P comparison interpretable across a source replication and a modality/semantic
shift.

## Candidate A — PathMNIST-224 / NCT-CRC

### Primary evidence

- The [MedMNIST repository](https://github.com/MedMNIST/MedMNIST) identifies PathMNIST as 100,000 training/validation
  patches from NCT-CRC-HE-100K and 7,180 test patches from CRC-VAL-HE-7K, exposes an exact source-image mapping CSV,
  and declares the non-Derma MedMNIST release CC BY 4.0.
- The [MedMNIST+ construction note](https://github.com/MedMNIST/MedMNIST/blob/main/on_medmnist_plus.md) states that
  PathMNIST-224 uses the 224-by-224 source images directly rather than upsampling the 28-pixel release.
- The [primary NCT-CRC Zenodo record](https://zenodo.org/records/1214456) describes 100,000 non-overlapping H&E patches
  from 86 slides and an independent 7,180-patch cohort from 50 patients with no patient overlap.

### Permitted target meaning

The only initial target is the source tissue class: adipose, background, debris, lymphocytes, mucus, smooth muscle,
normal colon mucosa, cancer-associated stroma, or colorectal adenocarcinoma epithelium. A tissue class is not a
patient diagnosis, stage, prognosis, or proof that a whole slide contains or lacks cancer.

### Admission gates

PathMNIST remains ineligible unless all of these hold:

1. every retained patch maps to the exact source filename and one defensible slide or patient parent;
2. no slide or patient crosses train, adaptive-development, or confirmation roles;
3. the published patch-random 9:1 NCT train/validation split is not used for a decision unless it independently proves
   parent disjointness; otherwise a prospectively frozen parent-grouped split is constructed from the source training
   population;
4. CRC-VAL-HE-7K stays unopened for confirmation until the recipe, checkpoint-selection rule, and thresholds are
   frozen;
5. the normalized and non-normalized NCT variants are treated as one upstream family and cannot cross roles;
6. the exact MedMNIST release, mapping CSV, source record, transformation, and all attribution obligations are bound;
7. a qualified review sample verifies that wrapper labels and source tissue semantics agree; and
8. cross-source exact/perceptual review checks the admitted population against every other candidate family before
   splitting.

Failure to reconstruct the parent key rejects PathMNIST for decision-bearing use. Patch count cannot substitute for 86
source slides.

## Candidate B — ChestMNIST-224 / NIH ChestX-ray14

### Primary evidence

- The [MedMNIST repository](https://github.com/MedMNIST/MedMNIST) describes 112,120 frontal radiographs from 30,805
  patients, preserves the source split, exposes source-image mapping, and identifies 14 text-mined finding labels.
- The [MedMNIST+ construction note](https://github.com/MedMNIST/MedMNIST/blob/main/on_medmnist_plus.md) states that
  the 224-pixel release resizes the 1,024-pixel source images.
- The [NIH ChestX-ray paper](https://arxiv.org/abs/1705.02315) documents report-mined image labels and the public NIH
  distribution; it does not turn those labels into adjudicated radiologist truth.

### Permitted target meaning

An observed positive source label may support a finding-label target after QA. Absence of a label is not a verified
negative and may not be converted to “normal,” “no finding,” or disease absence. Multi-label images require a frozen
serializer and cannot be silently collapsed to whichever label is convenient.

### Admission gates

ChestMNIST remains ineligible unless all of these hold:

1. the exact source mapping recovers a patient parent for every retained image and proves patient-disjoint roles;
2. a frozen inclusion rule handles multi-label rows without inventing negative labels or choosing labels after model
   output;
3. medical QA estimates positive-label correctness for every retained class and blocks classes that miss the frozen
   ceiling;
4. acquisition view and portable-device shortcuts are measured and retained as limitations rather than erased;
5. wrapper and upstream terms, attribution, challenge use, disclosure, and trained-weight release are reviewed
   separately; and
6. the 224-pixel resizing path passes an image-content and source-mapping audit.

ChestMNIST is a fallback, not a default. Its scale does not compensate for weak labels.

## Candidate C — OrganAMNIST-224 / LiTS-derived organ crops

### Primary evidence

- The [MedMNIST repository](https://github.com/MedMNIST/MedMNIST) states that OrganAMNIST is derived from abdominal CT
  volumes, uses 11 organ bounding-box labels, and assigns 115, 16, and 70 CT scans to train, validation, and test.
- The [MedMNIST+ construction note](https://github.com/MedMNIST/MedMNIST/blob/main/on_medmnist_plus.md) says the 224
  release uses center slices from the 3D organ boxes and resizes them to the target resolution.

### Permitted target meaning

OrganAMNIST may support anatomy or body-part/context supervision. It does not support disease diagnosis, pathology,
lesion presence, or clinical outcome. Axial, coronal, sagittal, and 3D variants are one upstream CT family and cannot
be counted as independent sources.

### Admission gates

1. every crop maps to one source CT volume and volume-disjoint roles are preserved;
2. all OrganMNIST views and dimensions are reconciled as one source family;
3. a frozen shortcut audit tests whether crop geometry, padding, or preprocessing identifies the organ without useful
   visual anatomy;
4. the context target is included only if it matches a requested field in the frozen context registry; and
5. wrapper and upstream transformation, rights, attribution, disclosure, and release obligations pass review.

OrganAMNIST cannot satisfy the semantic-family minimum by itself and cannot replace a disease-bearing source in the
primary task comparison.

## Explicit first-packet exclusions

| Subset | First-packet disposition | Reason |
| --- | --- | --- |
| BreastMNIST | Exclude | Same breast-ultrasound neighborhood, source grouping unresolved, and the wrapper merges normal with benign into one label. |
| DermaMNIST | Exclude | CC BY-NC 4.0 creates avoidable release ambiguity and no indispensable task cell. |
| TissueMNIST | Exclude | 236,386 cells come from only three reference specimens; cell count would grossly overstate independent support. |
| BloodMNIST | Exclude | Donor/group reconstruction is not established by the wrapper metadata, and normal-cell crops do not address the current spatial residual. |
| OCTMNIST | Hold | Strong disease semantics, but patient grouping and source-split reconstruction are not established by the current receipt. |
| PneumoniaMNIST | Hold | Pediatric chest-radiograph labels are attractive, but patient grouping and the center-crop/upsampling path need a stronger source receipt. |
| RetinaMNIST | Hold | Patient/eye grouping and ordinal-label semantics need a source-specific review. |
| OrganCMNIST / OrganSMNIST / OrganMNIST3D | Collapse | Same LiTS-derived upstream family as OrganAMNIST; useful as controlled views, never independent families. |

## Frozen role template

No actual role assignment occurs until each source is admitted, but the scientific freeze must use this template:

| Family | Earliest permissible role | Prohibited interpretation |
| --- | --- | --- |
| BUS-BRA | engineering, then train/adaptive development after full admission | single-source evidence of broad generalization |
| BUS-UCLM | held-out ultrasound family or confirmation, after full admission | extra BUS-BRA sample count or independent modality |
| PathMNIST / NCT-CRC | non-ultrasound breadth train or held-out family, after full admission | patient-level evidence when only patch IDs are known |
| ChestMNIST / NIH | fallback non-ultrasound breadth role | adjudicated disease absence or clean radiologist truth |
| OrganMNIST / LiTS | anatomy/context auxiliary role | diagnosis evidence or a second CT family from another view |

The final role assignment, source counts, seeds, and decision thresholds must be frozen through the repository's
decision-runner and opening-receipt process before any decision-bearing labels or outputs are opened.

## Stop rules

- Stop PathMNIST intake if the source mapping cannot produce complete parent groups.
- Stop ChestMNIST intake if positive-label QA or patient mapping fails; do not repair it with “no finding” negatives.
- Stop OrganAMNIST intake if anatomy is recoverable mainly from transformation artifacts or if its field is absent
  from the frozen context contract.
- Do not replace a failed candidate by silently selecting another MedMNIST subset. Issue a successor decision.
- Do not count wrapper datasets, alternate planes, resolutions, normalized variants, or derived task views as new
  independent source families.
- Do not acquire pixels or labels under this document. Acquisition and protected opening require their own active
  authorization, registry head, lock, and receipt.

## Evidence consequence

This decision improves source-search precision, not data readiness. The admitted-source count remains zero and the
project's empirical evidence score does not change. Its value is preventative: it blocks patch leakage, wrapper-family
inflation, noisy-negative invention, and anatomy-as-diagnosis before those errors consume review or GPU budget.
