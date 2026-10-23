# Annotation-to-task lattice

**Date:** October 17, 2026  
**Status:** prospective training-data specification; no records admitted and no result claimed

## Purpose

MMBU measures related abilities through different interfaces: ungrounded classification, region-grounded
classification, and coordinate localization. The paper also analyzes closed and open answer forms, but the visible
current task card says to send `question` and not the separate `options` field. Closed-option views are therefore a
secondary robustness curriculum, not an official-task proxy, until later authority changes that input boundary. The training plan should exploit
an admitted source annotation across those interfaces without inventing medical facts, duplicating independent units,
or learning the public benchmark's wording. This document defines the deterministic transformations and the gates that
make that claim testable.

This is a task-aligned data strategy and governance contract, not a curriculum or architecture novelty claim. Schedule
order is separately ablated. It can be applied first to the base-architecture-preserving B2 model, pending loader
confirmation, and later, under the same records, to
B4 or an otherwise eligible research branch.

## Atomic source facts

Each admitted independent unit receives an immutable `independent_unit_id` before splitting. Its source may provide
only some of the following atoms:

- image identity and immutable bytes/hash;
- source ontology term and source label ID;
- global image label;
- instance class and instance identifier;
- instance mask;
- source-provided bounding box;
- source-provided count;
- source-authoritative modality, submodality, specimen, anatomy/region, stain, contrast, acquisition, or task-form
  metadata that the license permits us to retain.

Every atom keeps source, version, license, original split, annotation method, and reviewer status. A derived view may
use only atoms explicitly present in the same independent unit. It may not infer a diagnosis, prognosis, anatomy,
specimen, modality, or causal statement from visual appearance or filename conventions.

## Deterministic view graph

| Input atoms | Allowed output view | Deterministic rule | Required check |
|---|---|---|---|
| Global label | Ungrounded classification | Ask for the normalized source term; preserve an auditable source-to-display map | Round-trip display term to source ID |
| Instance class + source box | Box-grounded classification | Render that exact box with the frozen class-agnostic overlay compositor and ask for its normalized class | Box bounds, class/instance join, nonempty extent, overlay receipt |
| Instance class + mask | Mask-grounded classification | Render that exact mask with the frozen class-agnostic overlay compositor and ask for its normalized class | Shape/image match, nonempty mask, class/instance join, overlay receipt |
| Instance mask | Coordinate localization target | Convert positive support through a pinned half-open tight-box intermediate, then serialize original-image pixel `xywh` | Golden edge/corner/single-pixel fixtures and inverse round trip |
| Source box | Coordinate localization target | Convert the declared source convention to geometry-equivalent original-image pixel `xywh`; never emit normalized final coordinates | Source parse, transform/inverse transform, serialize round trip, and tolerance fixture |
| Complete valid instance set | Count answer | Count eligible instances after a pinned validity and border policy | Recompute from instance IDs; never count rendered boxes |
| Class + geometry | Grounded open answer | Ask for the class without answer options | Exact ontology serializer and accepted-synonym table |
| Class + geometry + admitted ontology | Secondary grounded closed answer | Add prospectively generated distractors from the admitted ontology; never label this the current official input profile | Distractor audit; no benchmark-derived options; secondary-purpose receipt |

No edge in this graph may use an MMBU public question, label, answer, image, embedding, model output, error bucket, or
prompt template. Public-set access remains confined to the separate evaluation firewall.

## Grounding-overlay contract

Box/mask-grounded views use one prospectively frozen compositor shared across sources, classes, splits, and candidates.
Stroke/fill color, width, alpha, z-order, antialiasing, label text policy, and resize order cannot encode class, source,
answer, or split. No class name, instance ID, confidence, source-specific palette, or hidden metadata is rendered. The
receipt binds original image hash, geometry atom, compositor version, rendered-pixel hash, dimensions, and inverse map.

The original unmodified image remains a paired control. Overlay-only crops are not new independent units. A geometry
perturbation control uses a registered transformation and is never relabeled as biomedical truth. If the source already
contains a burned-in overlay, that state is recorded and cannot be silently treated as an unmarked original.

