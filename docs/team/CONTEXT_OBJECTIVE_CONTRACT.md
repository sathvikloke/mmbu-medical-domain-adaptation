# Biomedical-context objective contract

**Date:** October 17, 2026  
**Status:** prospective proxy specification; final organizer context prompt/schema remains unresolved  
**Claim boundary:** design only; no context-training or accuracy result

## Authority boundary

Track 2 includes a separate biomedical-context pass, but the organizer's exact final prompt, requested-field registry,
unknown convention, evaluator, and zero-applicable-field behavior are not yet available. The historical package supports
the internal names `modality`, `submodality`, `specimen`, `body_part`, `stain`, and `medical_domain`; those names are an
engineering snapshot, not a promise that the final official registry has four fields, six fields, the same names, or
the same aggregation.

Every run therefore binds an ordered requested-field subset from one versioned prompt/schema contract. Changing the
field registry, order, prompt, schema, parser, or evaluator creates a successor condition. Until organizer-confirmed
bytes exist, every context result is labeled `context_proxy`, never official-equivalent.

## Target admission

A context target is eligible only when all hold:

1. the exact field is present in the run's bound requested-field registry;
2. the value comes from a source-authoritative annotation or reviewed ontology mapping tied to the same independent
   unit;
3. the source version, atom ID, mapping version, rights, and reviewer disposition are recorded;
4. ambiguous, compound, missing, inferred, or conflicting values are masked unknown rather than coerced;
5. the value is not derived from an MMBU public row, public output, frequency table, prompt, source path, filename, or
   dataset name; and
6. the unit remains inside its pre-expansion split and duplicate/source-family group.

Candidate source atoms such as contrast phase, acquisition device, view, or task form do not automatically become
context targets. They may enter only when a later bound field registry explicitly requests them and the source mapping
passes admission.

## Training allocation

Task and context are separate model calls and separate target serializers. They may share an image and independent-unit
ID, but they may not share conversation history, hidden cache state, reference answers, options, or previous outputs.

For each unit, define one total optimizer mass before source/task/context balancing. The task share and context share
are prospectively frozen; neither the number of derived task views nor the number of annotated context fields can
increase the unit's total mass. Within a context target, available fields are normalized so a six-field record does not
receive six times the weight of a one-field record. Missing fields receive exactly zero target loss and are not
negative labels.

For the local proxy, request only the intersection of the bound proxy field registry and source-authoritative targets.
A missing or ambiguous source target is not asked, serialized, scored, or represented by an invented `unknown` token.
If that intersection is empty, the training policy reallocates the frozen context share to the task endpoint and the
evaluation policy excludes the unit from the context estimator while reporting it. These local policies preserve total
unit mass and are replaced—not silently retained—when the organizer publishes official unknown and zero-field rules.

Do not copy the score's `0.8/0.2` coefficients directly into loss weights: the official score is multiplicative and
loss scales differ. Compare a small closed set of prospectively fixed allocations under the same units, tokens, steps,
and seeds, then apply the frozen robust-selection rule. The final context prompt's absence blocks official context
claims, not task-independent native load/export engineering.

Do not multiply minibatch task and context surrogates to imitate the official score. For
`S = (0.8T + 0.2C)(T - T_base)`, the gradient is only a state-dependent weighted sum of the task and context gradients;
the product introduces no new update direction. Worse, the context coefficient is `0.2(T - T_base)`, so it has the
wrong sign while estimated task gain is negative. Batch-composition covariance and noisy base-gap estimates make a
minibatch product still less defensible. Train with the frozen ordinary allocation and use the score only in the
prospective, uncertainty-aware selection rule after the positive task-gain floor is met.

## Prompt and output invariants

- The model sees the image, the context system/user prompt, and the ordered requested fields—nothing from the task
  question, task answer, judge label set, or previous pass.
- The output contains exactly the locally eligible requested keys with nonblank string values under the bound proxy
  serializer; the official successor may differ.
- Extra, missing, duplicate, unknown, or reordered fields are handled exactly by the bound parser; local proxy behavior
  fails closed and never repairs output.
- A record with zero applicable fields is not silently scored as correct or incorrect. It remains outside the context
  estimator until the official policy is known, and its count is reported.

## Shortcut and generalization controls

Report context results by field, source family, modality family where independently known, and held-out source. Add
these diagnostics without turning them into training labels:

- source-family decodability from outputs and hidden summaries;
- performance after source-name/path/filename removal;
- lineage-disjoint paraphrases of the context prompt;
- burned-in text/overlay and acquisition-device strata;
- within-field label performance on a source family absent from training; and
- image-blank and wrong-image alarms, interpreted only alongside normal competence and authoritative answer-changing
  pairs.

A context gain confined to a source family, watermark, prompt wording, or nonvisual metadata pattern is not evidence of
biomedical visual adaptation.

## Evaluation and promotion

Before opening results, freeze:

- the applicable-field rule and zero-field policy;
- per-field metric and any ontology/synonym judge;
- field aggregation, macro-source aggregation, and uncertainty method;
- practical margins and simultaneous safety bounds; and
- the exact relationship between context proxy results and candidate selection while the official prompt is missing.

Report exact requested-set validity, per-field performance, macro-field performance, macro-source performance, field
coverage, zero-field count, and malformed rate. A scalar context proxy may be reported only beside those components.

The dual-objective intervention fails if task improvement is accompanied by a context decrease beyond the frozen
margin; aggregate context improves while any sufficiently supported field drops materially; gains disappear on the
held-out source family; requested-set validity worsens; source identity explains the gain; or the candidate cannot be
ranked robustly across the admissible official-context uncertainty range.

## Two context readiness states

`context_proxy_executable` permits training, local-proxy evaluation, and candidate selection only when the proxy field
registry, serializers, admitted targets, zero-field policies, aggregation, uncertainty range, and robust-dominance
decision function are all literal and prospectively hash-bound. Selection may use the registered proxy components and
the score interval over the frozen admissible official-context range; it may not use an unbound official-context point
estimate or claim official equivalence.

`context_official_equivalent` additionally requires organizer-confirmed prompt/schema bytes, field registry, unknown
and zero-field behavior, parser/judge/aggregation, and runtime. The official successor retires rather than silently
mutates the proxy condition. A frozen proxy result remains a proxy result.

## Evidence needed for official equivalence

1. final organizer prompt/schema bytes and ordered field registry;
2. unknown and zero-applicable-field policy;
3. exact parser, judge, aggregation, and runtime;
4. admitted source-field mappings with medical/rights review;
5. a frozen unit-normalized training manifest;
6. native base and adapted context outputs on external development roles only; and
7. held-out-source, output-validity, cost, and fresh-load receipts.

Items 1–3 are not prerequisites for `context_proxy_executable`; they are mandatory for
`context_official_equivalent`. Items 4–7 remain prerequisites for empirical context claims at either status.
