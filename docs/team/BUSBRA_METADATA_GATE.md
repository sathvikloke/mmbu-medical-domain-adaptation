# BUS-BRA metadata gate

**Observed:** October 23, 2026
**Evidence:** [`outputs/BUSBRA-metadata-gate-2026-10-23.json`](../../outputs/BUSBRA-metadata-gate-2026-10-23.json)
**Decision:** metadata structure passes with a binding split restriction; model use remains unapproved

## Result

BUS-BRA 1.0 may advance to a quarantined structural intake after independent rights and purpose review. It is not yet
admitted for training, evaluation, model selection, or release. The audit extracted only the three CSV members through
bounded HTTP ranges. It did not extract or decode an image or mask, run a model, or inspect an MMBU example. Because
range blocks may overlap adjacent compressed members, the receipt does not claim that zero compressed image bytes
crossed the network.

The source archive closes structurally:

- the 1,875 metadata IDs match the 1,875 image names and 1,875 mask names exactly after the documented `bus_`/`mask_`
  filename transform;
- both official fold tables contain exactly the same 1,875 IDs and pathology labels as the metadata table;
- `Case` is present for all rows, agrees with the numeric ID prefix, and yields 1,064 independent patient groups;
- every stored `xywh` box is a four-integer, positive, in-bounds box under the row's declared width and height; and
- each patient belongs to one and only one outer `kFold` in both the five-fold and ten-fold tables.

## Binding split restriction

The release's `valid_*` columns are not patient-safe. Depending on the column, 201–216 patient groups in the five-fold
table and 221–245 patient groups in the ten-fold table receive inconsistent validation flags across their images.
Those fields must never define training, early stopping, validation, or confirmation roles.

The only source split field admitted by this metadata gate is the outer `kFold`, always interpreted at `Case` level.
Any development subdivision must be generated prospectively from whole `Case` groups inside the permitted outer
training population, before image bodies or model outcomes open. All views from one `Case` remain in one role.

## Annotation semantics

Pathology, histology, and device values are constant within every `Case`. One patient (`Case 856`) has separately
labeled left and right images with BI-RADS 4 and 5 while both share malignant invasive-ductal-carcinoma pathology.
This is retained as image-level source evidence, not repaired into a single patient label. Patient grouping still binds
the two images to one split.

The audit establishes structural joins only. Pixel/mask semantics, decoder behavior, duplicates, MMBU source-family
proximity, medical review, permitted derived task views, attribution, public weight release, and final purpose approval
remain unresolved.

## Honest impact on readiness

This closes the largest BUS-BRA metadata unknown and rejects an unsafe validation path. It does not make the source
training-ready by itself. Data readiness can rise only after a deterministic structural sample verifies decoded image
and mask semantics, duplicates and source proximity are reviewed, and an independent reviewer grants exact purposes.

## Quarantine inspector added after the gate

The repository now includes a two-phase local-only inspector in `tools/busbra_quarantine.py`:

1. `plan` reads only `bus_data.csv`, prioritizes the rarest pathology × BI-RADS strata, prevents reuse of
   a `Case`, and freezes exact image/mask member names under a digest before pixels open.
2. `inspect` verifies the complete local archive against the pinned byte count and MD5, reconstructs the plan
   from the archive metadata, and opens only the frozen members. It verifies PNG integrity, decoded dimensions, binary
   mask values, foreground presence, mask-derived `xywh`, box IoU, and exact decoded duplicates within the sample.

The receipt always records `training_ready=false` and `model_use_authorized=false`. A clean deterministic sample is not
a corpus-wide duplicate audit, clinical annotation review, source-proximity decision, rights decision, or purpose
authorization. The CLI has no network or model path and refuses to overwrite plans or receipt directories.

