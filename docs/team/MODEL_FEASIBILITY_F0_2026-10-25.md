# Bounded model-feasibility F0 trace

**Date:** October 25, 2026

**Status:** blocked before model loading by the MOCS user storage quota

**Scientific use:** none; this trace does not rank models or select a winner

## Frozen scope

The closed manifest is `config/phase1/model-feasibility-screen-2026-10-25.json`, SHA-256 `216f85f2de7e1ca25ddc2ef6505138f8f279b1ec3a346ef97b6f838e50275676`. The generated-only fixture, prompt, target, LoRA settings, optimizer, five candidate IDs, and exact revisions were not changed between attempts.

## Preserved attempts

| Attempt | Slurm job | Root | Outcome |
|---|---:|---|---|
| Initial acquisition | `85746` | `/storage/home/npl015/mmbu-f0/2026-10-25-0f68511` | Five terminal failure receipts; home-backed GPFS quota exhausted |
| One approved clean reacquisition | `85751` | `/storage/scr/npl015/mmbu-f0/2026-10-25-0f68511-reacquire1` | Five terminal failure receipts; the same account-level GPFS quota blocked scratch writes |

The first attempt's five receipts and ten stdout/stderr files remain in the home run root. Nothing there was deleted, moved, or overwritten. The clean scratch attempt used a brand-new path after `df` reported 284,467,200,000 KiB available cluster-wide. Its immediate `EDQUOT` failures show that free filesystem capacity was not the binding constraint; the account's GPFS allocation was.

## Candidate outcomes

| Candidate | Frozen revision | Acquisition | Model loaded | GPU F0 |
|---|---|---|---|---|
| `Qwen/Qwen3.5-9B` | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | Failed: quota | No | Not launched |
| `Qwen/Qwen3-VL-8B-Instruct` | `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` | Failed: quota | No | Not launched |
| `Qwen/Qwen3.5-4B` | `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | Failed: writer closed after peer quota failures | No | Not launched |
| `Qwen/Qwen3-VL-2B-Instruct` | `89644892e4d85e24eaac8bacfd4f463576704203` | Failed: writer closed after peer quota failures | No | Not launched |
| `OpenGVLab/InternVL3_5-2B-HF` | `3f301ffcf3dcbb47893afae6650ea3e78d96fb6d` | Failed: quota | No | Not launched |

`Internal Writer Error: Background writer channel closed` occurred in the same reconstruction layer as the explicit `Disk quota exceeded (os error 122)` failures. It is not model-runtime evidence. No candidate reached import, load, forward, backward, optimizer, save, or reload.

## Honest conclusion

There are no model-feasibility results yet. The only defensible result is that the present MOCS user allocation cannot hold the frozen five-snapshot screen. No retry is authorized, no GPU job ran, no MMBU public content was accessed, and no candidate may be promoted or rejected from this trace.
