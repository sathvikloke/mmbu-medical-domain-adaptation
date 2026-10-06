# MMBU CPU preparation — version 0.2

The next non-GPU preparation batch is implemented and tested. It adds a real-data conversion trial, image inspection, paired candidate comparison, and pinned model configuration evidence. **No model has been trained or evaluated; no training corpus or winning model has been established.**

## Concrete output

| Work | Result | Interpretation |
|---|---|---|
| BBBC039 public source-training intake | 100 images, 100 masks, 100 annotation sidecars | Native bytes preserved; source validation/test pixels and labels unopened |
| Annotation conversion | 11,999 components; 198 pending count/box records | Unapproved candidate targets, not validated biological labels or accepted training data |
| Independent decoder oracle | All 100 fields match on every component, box, area and border flag | Separate implementation using run-union logic |
| Repeat conversion | All 303 output files match byte-for-byte | Reproducible final-code CPU transformation |
| Image inspection | Native size/precision/orientation and exact decoded duplicate checks | No perceptual deduplication or patient-independence claim |
| Candidate comparison | Joint paired bootstrap with matched populations and candidate-specific baselines | Exploratory differences; no automatic winner selection |
| Model metadata | Pinned config snapshots for three candidates; 8 successful files and one recorded 404 | No weights or runtime verification |
| Tests | 178 pass with Pillow on Python 3.12; Python 3.14 has 146 passes and 32 explicit optional-dependency skips | Python 3.11 syntax checked; its runtime unavailable |

## Findings that matter

The supplied source training/validation/test partitions share plates. The 100 training fields cover 20 plates, all also present in other source partitions. We should not describe these as unseen-plate validation. The QA queue retains two empty masks, 1,997 border-touching components, and 429 components smaller than 25 pixels. Those need explicit annotation/target policies before use; no small objects were silently removed.

Independent reviews reproduced and closed converter transparency, mask-depth and big-endian TIFF issues, plus a portable-map precision issue in the image inspector. A separate bootstrap fix prevents very small source contributions disappearing through multiplication-order underflow. The original version 0.1 ZIP remains unchanged for historical traceability; use the new version for subsequent work. Exact findings, repair receipts and remaining limits are in the evidence directory.

The first model bring-up remains **Qwen/Qwen2.5-VL-7B-Instruct**, with **Qwen/Qwen3.5-9B** as the first challenger. Public metadata reports 8.29B and 9.65B checkpoint parameters respectively, with about 15.45 and 17.98 GiB of tensor storage before runtime/training overhead. These numbers do not establish GPU fit. A final choice needs measured adaptation gains on the same reviewed cohort.

## Files

- Portable release: [mmbu-precompute-v0.2.zip](mmbu-precompute-v0.2.zip)
- Release verification: [MMBU-precompute-v0.2-verification.json](MMBU-precompute-v0.2-verification.json)
- Package: [mmbu-precompute/README.md](mmbu-precompute/README.md)
- Source intake and flags: [bbbc039-intake.md](mmbu-precompute/docs/bbbc039-intake.md)
- All 100 fields awaiting review: [bbbc039-review-queue.csv](mmbu-precompute/evidence/bbbc039-review-queue.csv)
- Independent source conversion review: [bbbc039-conversion-review.md](mmbu-precompute/evidence/bbbc039-conversion-review.md)
- Image review: [images-review.md](mmbu-precompute/evidence/images-review.md)
- Independent comparison/CLI review: [batch2-comparison-cli-review.md](mmbu-precompute/evidence/batch2-comparison-cli-review.md)
- Model preflight: [model-preflight.md](mmbu-precompute/docs/model-preflight.md)
- Final tests: [batch2-final-test-runs.json](mmbu-precompute/evidence/batch2-final-test-runs.json)

The raw source quarantine is at `work/bbbc039-quarantine` in this project, outside the portable code ZIP. Its prepared directory holds only source-training material; the source validation/test contents remain inside the original received archives. The eight-view structural contact sheet is in `work/bbbc039-quarantine/qa/structural-contact-sheet.png`. Its display scaling is documented and is not a training preprocessing decision.

## What still requires a different kind of evidence

- Organizer clarification of output/grading details, public-dev permissions and source-overlap eligibility. The question draft remains unsent.
- Biomedical annotation/ontology review and an approved, broader source mixture. This single microscopy source cannot represent the full challenge.
- A reviewed 16-bit image presentation policy and native model-processor compatibility.
- Einstein hardware/allocation details and a working GPU for baseline, bounded adaptation, throughput/memory measurements and export reload checks.

These gates do not invalidate the CPU work; they determine what can legitimately be promoted from preparation into model development. No training-ready status or performance claim is inferred from passing software tests.
