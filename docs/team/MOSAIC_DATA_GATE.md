# MOSAIC data-identifiability gate

**Status:** pre-acquisition research screen; no source is approved by this document  
**Date:** October 17, 2026  
**Decision:** the current source pool cannot yet validate the MOSAIC mechanism claim

## Why this gate exists

MOSAIC proposes reusable modality, specimen/scale, and task-geometry adapter factors. That claim is invalid if each
factor is merely another name for a dataset. For example, microscopy-only localization and radiology-only
classification would let a router learn source appearance while appearing to learn task geometry. More examples from
the same confounded cells do not repair the design.

This gate precedes model training. It is separate from rights, challenge eligibility, biomedical validity, and software
correctness; all of those gates still apply.

## Required frozen table

Before comparative outputs are opened, create one row per independently grouped unit with:

- exact source, release, source family, and upstream parent;
- independent group ID and grouping basis;
- modality and submodality;
- specimen/anatomy and biological scale;
- task geometry: `global_recognition`, `region_conditioned_recognition`, or `coordinate_localization`;
- annotation origin and whether it was human, algorithmic, caption-derived, or mask-derived;
- conversion version and target vocabulary;
- rights, purpose, overlap, QA, and release decision digests; and
- the prospectively assigned train, external-development, held-out-combination, or held-out-source role.

Unknown values remain `unknown`; they are never inferred from filenames or filled to improve coverage.

## Mechanical preconditions

The claim-validating population must satisfy all of these before G0 can authorize biomedical work:

1. Every factor value in a held-out combination occurs in training, while that exact joint combination does not.
2. Every claimed task-geometry value occurs in at least two modality classes and two source families.
3. Every claimed modality value occurs with at least two task-geometry values.
4. After removing declared reference levels, both the additive three-axis matrix and the preregistered matrix with
   source-family fixed effects have full column rank for the factor contrasts being claimed.
5. No factor level maps one-to-one to source family.
6. At least four nonempty joint combinations are prospectively held out, unless a written design review narrows the
   claim before results exist.
7. Cell sizes are counted in independent groups. Crops, questions, panels, augmentations, and transformed copies do not
   create additional independent units.
8. One entire eligible source family remains unopened for one-time confirmation after recipe selection.
9. The factor-support graph remains connected after removing any one development source family; a single bridge source
   cannot create the only apparent crossing.

If any item fails, run only the shared baseline or label factor routing an engineering probe. Do not substitute a random
row split and retain the compositional-generalization claim.

## Current evidence map

| Candidate | Useful coverage | Independence/rights state | MOSAIC role today |
|---|---|---|---|
| BBBC039 v1 | fluorescence microscopy; counts and mask-derived boxes | BBBC family; CC0 statement recorded; conversion and model-use approval pending | Quarantine engineering evidence only; one family cannot validate task transfer |
| ROCOv2 2.0.1 | varied medical figures and modality metadata | PMC-literature family; aggregate CC BY-NC 4.0 and item-level figure/release questions unresolved | Candidate for reviewed global/context examples, not approved |
| PMC-VQA | figure VQA | Same PMC-literature family as ROCO; shared PMCIDs recorded; images absent and rights/use pending | Does not add an independent family merely by using another release |
| MedMNIST+ | many modalities/specimens with standardized classification labels | Newly screened candidate; official site states CC BY 4.0 except DermaMNIST CC BY-NC 4.0; subset lineage, source splits, MMBU proximity, resolution, and release review pending | Promising Phase-A classification coverage; cannot validate spatial transfer alone |
| BBBC038 v1 | heterogeneous nuclei images with instance masks | Newly screened candidate; official BBBC page states CC0; BBBC-family dependence and source overlap require review | Could test microscopy localization robustness, not independent-family transfer |
| VinDr-CXR v1.0.0 | radiology classification and radiologist boxes | Newly screened candidate; credentialed PhysioNet Health Data License; user access and public-weight compatibility unestablished | Potential second-modality spatial source only after credentials and review |
| BUS-BRA 1.0 | breast ultrasound classification, BI-RADS, pathology, and lesion masks | Newly screened priority candidate; public record reports CC BY, 1,875 images from 1,064 patients, and standardized folds; exact terms/schema/group joins uninspected | Strongest metadata-only dual global/spatial candidate; not admitted |
| BUS-UCLM v3 | breast ultrasound labels and expert lesion masks | Newly screened priority candidate; Mendeley reports CC BY 4.0 and the paper describes 683 images from 38 patient-linked studies | Independent global/spatial family candidate; not admitted |
| BUSI-WHU v3 | breast ultrasound benign/malignant images and prospective segmentation | Mendeley reports CC BY 4.0, 927 images, an archive, and patient-information workbook; authoritative image-mask-patient join unverified | Conditional third ultrasound family; intake only after higher-priority sources |

Primary public evidence for the newly screened candidates: [MedMNIST v2](https://medmnist.com/v2),
[BBBC038](https://bbbc.broadinstitute.org/BBBC038), and
[VinDr-CXR](https://www.physionet.org/content/vindr-cxr/1.0.0/). The prioritized global/spatial ultrasound candidates
and their exact admission blockers are recorded in the [prospective source portfolio](DATA_SOURCE_PORTFOLIO.md). A website statement is screening evidence,
not authorization. No bytes were downloaded during this screen.

The [provisional source–factor incidence audit](SOURCE_FACTOR_INCIDENCE_AUDIT.md) stress-tests an optimistic version of
this map. Even after granting conditional task capabilities, its three-axis main-effect scaffold has rank 5 of 7
because modality and specimen are perfectly paired; adding source-family effects yields rank 8 of 12. These are not
admitted-data measurements, but they prove the current portfolio shape cannot validate the broad mechanism claim.
The follow-on [crossover-source search](CROSSOVER_SOURCE_SEARCH.md) identifies paired MRI/ultrasound SegThy and
restricted ultrasound/mammography BCMID as the highest-leverage repairs. Even granting both optimistically improves but
does not close the rank deficiency.

## Staged decision

### Phase A: factorization sanity check

If selected MedMNIST+ subsets pass source admission, use only source-provided training partitions and create grouped
external development splits without opening source validation/test material unless separately authorized. This phase
may test modality/specimen routing and source confounding. Because every task remains global classification, it cannot
support the spatial-transfer or full MOSAIC claim.

### Phase B: crossed spatial evidence

Admit spatial supervision in at least two modality classes and two independent families. BBBC039 plus BBBC038 is still
one conservative family. BUS-BRA and BUS-UCLM create a more plausible ultrasound route than relying only on VinDr-CXR,
but neither is admitted and same-modality family count does not by itself prove the full crossed design. If no eligible
cross-modal alternative exists, remove spatial factor reuse from the primary novelty claim rather than disguising the gap.

### Phase C: untouched confirmation

Freeze the winning recipe, route taxonomy, conversions, thresholds, and checkpoint before opening the confirmation
family. A failed confirmation is retained and reported; it is not converted into another development set.

## Required audit outputs

The data owner must return:

1. the frozen incidence table and its digest;
2. matrix rank and empty-cell report;
3. source-family/factor contingency tables;
4. independent-group counts per joint cell and split;
5. exact held-out combinations and proof each marginal factor appears in training;
6. exact source-family confirmation holdout;
7. rights, purpose, lineage, overlap, grouping, conversion, QA, and release decisions; and
8. a signed pass/fail statement for each mechanical precondition above.

Until those artifacts exist, the honest data-feasibility score remains **5.0/10**. The portfolio-level structural gate
is a provisional fail; the exact admitted-data gate remains not evaluated. Better prose does not raise either result.
