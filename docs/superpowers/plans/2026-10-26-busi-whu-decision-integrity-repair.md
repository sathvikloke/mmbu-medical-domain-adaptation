# BUSI-WHU Decision-Integrity Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make protected BUSI-WHU review and confirmation fail closed unless custody, human authority, targets, geometry, duplicates, and execution inputs are transitively frozen.

**Architecture:** Add small closed-schema modules for protected-opening authority, stable descriptor I/O, human credentials, and duplicate evidence. Extend the existing BUSI-WHU review and held-out confirmation modules only at their decision boundaries, retaining the current deterministic selection and statistics. Real and synthetic confirmation constructors become visibly separate.

**Tech Stack:** Python 3 standard library, Pillow-free strict BMP parsing already in the repository, canonical JSON/Phase 1 `RecordStore`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-26-busi-whu-decision-integrity-repair-design.md`

## Global Constraints

- No real biomedical payload opening, source admission, model loading, GPU use, training, MMBU public-set access, upload, or submission.
- Canonical identity is `source_id="busi-whu"`, `source_version="3"`.
- Every new schema is closed; unknown keys, duplicate identifiers, missing digests, and unresolved decisions reject.
- Numeric geometry disagreement blocks until an independently frozen tolerance contract exists; no observed-data-derived tolerance.
- Every change is RED then GREEN, committed separately, and no readiness/novelty score rises from this repair.

## Review Focus

- Authorization whose credential record is created after it: reject in Task 1.
- Symlink, hard-link, path replacement, or mutation between validation and read: reject in Task 2.
- Consistent target flips across every result condition: reject in Task 4.
- Missing fingerprint inventory for any active eligible source: reject in Task 3.
- Duplicate adjudication IDs, duplicate pair keys, or conflicting source assessments: reject in Task 5.

---

### Task 1: Closed Human-Credential and Opening-Authority Records

**Files:**
- Create: `src/mmbu_phase1/busi_whu_authority.py`
- Create: `tests/phase1/test_busi_whu_authority.py`

**Interfaces:**
- Produces: `validate_credential_verification(record, path) -> dict`, `validate_review_attestation(record, path) -> dict`, `validate_review_opening_authorization(record, path) -> dict`, and `validate_busi_whu_review_opening(store, authorization_digest, opening_receipt_digest, now) -> ReviewOpeningCapability`.
- `ReviewOpeningCapability` is an immutable private-construction dataclass carrying authorized artifact, operation, output-root, registry, credential, and fingerprint-inventory digests.

- [ ] Write failing tests for closed keys, canonical source identity, four-role independence, verifier/reviewer separation, credential-before-authorization chronology, output-attestation-after-report chronology, exact operations, one attempt, active registry heads, and the Review Focus chronology case.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.phase1.test_busi_whu_authority -v`; expect failures for missing module/interfaces.
- [ ] Implement the minimal closed validators and transitive store checks; only `validate_busi_whu_review_opening` may construct `ReviewOpeningCapability`.
- [ ] Rerun the focused test; expect PASS.
- [ ] Commit with `feat: require protected BUSI-WHU opening authority`.

### Task 2: Stable Single-Open Artifact I/O

**Files:**
- Create: `src/mmbu_phase1/protected_io.py`
- Create: `tests/phase1/test_protected_io.py`
- Modify: `src/mmbu_phase1/busi_whu_review.py`

**Interfaces:**
- Consumes: Task 1 `ReviewOpeningCapability`.
- Produces: `open_authorized_artifact(capability, logical_path, role) -> ProtectedArtifact`; `ProtectedArtifact` exposes retained-descriptor bytes/stream, SHA-256, size, and pre/post stat proof and is context-managed.

