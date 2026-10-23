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
