# Competition Lane 1 trainer implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a CPU-only synthetic end-to-end runner for the frozen five-arm competition experiment.

**Architecture:** A manifest-driven orchestrator validates the exact five-arm universe, applies one backend protocol to
matched synthetic units, and emits a closed engineering-only result. A deterministic standard-library backend proves
checkpoint/resume and export/reload behavior without model weights or biomedical data.

**Tech Stack:** Python 3.11+ standard library, existing `mmbu_phase1` validators, `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-24-competition-lane1-trainer-design.md`

## Global constraints

- CPU-only synthetic fixtures; no biomedical or MMBU-public content.
- No model/framework import, model/cache/weight access, network, GPU, HPC, upload, or submission.
- Exactly five enabled arms in canonical order: B0, B1-L task, B1-L dual, B2-P task, B2-P dual.
- No scientific selection, promotion, or performance claim.
- All production behavior is written test-first and each task ends with a focused green suite.

## Review focus

- A disguised non-synthetic or public-MMBU fixture must reject before the backend initializes.
- Duplicate or train/evaluation-overlapping units must reject rather than change denominators.
- B0 must never receive an optimizer update or adapted parameter.
- Resume and fresh reload must reproduce state and predictions exactly.
- A missing, extra, reordered, or scope-drifted arm must reject before execution.

---

### Task 1: Closed fixture and five-arm execution contract

**Files:**
- Create: `src/mmbu_phase1/lane1_trainer.py`
- Create: `tests/phase1/test_lane1_trainer.py`
- Modify: `src/mmbu_phase1/scope.py`

**Interfaces:**
- Consumes: `competition_manifest_v2.validate_manifest(record)` and `expected_comparator_map(record)`.
- Produces: `validate_fixture(value) -> dict`, `resolve_arms(manifest) -> tuple[dict, ...]`, and
  `validate_config(value) -> dict`.

- [ ] Write closed-schema fixture/config builders and tests that reject non-synthetic origins, public/biomedical flags,
  unknown keys, duplicate row/unit IDs, split overlap, invalid rational wires, missing context applicability, invalid
  trainable maps, and a fixture digest mismatch before the backend factory is called.
- [ ] Write manifest tests proving exact canonical order and exact closure of B0, B1-L task, B1-L dual, B2-P task, and
  B2-P dual.
- [ ] Run the focused tests and verify they fail because the Lane 1 module is absent.
- [ ] Implement strict fixture/config validators and exact manifest-derived five-arm closure.
- [ ] Add `test_lane1_trainer.py` to the fail-closed Phase 1 test inventory.
- [ ] Run the focused tests and root orchestration inventory test; expect all to pass.
- [ ] Commit as `feat: define competition lane1 contract`.

### Task 2: Deterministic backend and matched training loop

**Files:**
- Create: `src/mmbu_phase1/lane1_synthetic.py`
- Modify: `src/mmbu_phase1/lane1_trainer.py`
- Modify: `tests/phase1/test_lane1_trainer.py`

**Interfaces:**
- Consumes: validated arms, fixture, and engineering configuration from Task 1.
- Produces: `SyntheticBackend`, `run_arm(...) -> dict`, and `run_lane1(...) -> dict`.

- [ ] Write spy-backend tests proving exact arm order, the same base bytes and seed for every instance, B0 zero updates,
  matched ordered units/update counts, architecture-specific trainable scope before the first update, task-only versus
  dual objective separation, and retention of all five result rows.
- [ ] Write a runtime-failure test in which the first adapted arm fails and the result still contains exactly five rows:
  B0 passed, the first adapted row failed, and all later rows not-run with no later updates.
- [ ] Run the focused tests and verify the new behavioral assertions fail.
- [ ] Implement the backend and minimal matched five-arm loop with finite rational arithmetic.
- [ ] Run the focused tests; expect all to pass.
- [ ] Commit as `feat: run matched synthetic lane1 arms`.

### Task 3: Checkpoint, resume, export, reload, and score evidence

**Files:**
- Modify: `src/mmbu_phase1/lane1_trainer.py`
- Modify: `src/mmbu_phase1/lane1_synthetic.py`
- Modify: `tests/phase1/test_lane1_trainer.py`

**Interfaces:**
- Consumes: completed arm states and predictions from Task 2.
- Produces: exact resume/reload comparisons, task/context metrics, Track 2 proxy values, comparator deltas, and one
  closed engineering-only result.

- [ ] Write tests that checkpoint after at least one but before the last update; compare uninterrupted and resumed runs
  from separate instances; corrupt checkpoint/export bytes; force resumed-state or reload-prediction drift; and use a
  third fresh instance for export reload.
- [ ] Verify literal, hand-derived rational wires for task accuracy over all evaluation rows, context accuracy over only
  applicable rows, score proxy against B0, and all manifest-derived task/context/score deltas. Prove the result has no
  candidate-selection field.
- [ ] Run the focused tests and verify the new assertions fail.
- [ ] Implement deterministic checkpoint/resume, fresh-backend export/reload, exact metric arithmetic, comparator deltas,
  explicit failure rows, and claim-boundary fields.
- [ ] Run the focused tests; expect all to pass.
- [ ] Commit as `feat: verify lane1 resume and reload`.

### Task 4: CPU CLI and repository verification

**Files:**
- Create: `tools/lane1_synthetic.py`
- Modify: `tests/phase1/test_lane1_trainer.py`
- Modify: `docs/team/REPOSITORY_MAP.md`

**Interfaces:**
- Consumes: `run_lane1(...)` from Task 3 and a canonical JSON manifest/fixture/config.
- Produces: a canonical JSON result at an explicit output path; no implicit repository output.

- [ ] Write subprocess tests proving the CLI succeeds offline, writes exactly `canonical.dumps(result) + b"\n"`, rejects
  overwriting, emits no file on preflight failure, writes one closed result and exits nonzero on runtime failure, and
  rejects malformed or non-synthetic input.
- [ ] Add socket-attempt denial/recording, forbidden model-framework import guards, and backend file-access guards so an
  offline green result cannot be faked by unused mocks.
- [ ] Run the focused tests and verify they fail because the CLI is absent.
- [ ] Implement the minimal CLI and document the new files and engineering-only claim boundary.
- [ ] Run the focused suite, then `python3 tools/team.py test`; expect zero failures.
- [ ] Commit as `feat: add lane1 synthetic runner`.
