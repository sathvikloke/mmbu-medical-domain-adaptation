# Competition Lane 1 trainer design

## Intent

Implement the smallest end-to-end training lane that exercises the frozen five-arm competition design without opening
biomedical data, loading model weights, using a GPU, or making a scientific selection. The deliverable closes the current
software gap between one-step native preflights and a repeatable experiment loop. It is engineering evidence only.

The trusted human authorization is limited to implementing and testing this lane with CPU-only synthetic fixtures. It
does not authorize real data, model loading, GPU or HPC use, real-model training, MMBU evaluation, upload, or submission.

## Goals

- Execute exactly five arms: unchanged B0, B1-L task-only, B1-L dual, B2-P task-only, and B2-P dual.
- Consume a validated version-2 competition manifest instead of maintaining a second candidate definition.
- Keep the unchanged base free of optimizer updates.
- Give every adapted arm the same ordered independent units and optimizer-update count.
- Keep task-only and dual objectives distinct while preserving per-unit exposure accounting.
- Checkpoint and resume every adapted arm, then prove resumed state matches an uninterrupted reference.
- Export every final arm state, reload it through a fresh backend instance, and prove predictions match.
- Report task, context, and exact Track 2 proxy arithmetic against B0 without selecting or promoting a candidate.
- Reject non-synthetic, biomedical, public-MMBU, malformed, duplicated, or split-overlapping fixtures before execution.
- Provide a CPU-only CLI that writes one canonical result record and performs no network access.

## Non-goals

- No Qwen, Transformers, Torch, PEFT, model-cache, model-weight, GPU, Slurm, or HPC integration.
- No real biomedical source loader or label conversion.
- No hyperparameter, model, source, seed, threshold, or candidate selection.
- No claim of biomedical validity, learner novelty, performance, official-loader equivalence, or competition readiness.
- No change to the immutable historical bundle.

## Architecture

### Manifest-driven arm closure

`mmbu_phase1.lane1_trainer` validates a version-2 competition manifest with the existing Package F validator. It derives
the enabled candidates and exact comparator map from that validated record. The runner refuses any universe other than
the five authorized arms. Scientific literals that remain unknown in the design manifest stay unknown; the synthetic
runner uses a separate engineering configuration that cannot be promoted into a biomedical experiment record.

### Backend boundary

The orchestrator owns all file I/O and depends on a small in-memory backend protocol. A factory creates a fresh backend
with no arguments. The runner then calls:

- `initialize(base_state=bytes, arm=dict, seed=int) -> None`;
- `trainable_parameter_names() -> tuple[str, ...]`;
- `step(row=dict, objective_mode=str, learning_rate=Fraction) -> None`;
- `predict(row=dict) -> tuple[int, int | None]`;
- `dump_state() -> bytes` and `load_state(data=bytes) -> None` for checkpoints;
- `export() -> bytes` and `load_export(data=bytes) -> None` for final artifacts; and
- `base_state_bytes() -> bytes` to prove that initialization preserved the common base.

The runner creates distinct backend instances for uninterrupted, resumed, and export-reload paths. Every arm receives
the same immutable base bytes and seed. Before B0 evaluation or an adapted arm's first update, the reported trainable
names must equal the exact engineering configuration for that architecture. B0's tuple must be empty. B1-L and B2-P
must have fixed, nonempty, distinct tuples, with B1-L a proper subset of B2-P.

`mmbu_phase1.lane1_synthetic` implements that protocol with deterministic rational arithmetic over a tiny synthetic
state. It is deliberately incapable of opening files, importing model frameworks, or making network calls. A later
authorized VLM backend must satisfy the same observable contract.

### Closed records and fixture firewall

The fixture has exactly these top-level fields: `schema_id=mmbu.synthetic.lane1_fixture`, `schema_version=1`, a nonempty
`fixture_id`, `origin_class=synthetic_engineering`, `biomedical_content=false`, `mmbu_public_content=false`, nonempty
`train_rows`, and nonempty `evaluation_rows`. Each row has exactly `row_id`, `independent_unit_id`, `feature`,
`task_target`, and `context_target`. IDs are nonempty strings and unique across the entire fixture; `feature` is the
existing canonical reduced-rational wire type; `task_target` is integer 0 or 1; and `context_target` is integer 0 or 1
or null. Every training row must have a context target, and at least one evaluation row must have one. Unknown fields,
duplicate units, and train/evaluation overlap reject.

