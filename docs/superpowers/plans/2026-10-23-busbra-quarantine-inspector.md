# BUS-BRA Quarantine Inspector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, local-only BUS-BRA structural inspector that verifies a prospectively selected image/mask sample without granting any model-use purpose.

**Architecture:** A pure metadata planner freezes record selection before pixels open. A separate archive inspector verifies the exact pinned archive, opens only those frozen image/mask members, validates decoding, mask geometry, and within-sample exact duplicates, and emits a closed JSON receipt with `training_ready=false`. The existing CLI exposes both phases without network or model code.

**Tech Stack:** Python 3.11+, standard library, optional Pillow 12.3–12.x, `unittest`, existing `mmbu_prep` CLI.

**Spec:** `docs/team/BUSBRA_METADATA_GATE.md`

## Global Constraints

- The source is BUS-BRA 1.0, archive size `133917740`, declared MD5 `1f8b2be6476d58fc97bfb5e5a1ea9bab`.
- Selection depends only on frozen metadata and a versioned deterministic rule, never pixels, model behavior, or MMBU examples.
- `Case` is the independent unit; every `valid_*` field is prohibited.
- The inspector is local-only, opens only frozen sample members, never runs a model, never assigns train/dev/confirmation roles, and never grants source admission.
- Any malformed, mismatched, ambiguous, or changed input fails closed without publishing a partial output.

## Review Focus

- A plan created from different metadata must be rejected before any selected image or mask is read.
- Duplicate ZIP members, unsafe paths, encrypted entries, and archive checksum drift must fail closed.
- Image/mask dimension mismatch, empty masks, multichannel masks, and unexpected mask values must be reported as structural failures.
- Metadata boxes use `xywh`; mask-derived geometry must use the same half-open coordinate convention and report IoU without silently repairing either side.
- Sample-level duplicate absence must never be represented as corpus-wide duplicate clearance.

---

### Task 1: Prospective deterministic sample plan

**Files:**
- Create: `tools/busbra_quarantine.py`
- Create: `tests/test_busbra_quarantine.py`

**Interfaces:**
- Consumes: UTF-8 BUS-BRA `bus_data.csv` bytes.
- Produces: `build_sample_plan(metadata_bytes: bytes, *, per_stratum: int = 1) -> dict`.

- [ ] **Step 1: Write failing planner tests**

Test that the planner rejects duplicate IDs and `valid_*` influence, groups by `Case`, selects the lexicographically first record in each pathology × BI-RADS stratum, and binds the metadata SHA-256 and exact selected member names.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests/test_busbra_quarantine.py -v`
Expected: FAIL because `mmbu_prep.busbra` does not exist.

- [ ] **Step 3: Implement the minimal pure planner**

Implement strict CSV parsing, normalized BUS-BRA member naming, closed plan fields, and a canonical plan digest. Do not import Pillow or touch an archive.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest tests/test_busbra_quarantine.py -v`
Expected: planner tests PASS.

### Task 2: Fail-closed local archive inspection

**Files:**
- Modify: `tools/busbra_quarantine.py`
- Modify: `tests/test_busbra_quarantine.py`

**Interfaces:**
- Consumes: a local BUS-BRA ZIP path and the exact output of `build_sample_plan`.
- Produces: `inspect_quarantine(archive_path: Path, plan: dict, output: Path) -> dict`.

- [ ] **Step 1: Write failing archive-inspection tests**

Use tiny real PNG fixtures in a ZIP. Assert pinned archive identity, plan/metadata binding, selected-member-only reads, exact decoded hashes, mask values, derived bbox, bbox IoU, exact duplicate groups, and atomic publication. Add negative tests for malformed members, dimension drift, empty/ambiguous masks, and changed metadata.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests/test_busbra_quarantine.py -v`
Expected: FAIL because `inspect_quarantine` is absent.

- [ ] **Step 3: Implement the minimal inspector**

Verify the complete local archive hash before opening selected pixels, revalidate the metadata plan, inspect only frozen image/mask members with Pillow, derive mask geometry, and atomically emit `receipt.json`. Keep all eligibility and model-use flags false.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `python -m unittest tests/test_busbra_quarantine.py -v`
Expected: all BUS-BRA tests PASS.

### Task 3: CLI and evidence documentation

**Files:**
- Modify: `tools/busbra_quarantine.py`
- Modify: `tests/test_busbra_quarantine.py`
- Modify: `docs/team/BUSBRA_METADATA_GATE.md`

**Interfaces:**
- Consumes: local metadata/ZIP paths and a new output path.
- Produces: standalone `plan` and `inspect` CLI commands plus explicit limitations.

- [ ] **Step 1: Write failing CLI behavior tests**

Assert exclusive output creation, JSON-only stdout, nonzero JSON error output, and no network or model action.

- [ ] **Step 2: Run tests and verify RED**

Run: `python -m unittest tests/test_busbra_quarantine.py -v`
Expected: FAIL because the new commands are unknown.

- [ ] **Step 3: Implement CLI wiring and update the gate document**

Add the two commands and document that the inspector establishes sample-level structural evidence only; corpus duplicates, medical correctness, source proximity, rights, purpose admission, and release remain separate gates.

- [ ] **Step 4: Run focused and full verification**

Run: `python tools/team.py test && python tools/team.py test --images && python tools/team.py phase1-test && python tools/team.py verify-evidence && python tools/team.py verify-links`
Expected: every command PASS; image tests execute rather than skip in an image-enabled environment.