- [ ] Write failing tests for exact logical-path/role resolution, non-symlink ancestors, `O_NOFOLLOW`, regular-file and link-count checks, pre/post identity stability, path substitution after open, and all four Review Focus filesystem attacks.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.phase1.test_protected_io -v`; expect RED.
- [ ] Implement retained-descriptor hashing/parsing and consume it in `build_review_packet`; remove path-hash-then-reopen behavior.
- [ ] Rerun Tasks 1-2 focused tests; expect PASS.
- [ ] Commit with `fix: read protected BUSI-WHU artifacts once`.

### Task 3: Frozen Targets, Geometry, and Cross-Source Fingerprints

**Files:**
- Create: `src/mmbu_phase1/image_fingerprints.py`
- Create: `tests/phase1/test_image_fingerprints.py`
- Modify: `src/mmbu_phase1/busi_whu_review.py`
- Modify: `tests/phase1/test_busi_whu_review.py`

**Interfaces:**
- Produces: `dhash64(grayscale_rows) -> int`, `hamming64(left, right) -> int`, `build_duplicate_candidates(records, source_inventories) -> list[dict]`, and review packet records carrying `canonical_target`, `target_map_digest`, workbook geometry metrics, decoded geometry evidence, and separately sealed task-manifest digests.

- [ ] Write failing tests for dHash Hamming 0/1/4 accepted and 5 rejected, aspect relative delta at/beyond 0.05, exact SHA match, complete eligible-source inventory closure, deterministic pair ordering, fixed target mapping, and geometry disagreement as unresolved.
- [ ] Run the fingerprint and review tests; expect RED.
- [ ] Implement the 64-bit dHash contract, source-registry closure, exact geometry evidence, sealed target map, and canonical identity migration.
- [ ] Rerun the focused tests; expect PASS.
- [ ] Commit with `feat: freeze BUSI-WHU targets and duplicate evidence`.

### Task 4: Authenticated Real Confirmation Boundary

**Files:**
- Modify: `src/mmbu_phase1/heldout_confirmation.py`
- Modify: `tests/phase1/test_heldout_confirmation.py`
- Modify: `config/phase1/busi-whu-confirmation-spec-2026-10-25.json`

**Interfaces:**
- Consumes: Task 3 target mapping/report/task manifests and Task 1 authenticated records.
- Produces: `build_authenticated_randomization_artifacts(review_report, confirmation_source_manifest, store, source_admission_digest, confirmation_purpose_digest, created_at) -> dict` and `build_synthetic_randomization_artifacts(fixture, created_at) -> dict`.

- [ ] Write failing tests proving the old arbitrary patient-map/digest route is unavailable to real execution; require exact target-map equality in source manifest, population binding, general lock, confirmation lock, result rows, and analysis; add the consistent-all-conditions target-flip test.
- [ ] Run the held-out confirmation tests; expect RED.
- [ ] Split the constructors, enforce synthetic provenance, re-resolve the full real chain, and migrate `busi-whu-v3` to canonical identity fields.
- [ ] Rerun the focused test; expect PASS.
- [ ] Commit with `fix: authenticate BUSI-WHU confirmation inputs`.

### Task 5: Complete Clinical and Source-Level Decisions

**Files:**
- Modify: `src/mmbu_phase1/busi_whu_review_validation.py`
- Modify: `tests/phase1/test_busi_whu_review.py`
- Modify: `tools/busi_whu_review_validation.py`

**Interfaces:**
- Produces: closed record decisions for intended lesion, grounded completeness, localization completeness, additional-lesion risk, plus independently signed clinical-adjudicator and data-custodian source assessments.

- [ ] Write failing tests for per-task narrowing, every present/unresolved source finding blocking, assessor disagreement blocking, duplicate adjudication ID/pair/group rejection, and no last-entry-wins behavior.
- [ ] Run the BUSI-WHU review tests; expect RED.
- [ ] Implement the closed decisions, independence checks, source blockers, and unique-key validation; require both pre-opening credentials and post-output attestations before `reviewer_identity_authenticated=true`.
- [ ] Rerun focused review/authority tests; expect PASS.
- [ ] Commit with `fix: close BUSI-WHU clinical decision gaps`.

### Task 6: CLI Fail-Closed Orchestration

**Files:**
- Modify: `tools/busi_whu_review.py`
- Modify: `tools/busi_whu_review_validation.py`
- Modify: `tools/busi_whu_confirmation.py`
- Create: `tests/phase1/test_busi_whu_cli.py`

**Interfaces:**
- Consumes: Tasks 1-5 public entry points.
- Produces: CLI routes in which real review accepts authority/receipt/store inputs only, real confirmation uses the authenticated constructor only, and synthetic execution requires an explicit synthetic fixture.

- [ ] Write failing CLI tests for missing authority, raw-path bypass, arbitrary real patient map, synthetic/real mode confusion, and one-attempt consumption after descriptor acquisition.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.phase1.test_busi_whu_cli -v`; expect RED.
- [ ] Rewire CLIs without compatibility fallbacks that weaken the new boundary.
- [ ] Rerun all BUSI-WHU and held-out tests; expect PASS.
- [ ] Commit with `fix: fail closed at BUSI-WHU command boundaries`.

### Task 7: Status Successor and Whole-Branch Verification

**Files:**
- Modify: `src/mmbu_phase1/status.py`
- Modify: `src/mmbu_phase1/authority.py`
- Modify: `tests/phase1/test_authority.py`
- Create: `docs/team/BUSI_WHU_DECISION_INTEGRITY_REPAIR_2026-10-26.md`
- Modify: `config/phase1/current-status.json` only through the tested successor builder.

**Interfaces:**
- Produces: `validate_status_transition(predecessor, successor) -> dict` and a canonical blocked-external successor status preserving the predecessor digest, audit blockers, repaired revision, and exploratory-only evidence classification.

- [ ] Write failing tests for predecessor digest preservation, monotonic chronology, immutable historical evidence, blocked-external status, and rejection of in-place/unrelated successor mutation.
- [ ] Run status/authority tests; expect RED.
- [ ] Implement transition validation, preserve the old canonical bytes as evidence, generate the successor, and document exact remaining blockers without raising scores.
- [ ] Run focused tests, then `PYTHONPATH=src python3 -m unittest discover -s tests/phase1 -v`, `python3 tools/team.py verify-links`, `python3 -m compileall -q src tools tests`, `git diff --check`, and `git diff --check $(git merge-base origin/main HEAD)..HEAD`; expect all green except documented expected skips.
- [ ] Commit with `docs: record BUSI-WHU decision-integrity repair`.
- [ ] Request one fresh whole-branch correctness/security/competition review; fix only demonstrated Critical/Important findings with RED-to-GREEN tests, then rerun the full verification set.