## Prohibited transformations

- Do not convert a descriptive label into a diagnosis unless that diagnosis is the source annotation.
- Do not treat a caption, paper title, filename, or surrounding article prose as a verified patient label.
- Do not derive a mask from a box and then count the synthetic mask as independent spatial supervision.
- Do not create negative disease labels from the absence of an annotation.
- Do not infer that unannotated objects are absent; incomplete instance sets cannot produce count views.
- Do not mix ontology terms from sources with incompatible clinical meaning merely because their strings match.
- Do not make closed-answer distractors from MMBU options, frequency tables, or model mistakes.
- Do not assign multiple derived views to different splits or report them as additional independent samples.
- Do not use an image-absent or image-swapped example as biomedical truth; it is a diagnostic intervention only.

## Split-before-expansion invariant

1. Resolve exact and near-duplicate groups across all candidate sources before any view is emitted.
2. Bind every duplicate group, patient/study/specimen group, video/slide parent, and augmentation family to one
   `independent_unit_id` or one higher-level `split_group_id`.
3. Freeze train, validation, and held-out-source assignments on those groups.
4. Generate every task view only inside its already assigned split.
5. Reject a run if any content hash, perceptual-neighbor group, patient/study key, source parent, or derived-view lineage
   crosses a split.

Sample counts must be reported twice: number of views and number of independent units. Bootstrap intervals and all
promotion decisions use the independent grouping, not the inflated view count.

## Per-unit exposure and context invariant

Before source/task/context balancing, each independent unit receives the same total eligible optimizer mass. If unit
`u` emits `n_u` eligible views, the sum of its view weights is one unit mass; a default equal-within-unit allocation is
`1/n_u`, with any alternative frozen before results and constrained to the same sum. Token-level loss must also be
normalized so longer serializers or rationales do not silently restore annotation-density weighting. Report the final
mass by independent unit, source, task form, context field, and annotation density; maximum per-unit deviation from the
declared target is 1% before training can start.

Biomedical-context supervision is co-primary with answer-task supervision only where the source supplies a field in
the run's versioned requested-field registry. Every requested context field has an availability mask and an
authoritative atom ID. Missing fields receive no target loss and cannot be inferred from the source name, path,
question, prompt template, or another correlated field. Report every bound field separately before applying the
prospectively frozen context aggregation; follow the [context objective contract](CONTEXT_OBJECTIVE_CONTRACT.md).

Static interleaving, forward curriculum, reverse curriculum, and shuffled curriculum comparisons must use identical
independent units, views, total token exposure, per-unit mass, optimizer steps, templates, serializers, and seeds. If
forward ordering fails to beat static and shuffled schedules by the frozen margin, delete the curriculum claim.

## Task-consistency objectives

The primary supervised loss is always the loss for the emitted task view. Optional consistency terms may be enabled
only in a prospectively registered condition:

1. **Ontology consistency:** open and closed answers derived from the same class must normalize to the same source ID.
2. **Geometry consistency:** a mask-derived tight box and any source box for the same instance must meet a predeclared
   compatibility threshold or be quarantined rather than silently reconciled.
3. **Count-localization consistency:** only for complete instance sets, the number of serialized localization targets
   must equal the count atom.
4. **View agreement:** predictions on grounded and ungrounded views of the same atom may share a consistency term, but
   that term cannot replace the supervised target and must be ablated.
5. **Base preservation:** on an admitted general-preservation set, penalize negative flips relative to the frozen base;
   do not use public MMBU items for this set.

Image blanking, image swapping, question-only evaluation, and geometry perturbation are diagnostic probes. They never
create positive training labels. The exact interpretation follows the
[competition-recipe red-team](COMPETITION_RECIPE_REDTEAM.md): blank/no-image gaps are descriptive shortcut alarms, not
causal image-reliance rewards; answer-changing swaps or region changes require independently authoritative targets for
both sides. A model that improves ordinary validation while failing normal competence, answer-preserving invariance, or
answer-changing target tracking is not evidence that the spatial multi-view intervention worked.

