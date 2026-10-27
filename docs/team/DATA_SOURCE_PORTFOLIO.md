# Prospective data-source portfolio

**Snapshot:** October 23, 2026
**Status:** public-metadata screen only; no source is admitted, downloaded, or approved by this document  
**Scope:** select the smallest defensible external-data portfolio for dual-objective B2 and the MOSAIC G-1 test

## Decision

The first B2 decision portfolio should prioritize **BUS-BRA**, **BUS-UCLM v3**, and **ChestMNIST-224 / NIH** if
ChestMNIST passes the rebuilt patient-grouped split and positive-label QA gates in the
[semantic-breadth intake decision](SEMANTIC_BREADTH_INTAKE_DECISION.md). **PathMNIST-224 / NCT-CRC** is blocked on
authoritative slide/patient lineage, and **OrganAMNIST-224 / LiTS** is anatomy/context support only. None is admitted. **BBBC039** is limited to
capped non-promotable geometry/count wiring smoke, while **BBBC038 v1** is deferred to post-selection heterogeneous
stress. For MOSAIC-specific structural intake, the later
[crossover-source search](CROSSOVER_SOURCE_SEARCH.md) places **SegThy** first because it contains paired MRI/ultrasound
subjects. This is a prioritization decision, not a license opinion. It replaces the earlier tendency to add sources
because they were medically relevant without first asking whether their annotations, grouping, rights, and source-family
independence can support the actual experiment.

The first network-read evidence capture is recorded in the
[data-source metadata receipt](DATA_SOURCE_METADATA_RECEIPT.md). It confirms the priority ordering but not admission.

The most important new candidate is BUS-BRA. Its public record and dataset paper describe 1,875 anonymized breast
ultrasound images from 1,064 patients, biopsy/pathology and BI-RADS labels, lesion delineations, and standardized folds.
That combination could support global classification, grounded classification, and mask-to-box localization from the
same source facts. BUS-UCLM provides a genuinely separate 38-patient ultrasound family with explicit patient-linked
filenames, benign/malignant labels, and expert masks. Together they are much stronger than treating a credentialed
chest-X-ray source as the only route to crossed spatial supervision.

This screen does **not** make MOSAIC identifiable. Exact admitted records, source-family assignments, and the resulting
design-matrix rank remain unknown. Later BUS-BRA and BUS-UCLM gates raise current data readiness to 5.8/10, but no real
source is admitted.

## Screening rules

A source can enter intake only if public primary metadata establishes a plausible path for all applicable fields below.
Unknown never means yes.

| Gate | Minimum evidence before download | Admission evidence after bounded intake |
|---|---|---|
| Authority and version | First-party or archival record with an immutable release/DOI | Stored page/terms receipt, resolved release, file manifest, hashes |
| Use and release rights | Express license or signed data-use route; absence of a prohibition is not permission | Human-reviewed purpose and public-weight/output decision; attribution obligations bound |
| Independent grouping | Patient, study, slide, field, video, or other defensible parent is described | Every record joins to a frozen group; unjoinable repeated acquisitions are quarantined |
| Task atoms | Labels, masks, boxes, or complete instance sets are explicitly described | Image/annotation joins, coordinate conventions, completeness, ontology, and QA pass |
| Source-family independence | Upstream parent and known derivatives can be named | Exact/perceptual overlap plus upstream-family reconciliation completes before splitting |
| Challenge separation | No need to inspect MMBU examples or outputs | No MMBU public image, text, label, embedding, frequency, or behavior enters admission or selection |
| Release compatibility | A plausible path exists for trained-weight release | Dataset license, challenge terms, model license, and artifact disclosure are reviewed separately |

Dataset licensing and permission to release model weights are separate questions. A permissive dataset license also does
not prove challenge eligibility, biomedical validity, or absence of overlap.

The October 14 organizer reply already permits independently obtained training splits from MMBU-contributing source
datasets and requires full dataset disclosure. “Challenge use” below therefore means source-specific terms, access,
intended-purpose, trained-weight release, lineage, and disclosure compatibility—not a missing blanket organizer ruling.
Contributor proximity remains a deduplication and generalization risk because the organizer provides no hidden-overlap
service; it is not an automatic prohibition.