The engineering configuration has exactly `schema_id=mmbu.synthetic.lane1_config`, `schema_version=1`, nonnegative
integer `seed`, positive integer `epochs`, positive reduced-rational `learning_rate`, integer
`checkpoint_after_updates`, a 64-hex `allowed_fixture_digest`, and `trainable_names_by_architecture`. The latter is a
closed map for `recipe_arch::B0`, `recipe_arch::B1-L`, and `recipe_arch::B2-P`; each value is a UTF-8-sorted unique string
array. B0 must be empty, B1-L nonempty, and B2-P a proper superset. The checkpoint boundary must be strictly between
zero and `epochs * len(train_rows)`.

The declared negative flags alone do not prove provenance. Before the backend factory is called, the runner computes
the canonical digest of the complete fixture and requires it to equal `allowed_fixture_digest`. This binds execution to
the exact independently reviewed synthetic bytes. The claim is therefore limited to validating declared origin and a
trusted digest, not detecting biomedical meaning from arbitrary text.

### Execution and evidence

Each adapted arm runs twice in memory: once uninterrupted and once through a checkpoint boundary. The runner requires
byte-identical final state and identical predictions. It then exports, creates a fresh backend instance, reloads, and
requires identical predictions again. B0 performs no update and is evaluated from the common initial state.

Task accuracy `T` is exact correct task predictions divided by every evaluation row. Context accuracy `C` is exact
correct context predictions divided only by evaluation rows whose context target is not null. Every arm uses the same
complete evaluation set and applicability mask. The score proxy is exactly
`score_proxy(T, C, T_B0) = (4/5*T + 1/5*C) * (T - T_B0)`. Each manifest-derived comparator edge reports task, context,
and score-proxy deltas. Every rational in the result uses `rational.to_wire`; tests include a hand-worked fixture with
literal expected wires rather than recomputing expectations through production helpers.

The closed result contains schema/version, engineering-only evidence class, manifest/fixture/config digests, exactly
five ordered arm rows, every manifest-derived comparison row, and fixed limitations. Each arm row includes candidate,
architecture and objective IDs; `passed`, `failed`, or `not_run` status; update count; ordered-unit digest; trainable
names; rational metrics when available; resume-state, resume-prediction, and reload-prediction checks; and nullable
failure stage/message. Comparison rows are `available` with three rational deltas only when both endpoints passed, or
`unavailable` with null deltas otherwise. The result always records `scientific_selection_output_observed=false` and
has no selected-candidate field.

## Failure behavior

Manifest, fixture, digest, arm-closure, split, origin, objective, and update-budget errors raise before the backend
factory is called and produce no result. Runtime scope errors are checked before the affected arm's first update.
Any runtime update, checkpoint, resume, export, reload, state, prediction, or exposure error stops further work and
returns a closed five-row result: completed rows stay `passed`, the current row is `failed`, and every later row is
`not_run`. The CLI writes that failure result exactly once and exits nonzero. A preflight error creates no output.

The CLI accepts four explicit paths (manifest, fixture, configuration, and output), uses exclusive creation so an
existing output cannot be overwritten, and writes exactly `canonical.dumps(result) + b"\n"`. Tests deny and record
socket attempts, block imports of model frameworks including Torch, Transformers, and PEFT, and prevent backend file
access. CLI-owned input/output access is outside that backend guard.

## Verification boundary

Passing the Lane 1 synthetic suite proves that the five-arm orchestration, fairness checks, checkpoint/resume path,
export/reload path, and arithmetic work on deterministic CPU fixtures. It does not raise empirical medical performance
or learner-novelty claims. Its value is removing a concrete implementation blocker before admitted data and an
authorized VLM backend exist.