## Secondary closed-answer construction

Closed questions are useful because the benchmark paper reports a large closed-to-open gap, but naive distractors can
create shortcuts. Under the visible current task card, separate options are judge-only and are not sent to the model;
these views therefore cannot establish official-protocol equivalence or drive the primary challenge-aligned promotion
endpoint. A secondary closed view is admissible only when:

- the candidate set is built from the frozen training ontology before model execution;
- the correct term appears exactly once after normalization;
- candidates are compatible with the task and source semantics;
- candidate sampling is source-balanced and drawn from the same frozen ontology depth/semantic neighborhood rather
  than source identity or global frequency;
- answer position is counterbalanced by a deterministic seed derived from the view ID;
- string length and superficial formatting do not identify the answer;
- normalized synonym/collision checks prove that two displayed choices do not map to the same source concept and that
  clinically distinct source concepts were not collapsed without medical review;
- no candidate or ordering was selected from public-set behavior; and
- the same independent unit's open view remains available for paired evaluation.

The closed-to-open delta is reported per independent unit and source. A gain confined to closed answers is a formatting
gain, not a sufficient medical-adaptation result.

## Required record fields

Each emitted view must bind at least:

```text
view_id
independent_unit_id
split_group_id
source_id
source_version
source_record_id
image_sha256
atom_ids
context_atom_ids
context_availability_mask
derivation_rule_id
derivation_rule_version
task_form
prompt_template_id
answer_serializer_id
license_id
review_status
split
unit_loss_mass
view_loss_weight
```

For geometry views, also bind the source coordinate convention, image dimensions, transform chain, output convention,
and a round-trip receipt. For closed views, bind ontology version, candidate source IDs, permutation seed, and correct
index. A view missing lineage is rejected, not repaired during training.

## Evaluation matrix

Every candidate condition is compared with the same admitted units and frozen training budget.

| Axis | Required slices |
|---|---|
| Task form | ungrounded class, box-grounded class, mask-grounded class, localization/count where valid |
| Answer form | current-card label/coordinate/count output; secondary closed robustness and paired closed-to-open delta reported separately |
| Generalization | seen source, held-out source, held-out task view, held-out source-task combination |
| Dependence | normal image, question-only, image swap, geometry perturbation |
| Safety | base negative flips, malformed-output rate, abstention/unknown where defined |
| Cost | trainable parameters, active FLOPs, peak memory, wall time, artifact bytes, offline-load time |

Use paired group bootstrap intervals keyed by `independent_unit_id`. Report macro-source and macro-task estimates beside
the pooled estimate so a large source cannot dominate promotion.

## Falsification and promotion gates

The task lattice is rejected as a useful competition intervention if any of the following occurs:

1. lineage or split-isolation validation fails;
2. gains disappear under independent-unit rather than view-level resampling;
3. the lower paired group-bootstrap bound does not exceed the frozen practical margin over same-budget B2;
4. improvement is confined to closed answers or one source;
5. visual-dependence probes do not improve for the spatial tasks;
6. open-answer, classification, context, or base-preservation performance materially regresses;
7. malformed serialization increases beyond the registered ceiling; or
8. runtime or packaging exceeds the challenge contract.

If it passes on B2, the same frozen view manifest becomes the common input for B4 and any research branch that first
passes its own eligibility gate. The manifest is never regenerated in response to their validation results.

## Evidence required before training

- admitted source ledger and license review;
- frozen ontology normalization and collision report;
- duplicate/split-group audit;
- transformation implementation with golden fixtures;
- frozen class-agnostic overlay compositor with shortcut/round-trip fixtures;
- view and independent-unit count report by source and task;
- human review sample selected before model output exists;
- signed manifest and hash for the final admitted views;
- frozen prompt, serializer, model pin, budget, seeds, metrics, margins, and stop rules; and
- MOCS native load/forward/export/reload receipt plus organizer-compatible packaging decision.

Until all items exist, the 8.5 competition-fit rating for multi-view annotation training in the portfolio is a design
judgment, not evidence of model quality. The broader dual-objective B2 flagship is rated separately.
