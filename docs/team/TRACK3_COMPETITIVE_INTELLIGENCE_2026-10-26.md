# Track 3 competitive intelligence — October 26, 2026

**Status:** public self-report; zero model-selection authority  
**Observed repository:** `StarAtNyte1/InternVL3.5-2B-MMBU-RFT`  
**Observed main revision:** `1a556fa3b5ec737a2775d34c9274ec185df297d5`  
**Observation date:** October 26, 2026  
**Mutability warning:** the public repository can change; all claims below are scoped to the observed revision.

## Executive finding

A public Track 3 entry demonstrates that a dense 2.348B InternVL checkpoint, broad external-biomedical training,
metadata supervision, tiling, rejection sampling, and full-model fine-tuning are already being pursued by another
team. This is a credible competitive threat, but it is not official scoring evidence and does not promote InternVL,
authorize copying its recipe, or establish that its choices are best.

The important signal is strategic: a generic “small medical VLM plus more data” story is crowded. Our defensible route
must instead produce prospectively frozen evidence that a compact model gains biomedical capability while preserving
general capability, respecting source lineage, and surviving matched base-relative and family-diverse comparisons.

## What the public card self-reports

The revision's README describes:

- a full fine-tune of `OpenGVLab/InternVL3_5-2B-HF`, including the vision tower, projector, and language model;
- 2.348B dense active parameters at inference;
- rejection-sampled answers from public biomedical datasets, including verified self-samples and
  hint-rationalized failures;
- metadata targets for modality, submodality, specimen, body part, stain, and medical domain;
- additional concept rows and dozens of public biomedical sources spanning multiple modalities;
- tiled training and inference with up to six 448-pixel tiles plus a thumbnail;
- later canonical-label and repair stages with biomedical, general-capability, and balanced yes/no replay; and
- a local evaluation table reporting higher biomedical task metrics than the base while retaining named weaknesses
  and general-capability regressions on some evaluations.

These are author-provided statements, not independently reproduced results. The card reports local MMBU public-dev
numbers, so those values have zero model-selection authority here under the project's stricter public-set firewall.
Its pHash-disjointness statement is also a self-report, not a proof that semantic, patient, source, or derivative
overlap is absent.

## Independence from the competitor discovery

`OpenGVLab/InternVL3_5-2B-HF` was already a pre-existing frozen F0 candidate in
[`MODEL_FEASIBILITY_F0_2026-10-25.md`](MODEL_FEASIBILITY_F0_2026-10-25.md), before this competitor evidence was
recorded. Its bounded F0 receipt established only engineering mechanics: load, one optimizer update, export,
fresh-process offline reload, deterministic prediction equality, memory, and runtime. It did not establish biomedical
quality or priority.

That chronology matters. Keeping InternVL in a later family-diverse screen is defensible because it was frozen before
the competitor result was observed. The competitor card does not promote InternVL and must not set our learning rate,
data proportions, tiling policy, checkpoint choice, or stopping rule.

## Evidence-bearing implications

1. **Track 3 is viable and crowded.** A 2B-class route can support broad full-model adaptation, so model size alone is
   not a novelty claim.
2. **Breadth is not enough.** The public recipe reports many sources and stages, yet also reports residual
   general-capability regressions. Preservation must be a prospective decision endpoint, not an afterthought.
3. **Public-dev iteration is not our decision method.** Reported MMBU public-dev changes cannot enter our candidate,
   hyperparameter, or checkpoint decisions.
4. **RFT is a baseline, not our contribution.** Rejection sampling, hint rationalization, metadata supervision,
   tiling, and replay are established competitive ingredients. Any claimed contribution needs a controlled ablation
   and a distinction beyond combining them.
5. **Source governance can become a real differentiator only through evidence.** Our stronger source admission,
   patient grouping, held-out-family design, and immutable receipts matter only if paired with positive biomedical
   results; process prose alone earns no score increase.

## Next matched external experiment

After real source admission and protocol freeze, run one matched external experiment across the already frozen
2B-class candidates:

- `Qwen/Qwen3-VL-2B-Instruct`;
- `OpenGVLab/InternVL3_5-2B-HF`.

Use unchanged base, task-only adaptation, and dual task-plus-context adaptation for each family under identical
eligible records, exposure, seeds, prompts, optimizer budget, stopping rule, and output contract. Predeclare:

- grouped biomedical task performance on source-held-out data;
- biomedical context performance using source-authoritative fields only;
- untouched external-family transfer;
- general-capability preservation;
- strict-format failure rate;
- peak memory, runtime, and active-parameter accounting; and
- family-wise uncertainty plus a no-promotion region.

Do not add a 4B candidate until the organizer resolves exact Track 3 parameter treatment or a separately sealed
sensitivity branch explicitly treats it as non-promotional. Do not expand to broad training when the small matched
experiment cannot reject the no-benefit or unacceptable-regression conditions.

## Decision boundary

This evidence changes the threat model and the minimum baseline, not the current competition decision. No track,
candidate, recipe, or checkpoint gains authority from this document. A later decision requires admitted data,
prospective matched results, preservation evidence, and the unresolved organizer rule clarifications recorded in
[`COMPETITION_DIRECTION_DECISION_2026-10-25.md`](COMPETITION_DIRECTION_DECISION_2026-10-25.md).

## Public sources

- Model repository and mutable current card: https://huggingface.co/StarAtNyte1/InternVL3.5-2B-MMBU-RFT
- Observed revision metadata: https://huggingface.co/api/models/StarAtNyte1/InternVL3.5-2B-MMBU-RFT/revision/1a556fa3b5ec737a2775d34c9274ec185df297d5
- Revision-pinned README: https://huggingface.co/StarAtNyte1/InternVL3.5-2B-MMBU-RFT/blob/1a556fa3b5ec737a2775d34c9274ec185df297d5/README.md

