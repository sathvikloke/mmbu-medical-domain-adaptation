# Multi-profile Candidate Manifest V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an additive, fail-closed version-2 competition manifest that represents and validates the five-arm architecture/objective experiment without changing v1 behavior.

**Architecture:** A new `competition_manifest_v2` module reuses v1's closed shared-field validators and supplies only the v2 profile, variable-candidate, ordering, and comparator-closure logic. A new test module derives a v2 fixture from the existing v1 fixture, proves the desired five-arm record passes, and pressure-tests every causal closure edge and version boundary.

**Tech Stack:** Python 3.11+ standard library, `unittest`, existing `mmbu_phase1` canonical/rational/field validators.

**Spec:** `docs/superpowers/specs/2026-10-23-multi-profile-candidate-manifest-v2-design.md`

## Global Constraints

- Preserve every tracked byte and behavior of `mmbu.competition.manifest` schema version 1.
- Keep new production code under `src/mmbu_phase1` and CPU tests under `tests/phase1`.
- Use no MMBU public examples or derivatives, real biomedical content, model weights, GPU, network, or external upload.
- A valid v2 record is design evidence only and grants no execution authority.
- Canonical digest verification must cover every v2 field while omitting only `canonical_digest` itself.
- Candidate and comparator order is deterministic and fail-closed.

## Review Focus

- A dual candidate whose task-only control exists in a different family must reject; Task 2 adds `test_dual_candidate_rejects_cross_family_task_control`.
- A comparator map with all required edges plus one opportunistic edge must reject; Task 2 adds `test_comparator_map_rejects_extra_edges`.
- An absent immediate architecture control must reject rather than make the hierarchy ambiguous; Task 2 adds `test_hierarchy_rejects_missing_immediate_control`.
- A disabled candidate must not enter a comparator key or value; Task 2 adds `test_disabled_candidates_cannot_enter_comparator_map`.
- v1 and v2 receipts must not cross-authenticate; Task 1 adds `test_schema_versions_are_mutually_exclusive` and digest assertions.

---

### Task 1: V2 profile and candidate universe

**Files:**
- Create: `src/mmbu_phase1/competition_manifest_v2.py`
- Create: `tests/phase1/test_package_f_manifest_v2.py`

**Interfaces:**
- Consumes: v1 shared validators and `manifest_digest(record: dict[str, Any]) -> str` from `mmbu_phase1.competition_manifest`.
- Produces: `validate_manifest(record: Any) -> dict`, `manifest_digest(record: dict[str, Any]) -> str`, and `expected_comparator_map(record: dict[str, Any]) -> dict[str, list[str]]`.

- [x] **Step 1: Write the failing five-arm and version-boundary tests**

Add `valid_v2_manifest()` and tests named `test_five_arm_manifest_is_valid_and_digest_bound`, `test_schema_versions_are_mutually_exclusive`, `test_exactly_one_base_is_required`, `test_architecture_profile_pairs_are_unique`, and `test_candidate_order_is_canonical`.

- [x] **Step 2: Run the focused file and verify RED**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests/phase1 -p 'test_package_f_manifest_v2.py' -v`

Expected: import failure because `mmbu_phase1.competition_manifest_v2` does not exist.

- [x] **Step 3: Implement the minimum v2 shared validation, objective-family validation, candidate uniqueness, and canonical ordering**

Implement `manifest_digest(record: dict[str, Any]) -> str`, `validate_manifest(record: Any) -> dict`, and internal helpers in `src/mmbu_phase1/competition_manifest_v2.py`. Reuse v1 validators for unchanged fields; do not modify v1.

- [x] **Step 4: Run the focused file and verify the Task 1 tests pass**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests/phase1 -p 'test_package_f_manifest_v2.py' -v`

Expected: Task 1 tests pass; comparator tests may not exist yet.

- [x] **Step 5: Commit Task 1**

```bash
git add src/mmbu_phase1/competition_manifest_v2.py tests/phase1/test_package_f_manifest_v2.py
git commit -m "feat: add multi-profile competition manifest v2"
```

### Task 2: Mechanical comparator closure

**Files:**
- Modify: `src/mmbu_phase1/competition_manifest_v2.py`
- Modify: `tests/phase1/test_package_f_manifest_v2.py`

**Interfaces:**
- Consumes: validated v2 profile modes, family IDs, candidate pairs, enabled flags, and fixed architecture hierarchy from Task 1.
- Produces: `expected_comparator_map(record: dict[str, Any]) -> dict[str, list[str]]`, whose result is required byte-for-byte by `validate_manifest`.

- [x] **Step 1: Write failing causal-closure tests**

Add tests named `test_five_arm_comparator_closure_is_exact`, `test_dual_candidate_requires_same_architecture_task_control`, `test_dual_candidate_rejects_cross_family_task_control`, `test_higher_task_candidate_requires_simpler_task_control`, `test_higher_dual_candidate_requires_simpler_dual_control`, `test_comparator_map_rejects_missing_edges`, `test_comparator_map_rejects_extra_edges`, `test_disabled_candidates_cannot_enter_comparator_map`, and `test_hierarchy_rejects_missing_immediate_control`. Expected comparator literals must be hand-derived.

- [x] **Step 2: Run the focused file and verify RED**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests/phase1 -p 'test_package_f_manifest_v2.py' -v`

Expected: comparator-closure tests fail because exact closure is not implemented.

- [x] **Step 3: Implement exact comparator derivation and equality validation**

Implement hierarchy lookup, same-family task-control lookup, enabled-only closure, and exact map comparison. Reject missing, extra, disabled, cross-family, and ambiguous controls.

- [x] **Step 4: Run focused and v1 regression tests**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests/phase1 -p 'test_package_f*.py' -v`

Expected: all v1 and v2 Package F tests pass.

- [x] **Step 5: Commit Task 2**

```bash
git add src/mmbu_phase1/competition_manifest_v2.py tests/phase1/test_package_f_manifest_v2.py
git commit -m "test: close v2 comparator graph"
```

### Task 3: Contract documentation and repository verification

**Files:**
- Create: `docs/team/COMPETITION_MANIFEST_V2.md`
- Modify: `docs/superpowers/plans/2026-10-23-multi-profile-candidate-manifest-v2.md`

**Interfaces:**
- Consumes: public v2 functions and tested comparator rules from Tasks 1 and 2.
- Produces: reviewer-facing schema boundary, five-arm causal interpretation, and explicit non-authorization/claim limits.

- [x] **Step 1: Write the v2 contract note**

Document version separation, added family field, candidate ordering, the literal five-arm comparator table, B2-F extension rule, digest boundary, and scientific claim limits in `docs/team/COMPETITION_MANIFEST_V2.md`.

- [x] **Step 2: Run focused tests, full CPU suite, smoke, evidence, links, and whitespace validation**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests/phase1 -p 'test_package_f*.py' -v`

Run: `python3 tools/team.py test`

Run: `python3 tools/team.py smoke`

Run: `python3 tools/team.py verify-evidence`

Run: `python3 tools/team.py verify-links`

Run: `git diff --check`

Expected: every command exits 0; full Phase 1 test count is greater than the 302-test baseline.

- [x] **Step 3: Commit Task 3**

```bash
git add docs/team/COMPETITION_MANIFEST_V2.md docs/superpowers/specs/2026-10-23-multi-profile-candidate-manifest-v2-design.md docs/superpowers/plans/2026-10-23-multi-profile-candidate-manifest-v2.md
git commit -m "docs: specify five-arm manifest v2"
```
