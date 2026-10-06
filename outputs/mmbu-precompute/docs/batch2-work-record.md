# CPU preparation, batch 2

This batch extends the completed 0.1 foundation without running a model. It applies the existing test-driven-development and verification-before-completion workflow. New functions receive executable behavioral tests; adversarial findings receive reproductions before repair. Separate agents review work they did not author. This separation provides an additional implementation check, not external human or biomedical validation.

## Scope and results

1. Joint candidate comparison: align example identity, task, source, group and annotated context fields; use the same within-source group resamples across every candidate's own baseline/adapted/context grades; return paired score differences and exploratory intervals. Keep exact supplied populations. Do not declare a winning model.
2. Image inspection: bounded file decoding, actual size/mode/frame/precision/orientation checks, byte and decoded-sample hashes, exact duplicate groups and cross-split flags. Reject unsupported transformations; do not claim perceptual deduplication or independent patients.
3. BBBC039 source-training intake: record official archive hashes, preserve original split/plate provenance, decode canonical connected components, retain raw 16-bit images, prepare unapproved count/box records and a 100-field QA queue. Keep source validation/test image and mask contents unopened.
4. Model preflight: snapshot small config files at pinned revisions and calculate tensor-storage arithmetic from the saved public API metadata. No weights, runtime fit, active count, inference or adaptation evidence.
5. Review, repair and release: independent source decoder oracle, independent rational comparison oracle, adversarial format probes, full suite with/without Pillow, clean-bundle verification, versioned ZIP and final evidence receipt.

## Defects found during the work

The first real mask decode exposed opaque RGBA source annotations beyond the initial RGB-only support. Regression coverage preceded the repair. Subsequent independent reviews found RGB tRNS transparency and 16-bit RGB PNG precision reduction bypasses in the converter, a native big-endian TIFF extrema compatibility error, and a PNM precision/scaling gap in generic image inspection. The decoder review preserves each finding and closure evidence.

Root inspection also identified multiplication-order underflow in the earlier single-candidate bootstrap. A four-row hand-calculated example now catches source contributions incorrectly collapsing to zero. Version 0.1's archived bundle remains unchanged for traceability; use 0.2 for the repaired calculation. Historical 0.1 test/audit receipts refer to that earlier code, not the current release.

## Interpretation

The source pass establishes deterministic conversion behavior on a concrete public source-training partition. It does not make the source eligible for the challenge, establish the biological validity of every supplied component, calibrate a semantic judge, or establish model improvement. The model-use registry deliberately remains closed for every real candidate source. The final status/report gives current test counts and review dispositions rather than treating draft plans or historical logs as current proof.
