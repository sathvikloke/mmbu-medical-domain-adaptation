# Bounded model-feasibility F0 trace

**Date:** October 25, 2026

**Status:** terminal; all five candidates passed every F0 gate across the preserved original and count-repair runs

**Scientific use:** none; this trace does not rank models or select a winner

## Frozen scope

The original closed manifest had SHA-256 `216f85f2de7e1ca25ddc2ef6505138f8f279b1ec3a346ef97b6f838e50275676`. After its two Qwen3.5 identity gates exposed incorrect pre-tie counts, the authorized amendment changed only those two expected counts. The corrected `config/phase1/model-feasibility-screen-2026-10-25.json` has SHA-256 `f429defebc1e9062042e9a64b11288662621adee6759e314888a83c27e92187a`. The generated-only fixture, prompt, target, LoRA settings, optimizer, five candidate IDs, and exact revisions remained unchanged.

## Preserved attempts

| Attempt | Slurm job | Root | Outcome |
|---|---:|---|---|
| Initial acquisition | `85746` | `/storage/home/npl015/mmbu-f0/2026-10-25-0f68511` | Five terminal failure receipts; home-backed GPFS quota exhausted |
| One approved clean reacquisition | `85751` | `/storage/scr/npl015/mmbu-f0/2026-10-25-0f68511-reacquire1` | Five terminal failure receipts; the same account-level GPFS quota blocked scratch writes |
| Post-cleanup acquisition | `85823` | `/storage/scr/npl015/mmbu-f0/2026-10-25-57ce4d7-reacquire2` | All five snapshots acquired; all exact revisions matched |
| First GPU F0 launch | `85828` | same scratch root | All five tasks exited `127` before Python because the launcher did not load MOCS Python 3.12.12 |
| Approved repaired F0 launch | `85836` | `replacement-2b3204e` under the same scratch root | Three complete passes; two preserved identity-gate failures; no retries |
| Authorized Qwen3.5 count repair | `85867` | `/storage/scr/npl015/mmbu-f0/2026-10-25-countfix-5f321ec` | Both previously blocked candidates passed every F0 gate; the three prior passes were not rerun |

The first attempt's five receipts and ten stdout/stderr files remain in the home run root. Nothing there was deleted, moved, or overwritten. The clean scratch attempt used a brand-new path after `df` reported 284,467,200,000 KiB available cluster-wide. Its immediate `EDQUOT` failures show that free filesystem capacity was not the binding constraint; the account's GPFS allocation was.

## Candidate outcomes

| Candidate | F0 status | Optimizer updates | Offline reload match | Peak allocated | Elapsed |
|---|---|---:|---|---:|---:|
| `Qwen/Qwen3.5-9B` | Passed after the authorized identity amendment to `9,409,813,744` | 1 | Yes | 20,428,182,016 bytes (19.02 GiB) | 94.99 s |
| `Qwen/Qwen3-VL-8B-Instruct` | Passed | 1 | Yes | 18,351,943,168 bytes (17.09 GiB) | 70.32 s |
| `Qwen/Qwen3.5-4B` | Passed after the authorized identity amendment to `4,539,265,536` | 1 | Yes | 10,680,275,456 bytes (9.95 GiB) | 65.71 s |
| `Qwen/Qwen3-VL-2B-Instruct` | Passed | 1 | Yes | 4,697,793,024 bytes (4.38 GiB) | 41.09 s |
| `OpenGVLab/InternVL3_5-2B-HF` | Passed | 1 | Yes | 6,067,502,592 bytes (5.65 GiB) | 41.09 s |

Every candidate produced a three-file adapter inventory, changed its trainable LoRA tensors in exactly one optimizer update, and reproduced identical deterministic prediction token IDs after a fresh-process offline reload. The Qwen3-VL-8B pass matched 72 language-model projection targets; the two small-model passes matched 56 each. Both count-repair receipts report `mmbu_public_content_used=false` and `biomedical_content_used=false`, as did the three original passing receipts.

The original Qwen3.5 attempts remain preserved as failures before device placement: their frozen expected counts described serialized weights rather than the native Transformers model objects after weight tying. A separate config-only meta-device reconstruction, with weights never loaded, produced post-tie counts of `9,409,813,744` for Qwen3.5-9B and `4,539,265,536` for Qwen3.5-4B. A failing regression test captured that mismatch before the manifest and validator were amended. Job `85867` then confirmed both corrected identities through load, forward/backward, one optimizer update, adapter export, fresh-process offline reload, and deterministic prediction equality.

## Honest conclusion

All five candidates are mechanically feasible under the matched one-update F0 envelope. This is engineering evidence only: it does not compare biomedical quality, adaptation gain, or official score, and it selects no winner. The next decision-bearing step is a separately approved matched unchanged-base versus adapted experiment on frozen external biomedical data with replication.
