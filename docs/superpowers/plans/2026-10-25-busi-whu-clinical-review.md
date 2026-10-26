# BUSI-WHU Clinical Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed, receipt-bound workflow that converts the sealed 927-record/816-patient BUSI-WHU metadata inventory into independently reviewed, task-specific confirmation eligibility without granting admission or model use.

**Architecture:** A new dependency-light module owns deterministic review selection, packet construction, and completed-review validation. It consumes the existing Stage A metadata inventory and emits canonical records that can later satisfy the existing `heldout_confirmation` readiness gate. Real image/annotation decoding remains a separately authorized execution; all repository tests use synthetic BMP/XLSX fixtures.

**Tech Stack:** Python standard library, Pillow only at the protected decode boundary already permitted by repository policy, canonical JSON helpers, `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-25-busi-whu-clinical-review-design.md`

## Global Constraints

- BUSI-WHU remains confirmation-only and must never enter training or candidate selection.
- The sealed predecessor contains exactly 927 records, 816 patient groups, 560 benign records, and 367 malignant records.
- The second-review population is all 149 records from 38 multi-record patients plus 50 hash-ranked benign singleton patients and 50 hash-ranked malignant singleton patients: exactly 249 records from 138 patients.
- No real biomedical payload may be decoded without a new digest-bound authority packet.
- Every generated artifact is canonical, one-shot, no-overwrite, and records `source_admission_authorized=false`, `training_ready=false`, and `model_use_authorized=false`.
- MMBU public content, model loading, GPUs, training, upload, and submission remain forbidden.

## Review Focus

- A patient with records carrying different labels must reject before selection rather than be assigned arbitrarily.
- Duplicate, missing, extra, or reordered predecessor records must change or invalidate the bound population digest.
- Hash-ranked selection must be byte-deterministic across input order and Python process.
- A primary/secondary disagreement without distinct adjudication must remain blocked.
- A mechanically valid review with missing qualification, chronology, purpose, or task eligibility must not become admission-ready.

---

### Task 1: Deterministic Review Selection

**Files:**
- Create: `src/mmbu_phase1/busi_whu_review.py`
- Create: `tests/phase1/test_busi_whu_review.py`
- Modify: `src/mmbu_phase1/scope.py`

**Interfaces:**
- Consumes: `build_review_selection(metadata_inventory: object) -> dict`
- Produces: canonical selection record with full population digest, primary record IDs, secondary record IDs, patient IDs, and frozen counts.

- [ ] Write failing tests for the exact 927/816 synthetic shape, all multi-record patients, 50 singleton patients per label, deterministic hash order, conflicting patient labels, and population drift.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.phase1.test_busi_whu_review -v`; expect failure because the module is absent.
- [ ] Implement strict predecessor validation and `SHA256(b"busi-whu-review-v1\\0" + parent_id.encode("utf-8"))` ranking.
- [ ] Register the test module in `REQUIRED_PHASE1_TEST_MODULES`.
- [ ] Rerun the focused tests; expect all pass.
- [ ] Commit `feat: freeze BUSI-WHU clinical review population`.

### Task 2: One-Shot Protected Review Packet Builder

**Files:**
- Modify: `src/mmbu_phase1/busi_whu_review.py`
- Create: `tools/busi_whu_review.py`
- Modify: `tests/phase1/test_busi_whu_review.py`

**Interfaces:**
- Consumes: `build_review_packet(archive_path: Path, workbook_path: Path, metadata_inventory: dict, selection: dict, output: Path) -> dict`
- Produces: immutable manifest, full-corpus decode inventory, duplicate candidates, review assets, pending worksheets, and packet receipt.

- [ ] Add failing synthetic tests for image/mask decode closure, dimension mismatch, nonbinary or empty annotations, duplicate candidates, no-overwrite behavior, and negative authority flags.
- [ ] Implement exact BMP decoding, annotation geometry, whole-corpus integrity checks, and atomic packet publication.
- [ ] Verify no model/MMBU imports or network access exist in the builder.
- [ ] Run focused tests and commit `feat: build BUSI-WHU protected review packet`.

### Task 3: Completed Human Review Validator

**Files:**
- Create: `src/mmbu_phase1/busi_whu_review_validation.py`
- Create: `tools/busi_whu_review_validation.py`
- Modify: `tests/phase1/test_busi_whu_review.py`

**Interfaces:**
- Consumes: immutable packet receipt, primary/secondary/adjudication forms, source rights/purpose form, and authorized opening record.
- Produces: canonical validation report with task-specific eligible/excluded patient and record IDs; all authority flags remain false.

- [ ] Add failing tests for qualification and chronology, complete primary coverage, exact secondary coverage, disagreement adjudication, task narrowing, unresolved exclusions, and separate purpose decisions.
- [ ] Implement closed schemas and transitive digest verification of every packet member and completed form.
- [ ] Emit exact eligible manifests but never an admission decision.
- [ ] Run focused tests and commit `feat: validate BUSI-WHU clinical review evidence`.

### Task 4: Confirmation Readiness Bridge and Full Verification

**Files:**
- Modify: `src/mmbu_phase1/heldout_confirmation.py`
- Modify: `tests/phase1/test_heldout_confirmation.py`
- Modify: `docs/team/REPOSITORY_MAP.md`
- Modify: `docs/team/CURRENT_VERIFICATION.md`

**Interfaces:**
- Consumes: authenticated Phase 1 admission digest plus Task 3 eligible-population digest.
- Produces: the existing `heldout_confirmation` source manifest and readiness gate inputs without changing its frozen prompts, candidate, seeds, margin, or statistics.

- [ ] Add failing tests that reject unauthenticated review reports, training-purpose leakage, fewer than 60 patients, cross-patient duplicate groups, and any post-lock mutation.
- [ ] Implement the minimal bridge; do not duplicate confirmation statistics.
- [ ] Run focused BUSI and held-out confirmation tests.
- [ ] Run `python3 tools/team.py test`, `python3 tools/team.py verify-links`, and `git diff --check`; require exit zero and a nonzero Phase 1 count.
- [ ] Commit `feat: bind BUSI-WHU admission to confirmation readiness`.

## Self-review result

- Spec coverage: selection, protected decode, independent review, adjudication, rights/purpose, task narrowing, and confirmation isolation each map to one task.
- Type consistency: every later task consumes canonical dictionaries and digests produced by the named earlier interface.
- Deliberate non-goal: the plan does not execute a real opening, authenticate reviewers, grant admission, train, or run confirmation.
- Existing code reuse: `heldout_confirmation` remains the sole owner of checkpoint lineage, bootstrap/randomization artifacts, scoring, and final pass/fail logic.
