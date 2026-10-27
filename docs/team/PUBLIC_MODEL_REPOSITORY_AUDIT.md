# Public model repository audit: descriptive intelligence only

> **Historical snapshot, superseded for current competitive intelligence.** This file preserves the October 23 v13
> observation at revision `ecea8e0bb19c9f26c36f658d6acbf2323af3f73a`. The public repository later changed. Use
> [`TRACK3_COMPETITIVE_INTELLIGENCE_2026-10-26.md`](TRACK3_COMPETITIVE_INTELLIGENCE_2026-10-26.md) for the
> revision-pinned October 26 v15 observation and current threat interpretation. Neither snapshot has model-selection
> or promotion authority.

**Observed:** October 23, 2026  
**Evidence class:** self-authored public model card and Hugging Face repository metadata; not official participation,
leaderboard, evaluator, or independent-reproduction evidence  
**Decision authority:** none; this observation cannot change any project candidate, source, curriculum, resolution,
vocabulary, hyperparameter, compute budget, stopping rule, or promotion decision

## Executive conclusion

A public model repository that describes itself as an MMBU Track 3 project reports two local evaluations of the
blended proxy `0.8T+0.2C`: `0.403/0.404` for its v13 model and `0.315/0.318` for its 2B InternVL base. The model card
describes full-model tuning, many public biomedical source datasets, canonical answer labels, metadata supervision,
tiled image processing, and perceptual-overlap screening. It also reports held-out source-test improvement and
regressions on external medical VQA and MMStar.

These are useful facts about what one public repository claims to have tried. They are not a Track 2 score, an official
MMBU result, a comparable competitive threshold, a controlled ablation, or proof that any ingredient caused a gain.
Under this project's stricter firewall, neither the reported MMBU-public values nor the repository's public-set-driven
iteration history may influence our work. The observation therefore makes no strategy, rating, or execution change.

## Frozen public observation

| Item | Observed value |
| --- | --- |
| Repository | `StarAtNyte1/InternVL3.5-2B-MMBU-RFT` |
| Self-description | Track 3; `OpenGVLab/InternVL3_5-2B-HF` |
| Repository revision | `ecea8e0bb19c9f26c36f658d6acbf2323af3f73a` |
| Revision time reported by API | `2026-10-22T12:22:24Z` |
| Pinned README raw-byte SHA-256 | `f2b17428e8b470e19735929b66e71beeb1f30c888819777a04d754287931ddc6` |
| Declared optimization | full model; BF16; 8-bit AdamW; effective batch 32; initial LR `1e-5`, later `5e-6` |
| Declared visual processing | at most six 448-pixel tiles plus a thumbnail, matched at inference |
| Declared supervision | verified self-samples, hint-rationalized failures, metadata rows, canonical labels, and task templates from many public source datasets |
| Declared overlap control | perceptual-hash screening against MMBU public images |
| Two self-reported local blended-proxy evaluations | base `0.315/0.318`; v13 `0.403/0.404`, using the card's local scorer |
| Self-reported held-out source task score | base `0.228`; v13 `0.467` |
| Self-reported regressions | external medical VQA `0.548 -> 0.526`; MMStar `0.579 -> 0.545` |

Primary public sources:

- [pinned model card](https://huggingface.co/StarAtNyte1/InternVL3.5-2B-MMBU-RFT/blob/ecea8e0bb19c9f26c36f658d6acbf2323af3f73a/README.md)
- [repository metadata](https://huggingface.co/api/models/StarAtNyte1/InternVL3.5-2B-MMBU-RFT)

The API response is mutable and its response hash is not a durable content identity. The repository revision and
pinned README digest above anchor only the card that was read.

## What cannot be inferred

- The blended values are not the Track 2 base-relative score `S=(0.8T+0.2C)(T-T_base)`. Separate `T` and `C` values
  are absent, so a Track 2 score cannot be derived.
- The local judge is not established as the final organizer evaluator, and private-set transfer is unknown.
- The self-description does not prove registration, an accepted submission, rank, eligibility, or future participation.
- Two adjacent local values are not independent replication.
- Full tuning is not matched against PEFT, and the 2B InternVL visual path is not comparable to the pinned Qwen path.
- The bundled recipe cannot isolate rejection sampling, hint rationalization, canonical labels, tiling, source count,
  full tuning, or continued training.
- Perceptual-hash screening alone cannot establish semantic or upstream-family independence.
- The external evaluations and held-out splits have not been independently reproduced here.

## Firewall disposition

This record is reporting-only. The model card's MMBU-public score, examples, outputs, error patterns, selected datasets,
canonical vocabulary, tiling choice, and iteration history have zero role in this project's model or recipe selection.
They cannot trigger a new ablation, add or remove a source, set a threshold, prioritize an error stratum, or justify a
future public-set opening.

The project's pre-existing multi-family data requirement instead follows from the benchmark's published breadth and
the independently developed source/task coverage analysis. The existing canonical-emission and preservation controls
also predate this observation and retain their original evidence and gates. Similarity between those controls and this
card is descriptive only.

Any future MMBU-public evaluation remains frozen-model, reporting-only, and incapable of authorizing another recipe
change. Organizer permission to use the public set more broadly does not silently weaken this local policy.

## Rating impact

None. The observation creates no evidence for this repository, and no score rises or falls because of it. Data
readiness and local empirical evidence remain low for their existing reasons: no admitted multi-family biomedical
portfolio and no decision-bearing biomedical comparison.

