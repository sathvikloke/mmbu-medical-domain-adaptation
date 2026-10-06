# Perceptual duplicate review candidates

The optional `near-duplicates` command proposes pairs for human review. It does not merge lineage, delete records, reassign splits, or certify that contamination is absent. Use it on approved display representations during data QA, outside model inference. It uses no learned image model.

```sh
PYTHONPATH=src python3 -m mmbu_prep near-duplicates manifest.jsonl --image-root images
```

Each input first passes the existing hash, decoding, sample-depth and orientation inspector. Triage accepts RGB8/L8 only; native16 data needs an independently reviewed explicit presentation first. Existing exact decoded cross-split leakage fails the prerequisite inspection; inspect-images already reports those pairs. This command is not a way to override that failure.

The versioned fingerprint converts to Pillow luminance, bilinearly resizes to 9×8, and compares each pixel with its right neighbor using strict greater-than. It packs 64 Boolean comparisons most-significant-bit first. Default candidate thresholds are Hamming distance at most 4 and relative aspect difference `abs(a-b)/max(a,b)` at most 0.05. Both are adjustable engineering settings, not measured clinical duplicate classifiers. The input cap is 1,000 images because exhaustive pair comparison is quadratic.

Flat or near-monotonic hashes with at most 2 or at least 62 set bits are explicitly weak. A black and white image can share the same hash: tests retain this counterexample. Hashes ignore color; crops, overlays, mirrors and changed panels may escape them. Candidates must be inspected alongside original figure/article/patient provenance. Resolve any accepted identity links before assigning connected split groups.

The 24-item ROCO sample produced no candidate pairs under these settings. This tiny result does not establish source-wide near-duplicate absence. Its exact settings and per-image fingerprints are retained in `evidence/roco-duplicate-triage.json`.
