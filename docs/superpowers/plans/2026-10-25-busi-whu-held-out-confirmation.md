# BUSI-WHU Held-Out Confirmation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CPU-only, fail-closed confirmation package that freezes and validates the BUSI-WHU held-out protocol without acquiring data, loading a model, training, or producing biomedical results.

**Architecture:** A closed JSON protocol specification feeds a pure Python validation and statistics module. The module validates immutable identities and gate references, builds exact patient-balanced estimands from synthetic or later authorized result rows, validates pre-output resampling artifacts, and emits a deterministic decision. A thin command reports readiness or validates synthetic fixtures; it has no network, model, scheduler, or biomedical-file path.

**Tech Stack:** Python standard library, repository canonical JSON and rational primitives, `unittest`, existing `tools/team.py` verification.

**Spec:** `docs/superpowers/specs/2026-10-25-busi-whu-held-out-confirmation-design.md`

## Scope and hard stops

- This plan authorizes source code, configuration literals, documentation, and CPU-only synthetic tests only.
- It does not authorize acquisition or opening of BUSI-WHU, BUS-BRA, PathMNIST, or MMBU content.
- It does not authorize model-weight loading, GPU/HPC use, training, inference, upload, or submission.
- Unknown real-world values remain blocking and must not be represented by synthetic placeholders in a real readiness receipt.

### Task 1: Freeze the closed protocol and test registration

**Files:**
- Create: `config/phase1/busi-whu-confirmation-spec-2026-10-25.json`
- Create: `tests/phase1/test_heldout_confirmation.py`
- Modify: `src/mmbu_phase1/scope.py`

- [x] Write failing tests proving the new module and protocol file are required and registered.
- [x] Freeze exact model ID/revision/parameter count, three seeds, LoRA literals, prompts, parser behavior, 1,024 updates, minimum 60 patients, 10,000 resamples, PRNG seeds, quantile index 999, strict `1/20` margin, one-attempt policy, and forbidden MMBU use.
- [x] Add negative mutation tests for unknown keys, model/revision drift, dropout drift, seed/update drift, prompt/parser drift, threshold drift, retry/rescue, BUS-UCLM substitution, and MMBU content permission.
- [x] Add `test_heldout_confirmation.py` to `REQUIRED_PHASE1_TEST_MODULES`.
- [x] Run the focused test and confirm it fails because the implementation is absent.

### Task 2: Implement the closed protocol validator

**Files:**
- Create: `src/mmbu_phase1/heldout_confirmation.py`
- Test: `tests/phase1/test_heldout_confirmation.py`

- [x] Implement exact-key, exact-type, exact-value validation with repository `ContractViolation` behavior.
- [x] Reject binary floats in every decision-bearing field and require canonical reduced rationals.
- [x] Validate that legacy exploratory adapters are ineligible and post-admission retraining is mandatory.
- [x] Validate the Qwen3.5-9B successor runtime-gate requirement and complete training-source purpose lineage references.
- [x] Make the focused validator tests pass.

### Task 3: Implement exact patient statistics and locked randomization artifacts

**Files:**
- Modify: `src/mmbu_phase1/heldout_confirmation.py`
- Modify: `tests/phase1/test_heldout_confirmation.py`

- [x] Write failing tests for patient-order drift, fewer than 60 patients, duplicate/missing condition rows, unequal image dropping, output failures removed from denominators, float arithmetic, and index/sign matrices generated after output.
- [x] Implement exact per-image, per-patient, per-seed, and family task/context calculations with `fractions.Fraction` converted only to canonical rational wire values.
- [x] Implement deterministic patient index and sign matrix construction from sorted UTF-8 patient IDs.
- [x] Validate matrix dimensions, values, canonical digest, creation chronology, and binding to the closed population before accepting result rows.
- [x] Compute the exact zero-based index-999 one-sided bound without interpolation and the exact sign-randomization diagnostic.
- [x] Make the focused statistics tests pass.

### Task 4: Implement the non-rescuable decision and diagnostics

**Files:**
- Modify: `src/mmbu_phase1/heldout_confirmation.py`
- Modify: `tests/phase1/test_heldout_confirmation.py`

- [x] Write failing boundary tests for equality at `1/20`, one nonpositive seed, lower-bound failure, incomplete replay, drift, secondary-score failure, and attempted seed/source substitution.
- [x] Require all three seed deltas, the family point estimate, and the one-sided bound to satisfy their exact rules.
- [x] Implement exact patient-balanced `T`, `C`, `Q`, class-conditioned scores, counts, and output-failure reporting as descriptive fields only.
- [x] Prove in tests that no secondary field or sign diagnostic can rescue or block the primary decision.
- [x] Emit only `confirmation_passed`, `confirmation_failed`, `underpowered`, or `blocked` with deterministic reason ordering.

### Task 5: Implement readiness and execution-envelope refusal

**Files:**
- Create: `tools/busi_whu_confirmation.py`
- Modify: `tests/phase1/test_heldout_confirmation.py`

- [ ] Write failing command tests for every missing admission/gate reference and for forbidden network, scheduler, data, model, and output actions.
- [ ] Implement `validate-spec`, `synthetic-check`, and `readiness` modes only.
- [ ] Make readiness report the first missing real record in frozen gate order and return nonzero while any value is unknown.
- [ ] Reject training-source authorization gaps, missing successor runtime evidence, old exploratory adapters, QA-order violations, outputs predating locks, repeated attempts, and any MMBU content lineage.
- [ ] Ensure the command never imports model, dataset, network, SSH, or scheduler libraries and never opens a referenced biomedical artifact.

### Task 6: Add synthetic conformance fixtures and adversarial coverage

**Files:**
- Create: `tests/phase1/fixtures/heldout-confirmation/positive.json`
- Create: `tests/phase1/fixtures/heldout-confirmation/underpowered.json`
- Create: `tests/phase1/fixtures/heldout-confirmation/threshold-failure.json`
- Modify: `tests/phase1/test_heldout_confirmation.py`

- [ ] Build a 60-patient synthetic positive case with no biomedical content.
- [ ] Add underpowered, exact-threshold, lower-bound, nonpositive-seed, parser-failure, chronology, matrix-drift, retry, and lineage-negative fixtures.
- [ ] Confirm every fixture declares `synthetic_only: true`, `biomedical_content_used: false`, and `mmbu_public_content_used: false`.
- [ ] Confirm synthetic pass results are labeled mechanics evidence only and never promotion or readiness evidence.

### Task 7: Verify, document, and seal the implementation

**Files:**
- Create: `docs/team/BUSI_WHU_CONFIRMATION_READINESS_2026-10-25.md`
- Modify: `docs/team/START_HERE.md`

- [ ] Document exactly what is implemented and every real-world blocker, including source admission, protected inventory, QA, training-source admission, successor runtime gate, checkpoint retraining, and authorization.
- [ ] Run `PYTHONPATH=src python3 -m unittest tests.phase1.test_heldout_confirmation -v`.
- [ ] Run `python3 tools/team.py test`.
- [ ] Run `python3 tools/team.py verify-links`.
- [ ] Run `git diff --check` and inspect the complete diff.
- [ ] Obtain an independent code review, repair demonstrated issues, rerun verification, and commit the sealed CPU-only package.

## Next experiment after this plan

No larger experiment follows automatically. Once this package is green, the next user decision is whether to authorize the real admission sequence for BUS-BRA and PathMNIST training lineage plus BUSI-WHU protected acquisition. The package must remain blocked until those records exist.
