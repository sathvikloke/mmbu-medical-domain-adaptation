# Purpose-tiered Source Admission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow exact public dataset annotations to satisfy training-only QA without a clinical reviewer while preserving distinct clinical review for adaptive-development and confirmation evidence.

**Architecture:** Add one deterministic purpose-to-reviewer-role projection in the existing admission validator and make `check_qa_receipt` enforce that projection. Keep every other admission, custody, rights, grouping, attestation, and external-authority rule unchanged, then bind the claim boundary in maintained documentation.

**Tech Stack:** Python standard library, `unittest`, existing canonical Phase 1 validators and synthetic admission fixtures.

**Spec:** `docs/superpowers/specs/2026-10-26-purpose-tiered-source-admission-design.md`

## Global Constraints

- No real source admission, biomedical payload access, MMBU public access, model use, training, GPU/HPC use, upload, or submission.
- `visual_qa_reviewer` is required for every approved QA receipt.
- `clinical_qa_reviewer` is additionally required whenever purposes contain `adaptive_dev` or `confirmation`.
- Existing adjudicator, threshold, completeness, shortcut, custody, rights, grouping, and external-authority rules do not change.
- Training-only evidence may describe publisher-provided source annotations, never clinical validity.

## Review Focus

- Mixed `train` plus `confirmation` purposes must require both reviewers.
- Purpose order cannot alter the required-role projection.
- A clinical reviewer without a visual reviewer must still fail.
- Nonzero disagreement must still require the exact adjudicator attestation.
- Existing multi-purpose synthetic fixtures must remain valid without resealing production evidence.

---

### Task 1: Purpose-sensitive reviewer projection

**Files:**
- Modify: `tests/phase1/test_admission.py`
- Modify: `src/mmbu_phase1/admission.py`

**Interfaces:**
- Consumes: validated QA receipt `purposes` and bound reviewer attestations.
- Produces: `required_qa_reviewer_roles(purposes: Iterable[str]) -> frozenset[str]` and purpose-sensitive enforcement in `check_qa_receipt`.

- [ ] **Step 1: Write failing tests**

Add focused cases proving that train-only plus visual QA passes, missing visual QA fails, and either `adaptive_dev` or `confirmation` requires clinical plus visual QA. Include a mixed-purpose case and retain the existing disagreement test.

- [ ] **Step 2: Run the focused tests and verify the expected reviewer-role failures**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_admission.ReviewEvidenceTests -v`

- [ ] **Step 3: Implement the projection and replace the unconditional dual-role subset check**

Add `required_qa_reviewer_roles(purposes: Iterable[str]) -> frozenset[str]` in `src/mmbu_phase1/admission.py`. It returns `{"visual_qa_reviewer"}` plus `clinical_qa_reviewer` exactly when any purpose is `adaptive_dev` or `confirmation`. Use it in `check_qa_receipt`; do not change approved-attestation validation or adjudication.

- [ ] **Step 4: Run the focused and full admission tests**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_admission -v`

- [ ] **Step 5: Commit**

Commit message: `feat: tier source QA by intended purpose`

### Task 2: Bind the nonclinical training claim boundary

**Files:**
- Modify: `tests/phase1/test_evidence_documentation.py`
- Modify: `docs/phase1/SCHEMAS.md`
- Modify: `docs/team/DECISIONS.md`
- Modify: `docs/team/CURRENT_VERIFICATION.md`
- Modify: `docs/team/REPOSITORY_MAP.md`

**Interfaces:**
- Consumes: `required_qa_reviewer_roles` behavior from Task 1.
- Produces: maintained documentation that distinguishes publisher-annotation training from clinical evidence and states that no source or training action was authorized.

- [ ] **Step 1: Write a failing documentation-boundary test**

Require the phrases `publisher-provided annotations`, `does not establish clinical validity`, `adaptive_dev`, `confirmation`, and `no real source is admitted` in the maintained decision/spec surfaces.

- [ ] **Step 2: Run the test and verify it fails on the missing maintained boundary**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_evidence_documentation -v`

- [ ] **Step 3: Update maintained documentation**

Document the purpose table, unchanged external blockers, nonclinical claim language, and link the design from the repository map. Do not change any score, admitted-source count, candidate, track, or execution state.

- [ ] **Step 4: Verify documentation and repository consistency**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_evidence_documentation -v`

Run: `python3 tools/team.py verify-links`

Run: `git diff --check`

- [ ] **Step 5: Commit**

Commit message: `docs: bind purpose-tiered admission boundary`

### Task 3: Whole-repository regression verification

**Files:**
- Modify only if a demonstrated regression requires a focused repair.

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: fresh full-suite evidence for the revised admission contract.

- [ ] **Step 1: Run the complete supported verification**

Run the Phase 1 suite, root repository/tool suite, maintained-link verification, Python compilation, and `git diff --check` using the commands documented in `docs/team/CURRENT_VERIFICATION.md`.

- [ ] **Step 2: Record exact fresh counts only if all commands pass**

Update `docs/team/CURRENT_VERIFICATION.md` with the actual counts and explicitly retain zero admitted sources and no execution authority.

- [ ] **Step 3: Commit**

Commit message: `test: verify purpose-tiered admission`

