# Data-source metadata receipt

**Observed:** `2026-10-18T04:18:04Z` (`2026-10-17` America/Chicago)  
**Evidence class:** network-read public metadata only  
**No data action:** no dataset archive, image, mask, label row, MMBU example, or model output was downloaded or opened

## BUS-BRA 1.0

### Primary observations

- The [Zenodo record](https://zenodo.org/records/8231412) identifies record `8231412`, DOI
  `10.5281/zenodo.8231412`, version `1.0`, and one file named `BUSBRA.zip`.
- [Zenodo's API](https://zenodo.org/api/records/8231412) returned `access_right: open` and license identifier `cc-by-4.0`. The rendered page's Rights section did
  not visibly render the license value during this observation, so the machine-readable API value—not a secondary
  search snippet—is the recorded license evidence.
- The API reported `BUSBRA.zip` size `133917740` bytes and checksum
  `md5:1f8b2be6476d58fc97bfb5e5a1ea9bab`.
- A canonical JSON projection of record ID, creation/update timestamps, title, version, access, license, and file
  identity hashed to
  `sha256:aa34430f3737b9549fd743bff34146d716509686a9af84e11786ea99e1b1744e`.
- The record describes 1,064 patients, biopsy-proven tumor cases, BI-RADS 2–5 annotations, and ground-truth tumor/normal
  delineations. The [dataset paper](https://doi.org/10.1002/mp.16812) describes 1,875 images, 1,064 patients, manual
  lesion outlines, pathology/BI-RADS use, and standardized cross-validation partitions.
- The authors' [source-code repository](https://github.com/wgomezf/BUS-BRA) resolved at observation to
  `296f9ae570b33fbb608b10b0cdd133f8addfab10`. Its README describes both segmentation and pathology/BI-RADS
  classification and five-fold cross-validation. The repository's GPL-3.0 license applies to code and is not used as
  evidence for the dataset license.

### October 23 structural updates

The initial [metadata gate](BUSBRA_METADATA_GATE.md) used bounded HTTP ranges to extract only `bus_data.csv`,
`5-fold-cv.csv`, and `10-fold-cv.csv`. No image or mask was extracted or decoded; fixed-size range blocks may still
overlap adjacent compressed members. The gate established exact 1,875-row image/mask/metadata closure, complete
`Case` grouping for 1,064 patients, valid stored boxes, and patient-disjoint outer `kFold` assignments. It also found
that the provided `valid_*` flags split hundreds of patients across training and validation; those fields are now
prohibited.

A later local quarantine audit authenticated the complete pinned archive and decoded all 1,875 image/mask pairs. Every
image and mask joined, all images were grayscale `L`, all masks were binary mode `1` with nonempty foreground, and no
exact decoded image or mask duplicate was found. Four rows declare the wrong height, 43 boxes differ from the
mask-derived extent by the source's apparent one-pixel boundary convention, and `bus_0845-s` has a material stored-box
versus mask-extent discrepancy. A full 64-bit difference-hash screen produced one cross-case candidate,
`bus_0110-l` / `bus_0536-r`; the pair is visibly different but remains open for provenance review. These findings do
not establish medical correctness, source proximity, patient identity, or near-duplicate absence.

### Still unknown

- medical interpretation, annotation completeness, multi-lesion policy, and adjudication of the `bus_0845-s` box;
- exact source family, acquisition-site/device interpretation, cross-source duplicates, and relationship to any MMBU source;
- source-specific purpose/terms, derived-view approval, disclosure readiness, and public trained-weight compatibility
  after joint review; the organizer's general contributor-source permission is already recorded separately.

**Disposition:** passes metadata closure, exact decoded-duplicate checks, and bounded within-source perceptual triage
with `Case` as the independent unit, outer `kFold` as the only source-provided split field, and every `valid_*` field
prohibited. Overall structural clearance remains false because of the source dimension/geometry findings. Independent
medical, provenance, rights, purpose, release, and source-proximity review still block model use.

## BUS-UCLM v3

### Primary observations

- The [Mendeley v3 record](https://data.mendeley.com/datasets/7fvgj4jsp7/3) identifies version `3`, DOI
  `10.17632/7fvgj4jsp7.3`, and CC BY 4.0.
- The record describes 683 images from 38 patients: 174 benign, 90 malignant, and 419 normal. It says the ground truth is
  stored as RGB masks, with green benign tissue, red malignant tissue, and black background/normal tissue.
- The [dataset paper](https://doi.org/10.1038/s41597-025-04562-3) states that the four-letter filename prefix is an
  anonymized patient identifier and describes separate image/mask folders plus image information.
- The authors' [source repository](https://github.com/noeliavallez/BUS-UCLM-Dataset) resolved on October 23 to commit
  `d9aa230cd1ab5f546746bef1380196e91f6b33a8`. Its README calls the dataset CC BY 4.0, but its `LICENSE.md` body says
  CC BY-NC 4.0. This conflicts with the earlier Mendeley-page observation and must be resolved against authoritative
  dataset terms before any model-use purpose is granted.

### Still unknown

- exact archive name, byte size, checksum, internal paths, and metadata columns from the current v3 distribution;
- authoritative dataset-license resolution for the CC BY versus CC BY-NC repository conflict;
- totality and uniqueness of image–patient–mask joins;
- source-provided split status; treatment of repeated views, combined images, Doppler images, and normal/no-lesion cases;
- duplicates, source proximity, source-specific purpose/terms, disclosure readiness, and trained-weight release
  compatibility; contributor-source status alone is not an organizer prohibition.

**Disposition:** remains Tier 1 priority 2 and blocked for model use. The exact v3 metadata gate below now establishes
patient/image/mask name closure, but schema clearance, pixels, medical review, duplicates, purpose/release review, and
authoritative license resolution remain incomplete.

### October 23 metadata-gate update

The later [BUS-UCLM metadata gate](BUSUCLM_METADATA_GATE.md) bounded-read the v3 central directory and `INFO.csv`. It
established exact closure across 683 metadata rows, 683 image names, 683 mask names, and 38 four-letter patient groups;
all rows declare `856x606`, and label totals match the publication. It also found one noncanonical `Doppler=Y` value
alongside 36 `Yes` values, plus 154 marked and 6 combined images. Schema clearance therefore remains false. The
license contradiction also remains unresolved, and no pixel body or model was opened.

## BUSI-WHU v3

The [Mendeley v3 record](https://data.mendeley.com/datasets/k6cpmwybk3/3) identifies version `3`, DOI
`10.17632/k6cpmwybk3.3`, CC BY 4.0, 927 benign/malignant images, tumor regions, and a segmentation purpose. The page does
not expose enough structure to prove image–mask–patient joins. Third-party reorganizations are not authority.

**Disposition:** stays conditional Tier 2. It cannot be used as the third family until the original archive's patient
workbook, image names, authoritative masks, and one-patient-one-split feasibility are verified.

## Gate result

The metadata screen **passes source-priority review** and **does not pass source admission**:

1. BUS-BRA passes metadata closure and quarantined full-corpus decoder/exact-duplicate checks with a binding split
   restriction, but structural clearance remains false; medical semantics, cross-source proximity, rights/purpose,
   release review, and near-duplicate certification remain open.
2. BUS-UCLM now passes exact metadata/image/mask name closure and patient grouping, but fails schema and license
   clearance; pixels, mask semantics, duplicates, medical review, and model-use purposes remain unopened.
3. BUSI-WHU remains conditional rather than being promoted from third-party evidence.
4. MOSAIC G-1 remains `not evaluated`; projected coverage is not an incidence matrix.
5. Data readiness remains 5.0/10 because no real record has passed rights, grouping, lineage, QA, purpose, and release
   admission together.

**Later authority:** the subsequent [source–factor incidence audit](SOURCE_FACTOR_INCIDENCE_AUDIT.md) does not change
the exact admitted-data status, but it does establish a provisional portfolio-structure failure under optimistic
metadata assumptions. Read `not evaluated` here as the admitted-data result, not as absence of a structural warning.
