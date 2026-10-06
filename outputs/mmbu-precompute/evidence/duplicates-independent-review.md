# Duplicate triage independent review

Verdict: PASS for bounded, read-only candidate triage after two defects were repaired by the root author. No medical threshold calibration, identity claim, split clearance or absence-of-leakage claim follows from this review.

The reviewer read `src/mmbu_prep/duplicates.py`, the nine focused unit tests and `near-duplicates` CLI wiring, then used independently constructed Pillow fixtures. Initial probes found two issues: (1) an exactly 5% aspect difference, 19×20 versus 20×20, was excluded because subtracting rounded aspect ratios produced 0.050000000000000044; (2) changing an image after prerequisite inspection produced a new dHash attributed to the old raw/pixel hashes. The root author's integer cross-product aspect computation and bounded, SHA-verified immutable image buffer now pass the original counterexamples. Initial failed evidence is retained in `duplicates-independent-probes-initial.json`.

The final driver passed all eight groups in `duplicates-independent-probes.json`: known first/last-bit hashes establish horizontal strict-greater comparison and MSB-first order; Hamming distance 4 is included and 5 excluded at defaults; exactly 5% aspect difference is included; same-split reencoding preserves decoded-identity reporting; cross-split exact decoded matches fail prerequisite inspection; changed bytes after inspection reject; 16 adversarial type/depth/alpha/orientation/path/bound cases reject; and real 24-image JSON plus CLI output exactly reproduce the saved triage. The CLI returns 2 with stderr for cross-split exact leakage and returns 0 with the expected JSON for valid triage. The driver returned exit code 0, changed no input records/files, modified no production code and used no network.

The nine production unit tests also passed independently; `duplicates-independent-tests.json` preserves the exact command, output, exit code 0 and test-file hash. Flat/monotonic hashes are flagged weak, candidates are not automatically merged or excluded, and original group/split assignments remain unchanged. The actual 24-image sample produced zero candidate pairs under these settings; that observation certifies neither unique images/patients nor absence of crop, flip, overlay or panel leakage.

Final SHA-256 values:

- Module: `03a832d3c2e325c04b26e7d10a0e855c0e891ea5227a12c870f505ac88665682`
- CLI: `81695eaabc24043da9a6382fcf4f0e4c47f099b30b7cbb3217bf1b81478c1ef8`
- Saved real-sample triage: `c2f0ef593507ba6d87645099e063fbaf11baeec5af30f6384b47206e8463fc40`
- Independent local driver `work/roco-upstream-rights/review_duplicates.py`: `99b9d16e998e108346e7d2fb881328afa0d71cf9935a5c35b21029885714b55a`
