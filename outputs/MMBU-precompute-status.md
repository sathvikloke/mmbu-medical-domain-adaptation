# MMBU preparation status — October 3, 2026

The CPU-only foundation is implemented. The next GPU milestone remains E00's native model load and BF16/FP16 export/reload; that milestone is not complete. Einstein access is user-reported and currently unreliable, with IT follow-up pending. Hardware, usable memory and allocation details remain unknown.

## Delivered

| Area | Actual result | Limit |
|---|---|---|
| Inference boundaries | Separate task/context/judge builders; reference data excluded from model input builders | No real model adapter or inference-state reset has been exercised |
| Output and geometry | Two explicitly provisional JSON diagnostics, raw-output preservation, pixel xywh and IoU checks | No official-format precedence or semantic judging selected |
| Data validation | Provenance/permission checks, hashes, target schemas, declared bounds and transitive group/image/parent leakage checks | Byte hashes do not establish decoding, near duplicates, true dimensions, medical labels or rights |
| Split protection | Deterministic connected-component assignment, held-out split protection, operational purpose/split matching, no overwrite of output manifests | Initial assignment only; actual study independence still depends on correct lineage and exposure history |
| Scoring | Signed adaptation formula, within-example context averaging, balanced development weights, paired group bootstrap within fixed sources | Explicitly pregraded input; no official evaluation, candidate-superiority test or hidden-rank prediction |
| Sources and protocol | Five external biomedical candidates and the official source documented; six protocol questions tracked | Real-source permissions remain ungranted; no biomedical ingestion or archive inspection |
| Model candidates | Current public repository revisions pinned for the three Qwen candidates | Metadata only; weights, runtime and complete parameter counts unverified |
| Operations | Experiment/confirmation records, calibration and QA sheets, IT handoff and unsent organizer questions | Records are templates, not completed experiments or reviewer approvals |

The example bundle has **five original non-biomedical shape images and twenty pregraded arithmetic rows**. These are software fixtures. They do not count toward the planned 200–500-example biomedical engineering cohort or the 2,000–5,000-record training pilot.

## Verification

The complete suite passes **114 tests** on Python **3.12.14** and **3.14.7**. Python 3.11 syntax was checked; that interpreter was not available for runtime testing. A clean directory copy runs the offline demo/status/scoring commands and rejects the synthetic manifest for training with the expected nonzero exit.

Separate agents cross-reviewed modules they did not implement. Reviews found and drove repairs for development-only assignment permissions, nonfinite JSON overflow, numeric validation edge cases, and held-out records passing a training-purpose preflight. Earlier findings and failing regressions remain in the evidence directory alongside repair checks. The geometry reviewer also compared 10,000 integer-box IoUs with a separate raster oracle; the lineage reviewer checked 120 input permutations and 30 graph-oracle cases. These are software checks by agents from the same model family, not independent biomedical or empirical model validation.

The previously audited competition plan remains unchanged at SHA-256 `7e4997da8fef7614ad057bbd910c15a585d354e7f2036cc6be8bd659f5afbe64`. Current preparation details live here and in the new package, so the old audit's artifact identity is preserved.

## Handoff

- [Package README and commands](/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/README.md)
- [Organizer questions — draft, not sent](/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/docs/organizer-questions.md)
- [Einstein IT and first-session checklist](/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/docs/einstein-handoff.md)
- [Source screening](/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/docs/source-screening.md)
- [Verification runs](/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/evidence/final-test-runs.json)

Before actual biomedical ingestion, resolve the intended source/split use and approve a versioned conversion with its QA evidence. Before binding model selection, confirm the evaluation contract and grading/calibration. After IT restores access, record actual GPU capacity, load the pinned baseline, verify independent passes/export, then measure cost before the small matched pilots.

No organizer or IT message was sent. No terms were accepted, no gated files or model weights were downloaded, and no training, GPU job or paid API call was started. The software can be exercised immediately on the supplied engineering fixtures.