The first quarantined run verified the complete `133917740`-byte archive at MD5
`1f8b2be6476d58fc97bfb5e5a1ea9bab`, then decoded eight patient-unique records spanning every observed pathology ×
BI-RADS stratum. Every image was grayscale `L`; every mask was binary mode `1` with nonempty foreground. Mask-derived
boxes agreed closely with stored boxes (IoU `0.9633458646616542`–`0.9911610401459854`), and no exact decoded-image
duplicate occurred within the eight-record sample. Receipt digest:
`669e4181bd677bf423ae9c40d12f8d98b634b90e91bb6adc027ca18e8c10cd8e`. The full receipt remains quarantined locally;
these sample results do not close corpus-wide duplicates or grant model use.

## Full-corpus structural audit

The quarantine tool now also provides `audit-corpus`. It authenticates the entire pinned archive, requires an exact
metadata-to-image/mask inventory, decodes all metadata-bound pairs without extraction, and emits an aggregate receipt.
It does not accept source-declared dimensions on faith: image and mask dimensions must agree, and any disagreement with
the metadata is retained as an erratum. Exact decoded duplicate groups are reported by record, patient, and pathology;
the command never converts exact-duplicate clearance into near-duplicate clearance or model-use approval.

The first full run decoded all 1,875 image/mask pairs across 1,064 cases. All images were grayscale `L`; all masks were
binary mode `1`, nonempty, and dimensionally paired with their image. No two images and no two masks were exactly equal
after decoding. That result closes exact equality only—not perceptual, acquisition-series, patient-identity, or source
proximity duplication.

The run also found source inconsistencies that the eight-record sample could not reveal:

- four rows declare an incorrect height even though each image and mask agree with one another:
  `bus_0856-l` (405 declared, 353 decoded), `bus_0857-r` (409/393), `bus_0912-l` (354/352), and
  `bus_0990-l` (354/352);
- 44 stored boxes have IoU below 0.95 against the corresponding mask-derived box; 43 follow a consistent one-pixel
  boundary convention, while `bus_0845-s` is a material exception (IoU `0.37134146341463414`, stored
  `[214,77,164,100]`, mask-derived `[291,107,87,70]`). The stored box appears to cover a wider caliper/ROI region, but
  that visual observation is not a medical adjudication and no label was rewritten.

The local aggregate receipt digest is
`60e97562267ae7e8b82021ce5c1dfcd2eabaf54907efa721e1b624e7e14d516f`. The receipt remains deliberately
`structural_clearance=false`, `training_ready=false`, `near_duplicate_clearance=false`, and
`model_use_authorized=false`. These findings require an explicit derived-task policy and, for the material box
exception, independent annotation review before box targets may be admitted.

## Perceptual duplicate triage

The new `triage-near-duplicates` command extends the repository's existing versioned 64-bit difference-hash method to
the full BUS-BRA archive without changing the immutable historical implementation. It authenticates and opens the
archive once, decodes every image, binds all 1,875 fingerprints in a separate hashed file, and compares every pair at
the pre-existing engineering thresholds: Hamming distance at most 4 and relative aspect-ratio difference at most 0.05.
It cannot merge, exclude, regroup, or resplit a record.

The first full run produced zero low-information fingerprints and one candidate pair:
`bus_0110-l` / `bus_0536-r`, belonging to different cases 110 and 536, both source-labeled benign, with Hamming
distance 4 and relative aspect difference `0.016128903918838273`. The images are not raw- or decoded-exact matches.
A structural side-by-side review found visibly different anatomy, lesion appearance, text overlays, and acquisition
layout, so the weak-hash collision is not evidence that they are the same frame. It remains a provenance-review
candidate because visual inspection alone cannot prove distinct patient identity or acquisition lineage.

The local triage receipt digest is
`4964005ffe63015cbb8a2e152ed84f3af42d56ee76abe743e3cfc05b29bae104`. It deliberately records
`automatic_merge_or_exclusion=false`, `absence_of_near_duplicates_certified=false`, `training_ready=false`, and
`model_use_authorized=false`. Crops, mirrors, overlays, and altered panels may escape this weak hash; source proximity
and cross-source duplicate review remain open.
