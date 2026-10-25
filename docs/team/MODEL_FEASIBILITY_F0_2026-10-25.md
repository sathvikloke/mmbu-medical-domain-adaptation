# Bounded model-feasibility F0 trace

**Date:** October 25, 2026

**Status:** terminal; three candidates passed every F0 gate and two failed closed at the frozen parameter-count identity gate

**Scientific use:** none; this trace does not rank models or select a winner

## Frozen scope

The closed manifest is `config/phase1/model-feasibility-screen-2026-10-25.json`, SHA-256 `216f85f2de7e1ca25ddc2ef6505138f8f279b1ec3a346ef97b6f838e50275676`. The generated-only fixture, prompt, target, LoRA settings, optimizer, five candidate IDs, and exact revisions were not changed between attempts.

## Preserved attempts

| Attempt | Slurm job | Root | Outcome |
|---|---:|---|---|
| Initial acquisition | `85746` | `/storage/home/npl015/mmbu-f0/2026-10-25-0f68511` | Five terminal failure receipts; home-backed GPFS quota exhausted |
| One approved clean reacquisition | `85751` | `/storage/scr/npl015/mmbu-f0/2026-10-25-0f68511-reacquire1` | Five terminal failure receipts; the same account-level GPFS quota blocked scratch writes |
| Post-cleanup acquisition | `85823` | `/storage/scr/npl015/mmbu-f0/2026-10-25-57ce4d7-reacquire2` | All five snapshots acquired; all exact revisions matched |
| First GPU F0 launch | `85828` | same scratch root | All five tasks exited `127` before Python because the launcher did not load MOCS Python 3.12.12 |
| Approved repaired F0 launch | `85836` | `replacement-2b3204e` under the same scratch root | Three complete passes; two preserved identity-gate failures; no retries |

The first attempt's five receipts and ten stdout/stderr files remain in the home run root. Nothing there was deleted, moved, or overwritten. The clean scratch attempt used a brand-new path after `df` reported 284,467,200,000 KiB available cluster-wide. Its immediate `EDQUOT` failures show that free filesystem capacity was not the binding constraint; the account's GPFS allocation was.

## Candidate outcomes

| Candidate | F0 status | Optimizer updates | Offline reload match | Peak allocated | Elapsed |
|---|---|---:|---|---:|---:|
| `Qwen/Qwen3.5-9B` | Failed at identity gate: loaded count differed from frozen `9,653,104,368` | 0 | Not reached | Not measured | 26.52 s |
| `Qwen/Qwen3-VL-8B-Instruct` | Passed | 1 | Yes | 18,351,943,168 bytes (17.09 GiB) | 70.32 s |
| `Qwen/Qwen3.5-4B` | Failed at identity gate: loaded count differed from frozen `4,659,865,088` | 0 | Not reached | Not measured | 26.09 s |
| `Qwen/Qwen3-VL-2B-Instruct` | Passed | 1 | Yes | 4,697,793,024 bytes (4.38 GiB) | 41.09 s |
| `OpenGVLab/InternVL3_5-2B-HF` | Passed | 1 | Yes | 6,067,502,592 bytes (5.65 GiB) | 41.09 s |

Every passed candidate produced a three-file adapter inventory, changed its trainable LoRA tensors in exactly one optimizer update, and reproduced identical deterministic prediction token IDs after a fresh-process offline reload. The Qwen3-VL-8B pass matched 72 language-model projection targets; the two small-model passes matched 56 each. All five receipts report `mmbu_public_content_used=false` and `biomedical_content_used=false`.

The two Qwen3.5 snapshots loaded but failed before device placement because the frozen expected parameter counts were incorrect for the native Transformers model objects. A separate config-only meta-device reconstruction, with weights never loaded, produced post-tie counts of `9,409,813,744` for Qwen3.5-9B and `4,539,265,536` for Qwen3.5-4B. Those diagnostic counts do not silently amend the frozen manifest.

## Honest conclusion

Qwen3-VL-8B-Instruct, Qwen3-VL-2B-Instruct, and InternVL3.5-2B-HF are mechanically feasible under the frozen one-update envelope. This is engineering evidence only: it does not compare biomedical quality, adaptation gain, or official score, and it selects no winner. The Qwen3.5 outcomes are identity-contract failures rather than evidence of model incompatibility. Correcting their count contract and rerunning only those two candidates requires explicit approval.
