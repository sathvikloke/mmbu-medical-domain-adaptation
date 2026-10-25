# Track Decision and Bounded F0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a rules-grounded Track 2/Track 3 decision, a tested official-style context evaluator, and one bounded engineering feasibility receipt for each frozen model candidate.

**Architecture:** Keep competition strategy, evaluator mechanics, and native-model feasibility as separate evidence layers. The evaluator is a dependency-light module tested on synthetic records; the F0 runner consumes one closed JSON manifest and writes a terminal receipt even on failure. GPU jobs are launched only after the decision, evaluator, and manifest checks are green.

**Tech Stack:** Python 3.12, standard-library validation, PyTorch, Transformers, PEFT, Slurm, canonical JSON.

**Spec:** `docs/superpowers/specs/2026-10-25-track-decision-and-f0-design.md`

## Global Constraints

- Do not access or evaluate the MMBU public set.
- Do not run full training or a multi-seed adaptation campaign.
- Use generated-only F0 inputs and one A100-hour maximum per candidate.
- Give each candidate one attempt and do not rescue or expand a failed candidate automatically.
- Preserve all prior and failed evidence; never select a winner from F0.
- Stop after F0 and identify the exact next experiment requiring user approval.

## Review Focus

- Strict JSON must reject fences, duplicate keys, trailing objects, unknown/missing fields, and non-string values.
- Context scoring must average only the prospectively requested applicable fields and keep validity separate from correctness.
- The F0 manifest must reject floating revisions, duplicate candidates, candidate-specific scientific settings, and limits above one A100-hour.
- A failed native job must still retain candidate identity, stage, runtime, and error without fabricating later-stage evidence.
- Offline reload must run in a fresh process with network disabled and compare a deterministic prediction from identical bytes.

---

### Task 1: Amend the competition decision

**Files:**
- Modify: `docs/team/COMPETITION_DIRECTION_DECISION_2026-10-25.md`
- Modify: `docs/team/DECISIONS.md`
- Modify: `docs/team/REPOSITORY_MAP.md`

**Interfaces:**
- Consumes: official source map, organizer clarifications, completed Lane 1 trace, current public model metadata.
- Produces: one decision separating Track 3 primary hypothesis, Track 2 backup hypothesis, dual-track conditions, exact uncertainties, and switch evidence.

- [ ] Replace the Track-2-only conclusion and withdraw the uncalibrated fixed readiness score and fixed 80-A100-hour ceiling.
- [ ] Record score arithmetic, exact model shortlists/revisions, parameter-count uncertainty, dual-track conditions, and organizer questions.
- [ ] Run `python3 tools/team.py verify-links` and `git diff --check`.
- [ ] Commit the decision amendment.

### Task 2: Implement the official-style context evaluator

**Files:**
- Create: `src/mmbu_phase1/official_context.py`
- Create: `tests/phase1/test_official_context.py`
- Modify: `src/mmbu_phase1/biomedical_lane1.py`

**Interfaces:**
- Produces: `parse_context_output(raw: str, requested_fields: list[str]) -> dict` and `score_context_output(raw: str, target: dict, requested_fields: list[str]) -> dict`.

- [ ] Write failing tests for exact valid JSON, field-level partial credit, dynamic subsets, fences, duplicate keys, unknown/missing keys, trailing material, non-string values, and empty/unsupported subsets.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.phase1.test_official_context -v` and confirm failures.
- [ ] Implement the minimal closed parser/scorer and route Lane 1's diagnostic scorer through it only when official-style rows are supplied; preserve historical behavior for historical rows.
- [ ] Run the focused evaluator and Lane 1 tests and confirm all pass.
- [ ] Commit the evaluator repair.

### Task 3: Freeze and validate the F0 screen

**Files:**
- Create: `config/phase1/model-feasibility-screen-2026-10-25.json`
- Create: `src/mmbu_phase1/model_feasibility.py`
- Create: `tests/phase1/test_model_feasibility.py`

**Interfaces:**
- Produces: `load_manifest(path: Path) -> dict`, `validate_manifest(value: object) -> dict`, and deterministic candidate lookup.

- [ ] Write failing tests for the exact candidate/revision set and all constraint violations listed under Review Focus.
- [ ] Implement the closed manifest validator and frozen manifest.
- [ ] Run focused tests, then `python3 tools/team.py test`.
- [ ] Commit the freeze.

### Task 4: Implement one-shot native F0 receipts

**Files:**
- Create: `tools/model_feasibility_f0.py`
- Create: `tools/model_feasibility_f0_reload.py`
- Create: `tools/model_feasibility_f0.sbatch`
- Modify: `tests/phase1/test_model_feasibility.py`

**Interfaces:**
- Consumes: validated manifest and one candidate index.
- Produces: canonical `result.json` with terminal stage, exact identity, runtime/resources, LoRA update evidence, adapter inventory, and fresh-process reload result.

- [ ] Write failing tests for one-shot output refusal, offline environment enforcement, command construction, terminal failure receipts, and one-hour Slurm limit.
- [ ] Implement the architecture-neutral runner with explicit Qwen/InternVL compatibility adapters and a separate reload process.
- [ ] Run static/focused tests and the full CPU suite.
- [ ] Commit the F0 runner.

### Task 5: Execute the bounded screen on MOCS

**Files:**
- Create after execution: `docs/team/MODEL_FEASIBILITY_F0_2026-10-25.md`

**Interfaces:**
- Consumes: exact remote repository commit, exact snapshots, validated manifest.
- Produces: one preserved terminal receipt per attempted candidate and a descriptive feasibility matrix.

- [ ] Sync only the approved worktree to a unique remote run root and acquire exact candidate revisions without opening MMBU or biomedical data.
- [ ] Verify snapshot identity before GPU allocation.
- [ ] Submit at most five independent one-hour A100 tasks; do not resubmit a failure.
- [ ] Validate every receipt and describe pass/fail without ranking capability.
- [ ] Run focused repository verification after adding the trace and commit it.

### Task 6: Stop and report

**Files:**
- Create: `docs/team/MORNING_REPORT_2026-10-25.md`

**Interfaces:**
- Consumes: Tasks 1–5 evidence.
- Produces: plain report with primary/backup track, uncertainties, F0 pass/fail table, and exactly one next experiment requiring approval.

- [ ] Write the report without changing scores or promoting a model from F0.
- [ ] Run `python3 tools/team.py verify-links`, `git diff --check`, and relevant focused tests.
- [ ] Commit the report and stop without launching larger work.
