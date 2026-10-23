# Prospective data-source portfolio

**Snapshot:** October 17, 2026  
**Status:** public-metadata screen only; no source is admitted, downloaded, or approved by this document  
**Scope:** select the smallest defensible external-data portfolio for dual-objective B2 and the MOSAIC G-1 test

## Decision

The first B2 intake should prioritize **BUS-BRA**, **BUS-UCLM v3**, selected non-Derma **MedMNIST+** subsets, and
**BBBC038 v1**. For MOSAIC-specific structural intake, the later
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

This screen does **not** make MOSAIC identifiable. Exact records, grouping joins, source-family assignments, and the
resulting design-matrix rank are still unknown. Data readiness therefore remains 5.0/10.

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
| 2 | **BUS-UCLM v3** — independent ultrasound global, grounded, and localization views | [Mendeley v3](https://doi.org/10.17632/7fvgj4jsp7.3); [dataset paper](https://doi.org/10.1038/s41597-025-04562-3) | 683 images from 38 patients; filename prefix is a patient identifier; expert RGB masks encode benign/malignant tissue; Mendeley reports CC BY 4.0 | Verify all image-to-patient and image-to-mask joins; freeze at patient level; define treatment of normal/no-mask, Doppler, and combined images; inspect duplicate/near-duplicate studies; review attribution, source-specific purpose, weight release, disclosure, and source proximity |
| 3 | **Selected MedMNIST+ 224 subsets, excluding DermaMNIST** — global classification breadth only | [Official repository](https://github.com/MedMNIST/MedMNIST); [MedMNIST+ construction](https://github.com/MedMNIST/MedMNIST/blob/main/on_medmnist_plus.md); [v2 paper](https://doi.org/10.1038/s41597-022-01721-8) | Standard train/validation/test partitions, 224-pixel versions, source-image mapping CSVs, and aggregate CC BY 4.0 statement except DermaMNIST | Review each subset separately; join the published mapping back to upstream grouping where possible; collapse Organ A/C/S/3D and other shared origins into one family; reject subsets whose patient/slide/study grouping cannot be reconstructed for the intended comparison; verify upstream obligations and label semantics; do not treat wrapper subsets as independent families |
| 4 | **BBBC038 v1** — microscopy instance localization/counting | [Official BBBC038 page](https://bbbc.broadinstitute.org/BBBC038) | 670 heterogeneous nuclei images; instance masks for the training portion; official page declares CC0 | Use only annotation-bearing source-training material; reconcile documented BBBC039 overlap and all upstream contributors; prove instance-set completeness before count views; retain source/contributor grouping when available; do not count the trivial label “nucleus” as meaningful region-conditioned medical recognition |

**MOSAIC structural priority:** [SegThy](https://www.cs.cit.tum.de/en/camp/publications/segthy-dataset/) is a separate
Tier 1 metadata/schema candidate. Its 28 paired MRI/ultrasound volunteers can repair part of the modality alias for
localization, but it does not replace the B2 competition sources or supply disease recognition.

Tier 1 means “worth a small, receipted intake review,” not “safe to train on.” Downloading should be source-by-source and
stop after metadata/structure inspection if a hard gate fails.

### Tier 2 — useful only after an additional authority or grouping gate

| Source | Why it is attractive | Why it is not Tier 1 |
|---|---|---|
| **BUSI-WHU v3** | The [Mendeley record](https://doi.org/10.17632/k6cpmwybk3.3) reports 927 benign/malignant ultrasound images, a segmentation purpose, a data archive, a patient-information workbook, and CC BY 4.0 | Public metadata does not by itself prove that every image joins to a patient and authoritative mask. Inspect only after BUS-BRA/BUS-UCLM; promote only if patient grouping, mask provenance, labels, and split isolation are complete |
| **VinDr-CXR v1.0.0** | Radiologist global labels and boxes provide a second spatial modality | The [PhysioNet record](https://www.physionet.org/content/vindr-cxr/1.0.0/) requires credentialing, CITI training, and a signed Health Data Use Agreement. Access, permitted competition use, trained-weight compatibility, and patient/study grouping are not established |
| **HyperKvasir** | The [official page](https://datasets.simula.no/hyper-kvasir/) describes 10,662 labeled images and 1,000 polyp masks/boxes | Its terms require citation but the page does not state an express data license grant. The segmentation images duplicate the polyp-class images and substantially overlap the Kvasir family. Written use/release clarification is required before intake |
| **Kvasir-SEG** | The [official page](https://datasets.simula.no/kvasir-seg/) describes 1,000 medically reviewed polyp masks and boxes | Official terms restrict use to research/education and forbid commercial use without prior written permission. Competition and public-weight use are not assumed; it is the same Kvasir source family, not independent evidence from HyperKvasir |
| **BCMID** | The [Zenodo record](https://zenodo.org/records/14970848) describes same-patient breast ultrasound and mammography for 323 patients | Files are restricted, the rendered record exposes no license value, and the current-version/access/release basis is unresolved |
| **VinDr-Mammo 1.0.0** | The [PhysioNet record](https://physionet.org/content/vindr-mammo/1.0.0/) provides 5,000 mammography exams with breast-level labels and boxes | Restricted Health Data License and signed DUA apply; competition purpose, team access, and public trained-weight compatibility are unestablished |

### Existing quarantine sources

- **BBBC039** remains useful engineering material, but BBBC038 and BBBC039 have documented partial overlap and are one
  conservative BBBC/upstream family until reconciled.
- **ROCOv2 and PMC-VQA** remain one conservative PMC-literature family because inspected metadata already shows shared
  PMCIDs. Their figure-level rights and semantic-label suitability remain unresolved.
- **DermaMNIST** is excluded from the first screen because its official aggregate license is CC BY-NC 4.0. It adds no
  indispensable cell that justifies early noncommercial/release ambiguity.

## Task-atom reality check

| Source | Global recognition | Region-conditioned recognition | Coordinate localization | Counting | Important limitation |
|---|---:|---:|---:|---:|---|
| BUS-BRA | Candidate | Candidate | Candidate from reviewed mask/box conversion | No | All three candidates must join to the same authoritative patient/image/lesion record |
| BUS-UCLM | Candidate | Candidate for lesion-bearing images | Candidate from reviewed masks | No | Normal images cannot silently receive synthetic lesion boxes or negative disease labels |
| BUSI-WHU | Candidate | Unknown pending archive inspection | Unknown pending authoritative mask inspection | No | A stated segmentation purpose is not proof of a complete image-mask-patient join |
| MedMNIST+ | Candidate | No | No | No | Classification wrapper; source mapping and group recovery vary by subset |
| BBBC038 | No meaningful medical class | Not counted as meaningful | Candidate | Candidate only for complete instance sets | “Nucleus” is a trivial object type, not semantic transfer evidence |
| VinDr-CXR | Candidate | Candidate | Candidate | No | Credentialed-data and release gates precede any technical use |

No source may be credited for a task cell merely because a transformation is mathematically possible. The source atoms
must support the target meaning. Masks can yield tight boxes, but boxes cannot establish diagnoses, and incomplete
instances cannot yield counts.

## Minimum competition portfolio versus MOSAIC portfolio

### B2 competition curriculum

The smallest credible intake target is:

1. BUS-BRA plus BUS-UCLM for patient-grouped ultrasound classification, grounding, and localization;
2. selected MedMNIST+ subsets for classification breadth only, after subset-level lineage/group review; and
3. BBBC038 for genuinely instance-based coordinate/count views after completeness and overlap review.

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
there are still **zero admitted real sources**. BUS-BRA has now completed metadata closure and quarantined full-corpus
structural/perceptual inspection but remains blocked by recorded geometry exceptions and medical/provenance/rights/
purpose/release gates. BUS-UCLM still needs authoritative license resolution and bounded structural intake. Neither
status requires inspecting MMBU examples or running a model.
