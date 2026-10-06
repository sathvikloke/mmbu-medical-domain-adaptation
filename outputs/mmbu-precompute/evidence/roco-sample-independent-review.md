# ROCO sample coordinator independent review

Verdict: PASS within the fixed 24-image local quarantine-preparation scope, after one receipt-provenance defect was repaired by the root author. This review grants no source, figure, or model-use approval.

The reviewer read `tools/prepare_roco_sample.py` and independently replayed preparation with bundled Pillow Python into a temporary directory. All 53 output files reproduced the existing prepared sample byte for byte. All 24 raw JPEG copies matched the acquisition receipt's SHA-256, byte length and selected-member ZIP CRC32. The 24 PNGs preserved source dimensions and exactly matched Pillow RGB conversion of the source pixels (13 RGB and 11 grayscale JPEGs); presentation transforms were identity. Source IDs, captions/attribution sidecars, questions, manual modality answers and 24 distinct article groups matched the deterministic shortlist. No source or existing output bytes changed.

All records remained source-training, pending, with empty allowed purposes. The normal training gate rejected all 24 for each of source ineligibility, unpermitted purpose, unpermitted split and unapproved review status. Historical metadata sidecars intentionally retain their acquisition-time `metadata_only` and `image_not_acquired` flags; current image and presentation evidence is separate. Original-figure IDs remain null here; newer upstream-rights evidence is not silently grafted into the original conversion.

Adversarial replay rejected changed member hashes, missing/duplicated receipt members, missing/changed physical files, source symlinks, modified pinned metadata, unsupported RGBA input after staging, and existing output. Failed staging left no partial published output or staging directory. An initial counterexample showed that contradictory receipt source/version/partition/URL/shortlist declarations were ignored. The root author added strict fixed-value and exact-type validation. The same counterexample and 12 individually mutated declarations now reject before publication; these include boolean-versus-integer confusion and checksum/model-use status assertions.

Evidence: `roco-sample-independent-review-initial.json` preserves the original finding; `roco-sample-independent-review.json` records the final 23 passing cases. The local driver `work/roco-upstream-rights/review_sample.py` returned exit code 0. It performed no network requests and modified no production code. This is a deterministic local review, not an independent download or verification of the whole 4.61 GB source archive.

Final SHA-256 values:

- Coordinator: `9a961ca391179b6fd58250550631d98d88190489a567988c92ffd524fa269dce`
- Acquisition receipt: `5572860a78193a1f53ee7755e7d647b18fbfef96c7f84d950e09c25e597cf7cd`
- Shortlist: `d815b2238224f8e92cf5f321aba387e9a4ca3686bfd4dab13bf1c3b4377b9014`
- Independent driver: `74cbdcf84c0a19a781850c9767cc365aa7ed08392884fc90370ff2fa3203763d`
