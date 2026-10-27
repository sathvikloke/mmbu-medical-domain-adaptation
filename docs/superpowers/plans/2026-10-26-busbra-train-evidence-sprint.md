# BUS-BRA Train-Only Evidence Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a fail-closed BUS-BRA training-only visual-QA packet and completed-evidence validator without admitting data or running a model.

**Architecture:** A projection builder reads only an immutable BUS-BRA review packet v2, deterministically selects mandatory records plus 60 patient-exclusive routine records, and writes a no-overwrite review packet. A separate validator re-verifies the predecessor and projected packet before validating human-completed visual-QA and train-rights forms and emitting a non-authoritative admission-input report.

**Tech Stack:** Python 3.11+, standard library, existing `mmbu_phase1.canonical` helpers, `unittest`

**Spec:** `docs/superpowers/specs/2026-10-26-busbra-train-evidence-sprint-design.md`

## Global Constraints

- Input is an immutable BUS-BRA human-review packet v2; do not read the source archive.
- Proposed purpose is exactly `train`; release, adaptive development, confirmation, upload, submission, and MMBU public-set use remain prohibited.
- Cases 110 and 536 remain excluded pending provenance resolution.
- Outputs are atomic and no-overwrite.
- No reviewer identity, qualification, decision, scientific value, or authority may be fabricated.
- Every emitted report keeps `source_admission_authorized`, `training_ready`, and `model_use_authorized` false.

## Review Focus

- A tampered predecessor asset or receipt must fail before projection or validation.
- Duplicate patients in the routine sample must never count twice toward the 60-patient floor.
- A missing mandatory row or unresolved mandatory disposition must block readiness.
- Any routine critical failure must block readiness without automatic resampling.
- Completed evidence predating the authorized opening, using unknown columns, or containing path escapes must fail.

---

### Task 1: Deterministic train-only packet projection

**Files:**
- Create: `src/mmbu_phase1/busbra_train_qa.py`
- Create: `tools/busbra_train_qa.py`
- Create: `tests/phase1/test_busbra_train_qa.py`

**Interfaces:**
- Consumes: immutable predecessor packet path and a caller-supplied new output path.
- Produces: `build_train_qa_packet(packet_dir: Path, output_dir: Path) -> dict` and CLI subcommand `build`.

- [ ] **Step 1: Write failing tests for exact deterministic selection, unresolved-case exclusion, predecessor tamper rejection, path-safety rejection, and output no-overwrite.**
- [ ] **Step 2: Run `PYTHONPATH=src python3 -m unittest tests.phase1.test_busbra_train_qa.BusbraTrainQaBuildTests -v` and confirm failures are from the missing implementation.**
- [ ] **Step 3: Implement closed-schema predecessor verification, stable patient-exclusive selection, templates, file hashes, receipt sealing, and atomic publication.**
- [ ] **Step 4: Run the focused build tests and confirm all pass.**
- [ ] **Step 5: Commit the builder and tests.**

### Task 2: Completed human-evidence validation

**Files:**
- Create: `src/mmbu_phase1/busbra_train_qa_validation.py`
- Modify: `tools/busbra_train_qa.py`
- Modify: `tests/phase1/test_busbra_train_qa.py`

**Interfaces:**
- Consumes: immutable projected packet, completed visual CSV, completed rights JSON, and authorized-opening JSON.
- Produces: `validate_train_qa(packet_dir: Path, completed_visual: Path, completed_rights: Path, opening: Path, expected_receipt_digest: str) -> dict` and CLI subcommand `validate`.

- [ ] **Step 1: Write failing happy-path tests plus negatives for incomplete rows, unknown enums, missing mandatory dispositions, routine critical failures, unresolved rights, chronology violations, tampered packet members, duplicate reviewers/rows, and output authority flags.**
- [ ] **Step 2: Run the focused validator tests and confirm failures are from the missing implementation.**
- [ ] **Step 3: Implement exact packet re-verification, closed-form parsing, chronology checks, deterministic eligibility projection, rule-of-three reporting, and the non-authoritative validation receipt.**
- [ ] **Step 4: Run all BUS-BRA train-QA tests and confirm all pass.**
- [ ] **Step 5: Commit the validator and tests.**

### Task 3: Operator handoff and repository registration

**Files:**
- Create: `docs/team/BUSBRA_TRAIN_ONLY_EVIDENCE_SPRINT.md`
- Modify: `docs/team/REPOSITORY_MAP.md`
- Modify: `docs/team/START_HERE.md`
- Modify: `src/mmbu_phase1/scope.py`
- Modify: `docs/team/CURRENT_VERIFICATION.md`

**Interfaces:**
- Consumes: Tasks 1 and 2 public CLI and schemas.
- Produces: a discoverable, exact operator/reviewer workflow with honest blockers and suite registration.

- [ ] **Step 1: Add a failing scope test or update the scope manifest so the new test module is included in the Phase 1 suite.**
- [ ] **Step 2: Document exact build/validate commands, reviewer fields, claim boundary, and the subsequent generic-admission and bounded-pilot gates.**
- [ ] **Step 3: Register the new files in the repository map and current verification without changing admitted-source count or scores.**
- [ ] **Step 4: Run focused tests, `python3 tools/team.py verify-links`, and `git diff --check`.**
- [ ] **Step 5: Commit the documentation and suite registration.**

### Task 4: Whole-branch verification

**Files:**
- Verify only; modify only demonstrated defects.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: a green branch and an exact remaining-blocker report.

- [ ] **Step 1: Run `PYTHONPATH=src python3 -m unittest tests.phase1.test_busbra_train_qa -v`.**
- [ ] **Step 2: Run `python3 tools/team.py test`, `python3 tools/team.py smoke`, `python3 tools/team.py verify-evidence`, `python3 tools/team.py verify-links`, and `python3 tools/team.py verify-contract`.**
- [ ] **Step 3: Run `python3 -m compileall -q src tools tests` and `git diff --check`.**
- [ ] **Step 4: Inspect the final diff for authority inflation, hidden data/model access, and stale documentation.**
- [ ] **Step 5: Record the exact human evidence still required; do not rescore before it exists.**
