# Multi-profile candidate manifest v2 design

## Decision

Add `mmbu.competition.manifest` schema version 2 as an additive validator. Version 1 remains byte-for-byte and behaviorally unchanged. A v1 validator must reject v2 records and the v2 validator must reject v1 records.

Version 2 represents candidates as architecture/objective-profile pairs rather than requiring exactly one row for each architecture. It supports the five-arm causal experiment:

1. `B0` unchanged base;
2. `B1-L` task-only;
3. `B1-L` dual task/context;
4. `B2-P` task-only;
5. `B2-P` dual task/context.

`B2-F` remains an optional later architecture and obeys the same closure rules when present. This schema validates a design; it does not authorize execution, select scientific values, or create empirical evidence.

## Objective families

Every v2 objective profile adds `matched_objective_family_id`. Within one family there may be at most one task-only profile (`context_unit_share == 0`) and at most one dual profile (`context_unit_share > 0`). A dual profile is usable only when the same family has a task-only profile. Existing exact-rational share, exposure, context, and normalization rules remain unchanged.

`B0` has a null objective profile. Every other candidate resolves exactly one declared profile. Candidate IDs remain architecture-qualified and the pair `(architecture_id, objective_profile_id)` is unique.

## Candidate order

Candidate rows use the fixed architecture order `B0`, `B1-L`, `B2-P`, `B2-F`. `B0` appears exactly once and first. Within each non-base architecture, task-only candidates precede dual candidates and profile IDs are UTF-8 sorted within each mode. This makes the manifest representation deterministic without forcing every architecture to exist.

## Comparator closure

The comparator map contains exactly the enabled non-base candidates. Each comparator list is a unique UTF-8-sorted set and equals—not merely contains—the mechanically derived closure:

- every enabled candidate compares with `B0`;
- every dual candidate compares with the task-only candidate from the same architecture and objective family;
- every candidate above `B1-L` compares with the enabled candidate on the immediately simpler architecture with the same objective profile;
- an absent immediate control rejects the higher architecture rather than silently skipping a rung;
- disabled candidates and undeclared candidates cannot be comparator keys or comparator values.

Thus the five-arm closure is:

- `B1-L/task -> {B0}`;
- `B1-L/dual -> {B0, B1-L/task}`;
- `B2-P/task -> {B0, B1-L/task}`;
- `B2-P/dual -> {B0, B1-L/dual, B2-P/task}`.

These comparisons isolate, respectively, adaptation, context-objective contribution, architecture contribution under task-only training, and the interaction between architecture and the dual objective.

## Compatibility and claim boundary

Version 2 reuses the v1 authority, data, model, training, promotion, release, research-registry, unknown-value, digest, and state gates. Its canonical digest includes `schema_version=2`, the added family fields, all candidate rows, and the exact comparator map. A v1 digest or receipt cannot authenticate v2 bytes.

Passing v2 validation proves only that a synthetic competition design is closed and causally interpretable. It does not prove biomedical validity, learner novelty, performance, official-harness equivalence, source permission, compute feasibility, or competition readiness.
