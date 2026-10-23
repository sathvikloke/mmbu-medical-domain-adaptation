# Crossover-source repair search

**Observed:** October 17, 2026  
**Evidence class:** public primary metadata only  
**No data action:** no archive, image, label row, restricted file, or model output was opened

## Decision

The best newly identified structural candidates are **SegThy** and **BCMID**, because each varies modality within one
source family and one anatomy. TN3K and VinDr-Mammo add useful cross-anatomy or cross-modality cells, but each remains a
single-modality family. None of them makes the full three-axis MOSAIC claim identifiable today.

This changes acquisition priority, not readiness. It does not authorize access, training, or derived views.

## Ranked repair candidates

| Priority | Candidate | Structural value | Primary evidence | Blocking facts | Disposition |
|---:|---|---|---|---|---|
| 1 | **SegThy** | Same healthy volunteers have MRI and repeated tracked 3D ultrasound of the thyroid/neck with label maps; this creates within-family modality variation for localization | [TUM dataset page](https://www.cs.cit.tum.de/en/camp/publications/segthy-dataset/) states 28 paired MRI/US volunteers, 186 additional US patients, manual label maps, direct downloads, and CC BY | Only 28 subjects are multimodal; the supported atom is anatomical localization, not disease recognition; 3D-to-2D conversion, group accounting, archive version/hash, overlap, source-specific purpose/disclosure, and weight-release review remain | Tier 1 metadata/schema intake candidate; strongest open structural repair |
| 2 | **BCMID** | Ultrasound and mammography are organized under each of 323 patient folders with patient labels; this is within-patient modality variation for breast recognition | [Zenodo v1](https://zenodo.org/records/14970848) identifies the paired patient structure and 323 adults | Files are restricted; the rendered record exposes no license value; newer version and access terms need resolution; spatial annotations are not established | Conditional; do not request or use until exact current version, terms, access basis, and challenge/release compatibility pass |
| 3 | **TN3K** | Ultrasound × thyroid adds a non-breast anatomy with masks and a referenced benign/malignant label source | [Author repository](https://github.com/haifangong/TRFE-Net-for-thyroid-nodule-segmentation) states 3,493 open-access nodule images, high-quality masks, and classification-label pointer | Repository MIT license is explicitly for code and is not treated as dataset permission; patient/group mapping, exact data terms, authoritative label join, split isolation, and release compatibility are unresolved | Conditional Tier 1 only after an authoritative data-license and grouping receipt |
| 4 | **VinDr-Mammo 1.0.0** | Mammography × breast supplies global BI-RADS and radiologist boxes, complementing ultrasound × breast | [PhysioNet record](https://physionet.org/content/vindr-mammo/1.0.0/) states 5,000 four-view exams, study IDs, breast labels, boxes, and official split | Restricted access, signed DUA, research-only purpose, no access receipt, and public-weight compatibility unresolved | Tier 2 credentialed candidate; no access assumption |
| 5 | **Chinese multi-organ ultrasound report collection** | One project reports breast, thyroid, and liver ultrasound-report datasets, potentially creating within-project anatomy variation for global semantics | [Author project page](https://lijunrio.github.io/Ultrasound-Report-Generation/) reports 3,521 breast, 2,474 thyroid, and 1,395 liver patients | Calls them three separate datasets; common upstream family/site is not established; no dataset license is stated; report labels are not automatically MMBU-compatible | Discovery lead only; cannot contribute a factor row without provenance and rights |

## What the candidates actually repair

| Candidate | Modality↔specimen alias | Task↔source alias | Source-adjusted leverage |
|---|---|---|---|
| SegThy | Partially: US and MRI share thyroid/neck subjects | Localization only; no meaningful global disease atom | High for a narrow localization claim |
| BCMID | Partially: US and mammography share breast patients | Global patient label appears shared; no authoritative spatial atom established | High if current terms and exact joins pass |
| TN3K | Adds ultrasound × thyroid but source remains nested in that cell | Masks plus referenced class labels may vary task within family | Medium, pending rights/grouping |
| VinDr-Mammo | Adds mammography × breast with global and box atoms | Multiple task atoms within family | Medium, but modality remains tied to family and access is restricted |
| Multi-organ ultrasound reports | Could vary specimen within ultrasound if one true family | Global semantics only | Potentially high, currently unsupported |

## Optimistic re-test

Adding optimistic SegThy and BCMID rows to the earlier candidate scaffold improves connectivity but does not produce a
valid broad design. With five modality categories, four specimen categories, and three task categories, the additive
semantic matrix has **10 columns and rank 8**. With reference-coded source-family effects, it has **17 columns and rank
12**. These figures are a structural stress test, not admitted-data evidence.

The remaining deficiency is expected: several modality and specimen levels still occur in only one family or one
joint cell. Adding TN3K or VinDr-Mammo volume does not remove source nesting. A multi-organ ultrasound project could
help only if its three organ datasets are proven to share one defensible source family and allowed use; the public page
does not establish that.

## Bound next decisions

1. Add SegThy to the first metadata/schema intake packet, ahead of BBBC038 for MOSAIC-specific structural value.
2. Defer BBBC038 to post-selection heterogeneous localization/count stress; exclude it from B1-L/B2-P selection,
   training, and the semantic-family minimum.
3. Do not request BCMID or VinDr-Mammo access until credential/data-use, intended-purpose, disclosure, and trained-weight
   release compatibility are resolved in writing. The general organizer permission for independently obtained
   contributor-source training splits is already recorded and does not override source terms.
4. Ask the Chinese collection authors only if a public authoritative record cannot answer license, institution/family,
   patient grouping, and release questions.
5. Recompute the frozen incidence matrix after admission; do not select a taxonomy that makes these candidates pass.

## Fail-safe narrowing

If the broad grid cannot pass before the experiment freeze, remove the specimen/scale mechanism claim. The only
scientifically defensible fallback is a named **MOSAIC-2 engineering probe** over modality × task geometry, with:

- no claim that anatomy or biological scale has been factorized;
- no paper-level novelty claim from routing alone;
- source-balanced and leave-one-family-out evaluation;
- B2, B4, uniform-route, source-route, and shuffled-route controls; and
- automatic rejection if route logits predict source identity beyond the preregistered envelope.

This fallback is likely easier to execute but less novel. It cannot inherit the current MOSAIC novelty score without a
fresh adverse review.
