# Replicated biomedical response screen design

**Date:** 2026-10-25  
**Status:** approved for native implementation and execution by Aditya Raut's instruction to begin the previously described three-seed unchanged-base versus adapted experiment  
**Evidence class:** external-biomedical exploratory response evidence; never promotion, official-score, or source-admission evidence

## Intent

Measure whether the two mechanically feasible Qwen3.5 routes respond to the project's task-only and repaired answer/context adaptation recipes under matched conditions. The result should reduce the Track 2 versus Track 3 uncertainty without pretending that uncompleted human source admission or the unpublished official evaluator has been solved.

The screen compares:

- `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a`, the strongest current Track 2 route;
- `Qwen/Qwen3.5-4B@851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, the shared Track 3/Track 2 route explicitly recognized by the organizers; and
- for each model, an unchanged base, task-only language LoRA, and dual task/context language LoRA.

## Goals

1. Produce matched unchanged-base, task-only, and dual-objective results for both models.
2. Replicate each adapted condition at three prospectively fixed seeds.
3. Hold the selected records, record order, prompts, targets, update count, LoRA scope, optimizer, decoding, and evaluator fixed across models and seeds.
4. Replace the invalid shakedown context keys with defensible subsets of the published field registry.
5. Preserve raw per-row predictions, exact metrics, adapters, fresh-process reload equality, runtime, and memory.
6. Report uncertainty and negative flips without selecting or promoting a model.

## Non-goals and anti-goals

- Do not open, evaluate, or derive any decision from the MMBU public set.
- Do not use confirmation partitions, upload artifacts, or submit a model.
- Do not call this source admission, human medical review, official-harness equivalence, or competition performance.
- Do not let a training seed choose a different train or development population.
- Do not rescue a failed condition, change a threshold after results, drop failed rows, normalize malformed output, or select a winner.
- Do not make projector adaptation or a new learner mechanism part of this screen.

## Frozen data condition

Reuse the already checksummed BUS-BRA 1.0 and PathMNIST-224 v3 archives. Recompile them into a new manifest; never rewrite the earlier shakedown manifest.

- selection seed: `1729`;
- training: 512 independent units per source;
- development: 128 independent units per source;
- confirmation: sealed and unopened;
- all conditions consume the exact same selected row IDs in the exact same order;
- BUS-BRA remains patient-grouped by case;
- PathMNIST retains the publisher's train/validation roles but remains limited by unavailable parent-patient grouping;
- no result from this screen can admit either source or promote a competition candidate.

The successor context transformation is deterministic and source-level:

| Source | Requested fields | Exact targets |
|---|---|---|
| BUS-BRA | `body_part`, `medical_domain`, `modality` | `breast`, `radiology`, `ultrasound` |
| PathMNIST | `medical_domain`, `modality`, `specimen`, `stain` | `pathology`, `histopathology`, `colorectal tissue`, `hematoxylin and eosin` |

Every prompt requires exactly one raw JSON object with exactly the sorted requested keys. These targets come from the declared dataset identity and primary source descriptions, not model outputs or MMBU examples. They are deliberately coarse; unsupported submodality is omitted.

## Frozen model and training condition

- local exact snapshots from the completed F0 acquisition;
- generic native `AutoProcessor` and `AutoModelForImageTextToText` loading with `trust_remote_code=false`;
- BF16, SDPA, single A100 80 GB, offline mode, one process, no distributed execution;
- language-model `q_proj` and `v_proj` LoRA only;
- rank 8, alpha 16, dropout 0, learning rate `1e-4`, AdamW, weight decay 0;
- one epoch and exactly 1,024 optimizer updates per adapted condition;
- target-only labels, unit-normalized endpoint mass, gradient clipping at 1;
- fixed training order determined only by selection seed `1729`;
- training seeds `20261025`, `20261026`, and `20261027` vary initialization/RNG only;
- task-only mass is 1; dual mass is 3/4 task and 1/4 context when context exists;
- greedy generation with no sampling and fixed token ceilings;
- fresh-process offline adapter reload must reproduce every development prediction exactly.

There are fourteen conditions: one base plus six adapted conditions per model. At most five may run concurrently. Each condition gets one attempt and a four-hour wall-time ceiling. A scheduler rejection before job creation does not consume an attempt; a started condition does.

## Metrics and pre-output interpretation

For every source and pooled macro view, report task accuracy, strict context validity, field-level context score, `Q = 0.8T + 0.2C`, positive flips, negative flips, malformed outputs, runtime, and peak memory. Failed rows remain in every denominator as zero credit.

The screen has no automatic promotion output. Its predeclared descriptive checks are:

1. **Track 2 response signal:** for Qwen3.5-9B, each adapted seed's task delta versus the unchanged base is positive, and the cluster-bootstrap lower 90% confidence bound for the seed-mean paired task delta is above zero.
2. **Dual-objective value:** dual `Q` exceeds task-only `Q` by at least 0.01 in at least two of three matched seeds while its task score is no more than 0.01 lower in those seeds.
3. **Small-route competitiveness:** Qwen3.5-4B's adapted raw `Q` is within 0.03 of Qwen3.5-9B's matched adapted raw `Q` in at least two seeds. No Track 3 parameter multiplier is applied while `P/Pmax` remains unresolved.
4. **Instability flag:** any nonpositive medium-model task delta, any seed-direction reversal, or any materially elevated invalid-output rate blocks a Track 2 priority claim.

These checks prioritize the next experiment only. They cannot change the official track, select a submission checkpoint, or raise novelty on their own.

## Outputs and failure handling

Each condition writes once to a new condition directory and records:

- exact config/manifest/candidate/snapshot identities;
- selected train and development IDs and digests;
- raw predictions and exact metrics;
- optimizer-update count and trainable tensor inventory;
- adapter inventory for adapted conditions;
- fresh-process offline reload receipt and equality result;
- elapsed time, peak allocated/reserved memory, runtime package versions, and scheduler identity;
- explicit false MMBU-public-content use;
- explicit source-admission and promotion ineligibility.

Every exception emits a terminal failure receipt with its stage and traceback. Existing outputs are never overwritten. No condition is retried automatically.

## Claim boundary

A complete pass would show that the models and recipes can be compared reproducibly on this external exploratory population and would provide an honest adaptation-response signal. It would not establish medical validity, source admission, official MMBU generalization, learner-method novelty, a competition winner, or submission readiness.