## Ranked candidate screen

### Tier 1 — bounded intake candidates, still unapproved

| Priority | Source and prospective use | Primary public evidence | Known strengths | Blocking checks before admission |
|---:|---|---|---|---|
| 1 | **BUS-BRA 1.0** — ultrasound global, grounded, and localization views | [Zenodo record](https://doi.org/10.5281/zenodo.8231412); [dataset paper](https://doi.org/10.1002/mp.16812) | 1,875 images from 1,064 patients; biopsy/pathology, BI-RADS, lesion masks, and standardized folds; metadata, patient-disjoint outer folds, all decoded pairs, and within-source exact/perceptual triage are now receipted | Adjudicate four dimension errata and the `bus_0845-s` box/mask discrepancy; resolve the one perceptual provenance candidate; audit MMBU/cross-source proximity; obtain medical, purpose, rights, disclosure, and release sign-off |
| 2 | **BUS-UCLM v3** — independent ultrasound global, grounded, and localization views | [Mendeley v3](https://doi.org/10.17632/7fvgj4jsp7.3); [dataset paper](https://doi.org/10.1038/s41597-025-04562-3) | Exact 683-row image/mask name closure and 38 patient prefixes are now receipted; label totals match the paper; expert RGB masks remain unopened | Resolve CC BY versus CC BY-NC conflict and `Doppler=Y` anomaly; freeze patient-grouped treatment of normal, marked, Doppler, and combined images; inspect pixels/masks and duplicates; review attribution, purpose, weight release, disclosure, and source proximity |
| 3 | **ChestMNIST-224 / NIH**, with blocked **PathMNIST-224 / NCT-CRC** and **OrganAMNIST-224 / LiTS** for anatomy/context only | [Exact intake decision](SEMANTIC_BREADTH_INTAKE_DECISION.md); [ChestMNIST mapping audit](CHESTMNIST_MAPPING_AUDIT_2026-10-26.md); [official repository](https://github.com/MedMNIST/MedMNIST); [v2 paper](https://doi.org/10.1038/s41597-022-01721-8) | ChestMNIST's exact public mapping recovers 30,805 patient IDs and adds a distinct modality; its 112,120 image IDs exactly reconcile to the official NIH split universe | Ignore MedMNIST wrapper roles for scientific partitioning: they place 20,384 official NIH test images in wrapper train/validation. Build development roles only inside official NIH `train_val`, grouped by patient, and preserve all official NIH test images and patients untouched; never infer negative findings from absent text-mined labels; complete positive-label QA, resize/image, rights, purpose, release, and overlap review; restrict OrganAMNIST to anatomy/context |
| 4 | **BBBC038 v1** — post-selection heterogeneous localization/count stress only | [Official BBBC038 page](https://bbbc.broadinstitute.org/BBBC038) | 670 heterogeneous nuclei images; instance masks for the training portion; official page declares CC0 | Cannot satisfy the semantic-family minimum; use only after candidate selection, reconcile documented BBBC039 overlap and all upstream contributors, prove instance-set completeness, and retain source/contributor grouping |

**MOSAIC structural priority:** [SegThy](https://www.cs.cit.tum.de/en/camp/publications/segthy-dataset/) is a separate
Tier 1 metadata/schema candidate. Its 28 paired MRI/ultrasound volunteers can repair part of the modality alias for
localization, but it does not replace the B2 competition sources or supply disease recognition.

Tier 1 means “worth a small, receipted intake review,” not “safe to train on.” Downloading should be source-by-source and
stop after metadata/structure inspection if a hard gate fails.

### Tier 2 — useful only after an additional authority or grouping gate

| Source | Why it is attractive | Why it is not Tier 1 |
|---|---|---|
| **BUSI-WHU v3** | The [Mendeley record](https://doi.org/10.17632/k6cpmwybk3.3) reports 927 benign/malignant ultrasound images, a segmentation purpose, a data archive, a patient-information workbook, and CC BY 4.0. Protected metadata job `86066` proved the exact 927-row image/annotation/workbook join and 816 patient groups without decoding pixels. | Keep confirmation-only. Freeze patient-grouped clinical/annotation review, decode integrity and duplicate checks under a separate authority, and complete purpose/release review before admission. |
| **VinDr-CXR v1.0.0** | Radiologist global labels and boxes provide a second spatial modality | The [PhysioNet record](https://www.physionet.org/content/vindr-cxr/1.0.0/) requires credentialing, CITI training, and a signed Health Data Use Agreement. Access, permitted competition use, trained-weight compatibility, and patient/study grouping are not established |
| **HyperKvasir** | The [official page](https://datasets.simula.no/hyper-kvasir/) describes 10,662 labeled images and 1,000 polyp masks/boxes | Its terms require citation but the page does not state an express data license grant. The segmentation images duplicate the polyp-class images and substantially overlap the Kvasir family. Written use/release clarification is required before intake |
| **Kvasir-SEG** | The [official page](https://datasets.simula.no/kvasir-seg/) describes 1,000 medically reviewed polyp masks and boxes | Official terms restrict use to research/education and forbid commercial use without prior written permission. Competition and public-weight use are not assumed; it is the same Kvasir source family, not independent evidence from HyperKvasir |
| **BCMID** | The [Zenodo record](https://zenodo.org/records/14970848) describes same-patient breast ultrasound and mammography for 323 patients | Files are restricted, the rendered record exposes no license value, and the current-version/access/release basis is unresolved |
| **VinDr-Mammo 1.0.0** | The [PhysioNet record](https://physionet.org/content/vindr-mammo/1.0.0/) provides 5,000 mammography exams with breast-level labels and boxes | Restricted Health Data License and signed DUA apply; competition purpose, team access, and public trained-weight compatibility are unestablished |

### Existing quarantine sources

- **BBBC039** is capped non-promotable geometry/count wiring smoke only. It cannot select or kill a candidate, establish
  an effect floor, or satisfy the semantic-family minimum. BBBC038 and BBBC039 have documented partial overlap and are
  one conservative BBBC/upstream family until reconciled.
- **ROCOv2 and PMC-VQA** remain one conservative PMC-literature family because inspected metadata already shows shared
  PMCIDs. Their figure-level rights and semantic-label suitability remain unresolved.
- **DermaMNIST** is excluded from the first screen because its official aggregate license is CC BY-NC 4.0. It adds no
  indispensable cell that justifies early noncommercial/release ambiguity.

## Task-atom reality check

| Source | Global recognition | Region-conditioned recognition | Coordinate localization | Counting | Important limitation |
|---|---:|---:|---:|---:|---|
| BUS-BRA | Candidate | Candidate | Candidate from reviewed mask/box conversion | No | All three candidates must join to the same authoritative patient/image/lesion record |
| BUS-UCLM | Candidate | Candidate for lesion-bearing images | Candidate from reviewed masks | No | Normal images cannot silently receive synthetic lesion boxes or negative disease labels |
| BUSI-WHU | Candidate | **Mechanically complete:** 927 records map to 816 patients | **Mechanically paired only:** 927 image/annotation names match; payload validity remains unreviewed | No | Clinical correctness, mask usability, duplicates, purpose authorization, and confirmation eligibility remain unproved |
| PathMNIST / NCT-CRC | Blocked candidate | No | No | No | Requires authoritative slide/patient parent lineage for every patch |
| ChestMNIST / NIH | First executable breadth intake candidate | No | No | No | Patient IDs and the official NIH split are recoverable. Use only official NIH `train_val` for patient-grouped development; keep official NIH test untouched. QA text-mined positives; absent labels are not verified negatives |
| OrganAMNIST / LiTS | Anatomy/context candidate | No | No | No | All planes and 3D variants are one family; not disease evidence |
| BBBC038 | No meaningful medical class | Not counted as meaningful | Candidate | Candidate only for complete instance sets | “Nucleus” is a trivial object type, not semantic transfer evidence |
| VinDr-CXR | Candidate | Candidate | Candidate | No | Credentialed-data and release gates precede any technical use |

No source may be credited for a task cell merely because a transformation is mathematically possible. The source atoms
must support the target meaning. Masks can yield tight boxes, but boxes cannot establish diagnoses, and incomplete
instances cannot yield counts.

## Minimum competition portfolio versus MOSAIC portfolio

### B2 competition curriculum

The minimum decision-bearing source rule is exact:

1. **BBBC039** may be used only for capped, non-promotable geometry/count wiring smoke.
2. **BUS-BRA alone** is engineering-only and cannot select or kill B1-L/B2-P or establish an effect floor.
3. **B1-L/B2-P decisions require BUS-BRA plus at least two independently admitted semantic-breadth families**, with
   prospectively assigned development and held-out-family roles. BUS-UCLM remains the preferred independent
   ultrasound replication candidate. The metadata-only
   [semantic-breadth intake decision](SEMANTIC_BREADTH_INTAKE_DECISION.md) now ranks ChestMNIST-224 / NIH first for
   executable non-ultrasound intake after its patient-mapping audit, keeps PathMNIST-224 / NCT-CRC blocked on parent
   lineage, and limits OrganAMNIST-224 / LiTS to anatomy/context support. None is a pre-approved satisfier.
4. **BBBC038 is a post-selection heterogeneous stress source** and cannot satisfy the semantic-family minimum.

BUS-BRA engineering can verify loading, target construction, gradients, loss behavior, throughput, memory,
serialization, and within-source failure modes. It cannot support a held-out-source claim. The semantic-family minimum
follows from the declared task breadth and this document's source-coverage analysis, not from MMBU model outputs.

This portfolio can test whether task-form curriculum helps a base-architecture-preserving adapter, pending loader
confirmation. It does not need to prove semantic
factor reuse, and it should not be delayed merely to make MOSAIC viable.

### MOSAIC G-1

The same sources provide only a **candidate** route to a crossed grid, not a pass. The later
[source–factor incidence audit](SOURCE_FACTOR_INCIDENCE_AUDIT.md) shows that an optimistic scaffold is still rank
deficient because the cleanest modality and specimen levels are one-to-one:

- ultrasound has multiple candidate families with global and spatial atoms;
- microscopy can obtain global cells from separately reviewed MedMNIST subsets and spatial cells from BBBC;
- tissue/cellular/organ scale definitions may cross modalities, but must be frozen from source metadata rather than
  chosen after seeing rank; and
- a third independent eligible family must remain unopened for confirmation.

MOSAIC proceeds only after the exact admitted incidence table passes every condition in
[MOSAIC_DATA_GATE.md](MOSAIC_DATA_GATE.md). If modality, specimen/scale, task, or source family remains aliased, the
research branch is narrowed or rejected. Broadening a taxonomy until the matrix appears full rank is prohibited.

Additional same-cell ultrasound sources improve replication but do not repair the alias. Intake search must prioritize
true crossover cells and evaluate source-adjusted rank plus leave-one-family-out graph connectivity.

## Bounded intake order and stop rules

1. Capture immutable terms/version metadata for BUS-BRA and BUS-UCLM; do not fetch pixels yet.
2. Inspect archive listings and metadata schemas; confirm patient/fold/label/mask keys and expected counts.
3. Stop a source if patient/study grouping cannot be reconstructed for repeated images, if label-mask joins are
   ambiguous, or if rights/release review says no.
4. Only then fetch a minimal structural sample to validate decoders, coordinates, and hashes; sample selection must be
   deterministic and blind to model behavior.
5. Run cross-source exact/perceptual duplicate review before splitting.
6. Freeze source families, factor vocabulary, purpose decisions, and prospective split roles before generating views.
7. Leave the confirmation family unopened until the recipe and decision rule are frozen.

No source validation/test labels are opened merely to improve the source screen. Source-provided folds may be used only
under a prospectively assigned role. A failure produces rejection or a narrower claim, never an improvised split.

## Current disposition

This screen improves the path to G-1 by replacing a single credentialed radiology dependency with two open,
patient-described ultrasound candidates and a third conditional family. It does not raise the admitted-source count:
there are still **zero admitted real sources**. BUS-BRA has now completed metadata closure, quarantined full-corpus
structural/perceptual inspection, and a binding deterministic transform contract; it remains blocked by medical,
provenance, rights, purpose, and release gates. BUS-UCLM now has exact v3 metadata/image/mask inventory closure, but its
schema anomaly, license conflict, and unopened pixel/mask/duplicate/medical gates remain blocking. Neither status
requires inspecting MMBU examples or running a model.
