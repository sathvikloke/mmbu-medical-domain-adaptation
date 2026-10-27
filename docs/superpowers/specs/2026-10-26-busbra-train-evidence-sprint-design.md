# BUS-BRA train-only evidence sprint design

**Date:** 2026-10-26
**Status:** accepted for native implementation under the user's standing instruction to choose the safest highest-value path

## Objective

Create the shortest honest path from the current zero-admitted-source state to a real-data engineering result. The
sprint prepares a purpose-scoped BUS-BRA visual/annotation review packet, validates completed human evidence, and emits
an admission-input projection for `train` only. After the resulting evidence passes the existing Phase 1 admission
chain, a later separately frozen run may execute a small Qwen3.5-9B base/task-only/dual engineering pilot.

This sprint does not itself admit BUS-BRA, authorize model use, run training, or establish clinical validity.

## Why this path

The repository is already strong on contracts, custody, synthetic conformance, runtime feasibility, and exploratory
response evidence. Another broad audit or governance-only repair cannot materially raise the scientific score. The
largest movable blocker is that no real source is admitted. BUS-BRA is the closest source because its exact archive,
patient groups, folds, decoded image/mask pairs, geometry, and duplicate-risk findings are already receipted.

The earlier 244-record packet combines training annotation fidelity with clinical and confirmation questions. That is
appropriate for decision-bearing evidence but unnecessarily burdens the narrower claim permitted by the repository's
purpose-tiered admission rule: exact publisher annotations may be used for training when visual/annotation QA passes,
without claiming those annotations are clinically correct.

## Scope and claims

The sprint proposes exactly one purpose: `train`.

If every downstream gate later passes, the strongest permitted statement is:

> The exact BUS-BRA 1.0 publisher-provided annotations were used for training under recorded provenance, rights,
> patient grouping, integrity, visual-QA, exclusions, and limitations.

The evidence must never be described as clinical validation, diagnostic correctness, confirmation performance, expert
verification, official MMBU performance, or permission to release weights.

## Inputs

The projector consumes an already built immutable BUS-BRA human-review packet v2 and its packet receipt. It never reads
the source ZIP directly and never mutates the predecessor packet. The predecessor supplies exact record identity,
patient identity, frozen image/mask assets, decoded dimensions, mask-derived boxes, and mandatory-reason flags.

Production pins bind:

- BUS-BRA version 1.0;
- the predecessor packet receipt digest;
- the 244-record predecessor manifest;
- the existing structural-transform contract; and
- cases 110 and 536 as unresolved provenance exclusions.

## Review population

The train-only packet contains:

1. every predecessor record with a mandatory visual/geometry reason, except unresolved provenance cases 110 and 536;
2. `bus_0845-s`, whether or not another rule already selected it; and
3. a deterministic patient-exclusive routine sample selected from the remaining records by stable SHA-256 rank until
   60 distinct routine patients are represented, or every available routine patient if fewer exist.

The routine sample size is a QA trigger, not a clinical prevalence claim. With zero critical routine failures, 60
independent patients gives a one-sided rule-of-three upper bound of 5% for the sampled visual/data-integrity failure
rate. Any critical routine failure blocks automatic readiness and requires a newly frozen expanded review plan; the
tool must not silently resample.

## Human worksheet

One accountable visual/annotation reviewer completes one row per selected record. The closed fields are:

- reviewer identity and UTC timestamp;
- asset match (`yes`/`no`);
- image interpretable for data QA (`yes`/`no`);
- declared ultrasound/breast modality support (`yes`/`no`/`uncertain`);
- mask visibly nonempty and aligned to the displayed target (`yes`/`no`/`uncertain`);
- material additional-target or annotation-completeness concern (`yes`/`no`/`uncertain`);
- shortcut/artifact code from a closed vocabulary;
- permitted training targets from a closed set;
- final disposition (`eligible`, `exclude`, `escalate`); and
- a nonblank note for every `no`, `uncertain`, `exclude`, or `escalate` response.

The worksheet does not ask whether pathology or BI-RADS is clinically correct. It asks whether the bound publisher
record and visual annotation are mechanically usable under the training-only claim.

## Rights and purpose worksheet

A separate accountable team rights/purpose reviewer binds the exact source version, license evidence, attribution,
planned training purpose, challenge disclosure, local retention, and the fact that weight release is not authorized by
this sprint. The only allowed purpose decision is `approve`, `narrow`, `decline`, or `unresolved` for `train`.
`narrow` must name an exact scope. Release, adaptive development, confirmation, submission, and upload remain false.

## Validator and receipt

The validator re-hashes every immutable predecessor member, validates exact worksheet rows and chronology, enforces the
closed vocabularies, and computes:

- eligible and excluded record IDs;
- eligible patient IDs;
- target-specific eligibility;
- every mandatory exception disposition;
- routine critical-failure count;
- the rule-of-three bound when applicable;
- unresolved/escalated records; and
- raw and canonical digests of completed human evidence.

It emits a deterministic `mmbu.busbra.train_qa_validation.v1` report. The report may set
`admission_input_ready=true` only when all rows are complete, every mandatory record has a terminal disposition, the
routine critical-failure count is zero, cases 110 and 536 are excluded, the rights decision is exactly compatible with
`train`, and no escalation remains. It must always keep `source_admission_authorized`, `training_ready`, and
`model_use_authorized` false. External authenticated attestations and the generic Phase 1 admission chain remain
mandatory.

## Engineering pilot boundary

No GPU job is part of this implementation. Once a real BUS-BRA `train` admission and purpose authorization exist, the
next experiment is one bounded Qwen3.5-9B three-condition engineering pilot:

- unchanged base;
- matched answer-only LoRA; and
- matched answer-plus-source-mask-context LoRA.

It uses patient-disjoint BUS-BRA folds, one fixed seed, a frozen unit budget, exact reload verification, and no MMBU
public examples. It is wiring/learning evidence only and cannot select a final model or raise clinical/confirmation
claims. A decision-bearing study still requires two additional independently admitted semantic families and three
seeds.

## Failure behavior

- Never overwrite an output directory or completed evidence file.
- Reject symlinks, path escapes, malformed UTF-8, duplicate IDs, unknown columns, unknown enum values, stale timestamps,
  digest drift, missing mandatory rows, and evidence predating the authorized opening.
- Preserve excluded and escalated records; never silently drop them.
- Never convert incomplete forms into approval.
- Never infer reviewer identity, qualification, rights, clinical truth, or source-author provenance.

## Deliverables

- `src/mmbu_phase1/busbra_train_qa.py`: deterministic projection builder.
- `src/mmbu_phase1/busbra_train_qa_validation.py`: completed-evidence validator.
- `tools/busbra_train_qa.py`: dependency-light CLI.
- `tests/phase1/test_busbra_train_qa.py`: synthetic, adversarial, and no-overwrite coverage.
- `docs/team/BUSBRA_TRAIN_ONLY_EVIDENCE_SPRINT.md`: operator/reviewer handoff with claim boundaries.

## Success criterion

The code is successful when it converts a verified predecessor packet into a smaller, purpose-scoped, tamper-evident
human-review surface and can prove whether completed evidence is mechanically ready to enter—never bypass—the generic
Phase 1 admission chain. Project score does not rise merely because this code exists; it can rise only after genuine
human evidence, admission, and real prospective execution.
