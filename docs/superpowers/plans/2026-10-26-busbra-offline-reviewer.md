# BUS-BRA Offline Reviewer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a verified, self-contained offline browser interface that exports exact validator-compatible BUS-BRA train visual-review evidence.

**Architecture:** Reuse the existing train-packet verifier, transform the frozen manifest and receipt-bound PNG bytes into one escaped HTML document, and implement all reviewer interaction in embedded dependency-free JavaScript. Publish the HTML through exclusive hard-link creation so an existing output is never replaced.

**Tech Stack:** Python standard library, existing `mmbu_phase1` validators, HTML/CSS/JavaScript, `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-26-busbra-offline-reviewer-design.md`

## Global Constraints

- No network, server, external JavaScript/CSS, model, or biomedical source-archive access.
- The immutable packet and its receipt digest are required inputs and are never modified.
- The existing `VISUAL_FIELDS` and validator vocabularies are controlling.
- Generated output is a new regular file and never overwrites an existing path.
- The UI and its drafts never grant source admission, training, model-use, release, upload, or submission authority.

## Review Focus

- HTML-special characters in frozen or entered values must not become executable markup.
- CSV values containing commas, quotes, and newlines must round-trip to the Python validator.
- Drafts from another receipt or with unknown/missing records must be rejected.
- Missing or inconsistent required answers must block final export with record-specific feedback.
- An output-path race must preserve the competing file and fail closed.

---

### Task 1: Deterministic verified HTML generator

**Files:**
- Create: `src/mmbu_phase1/busbra_train_review_ui.py`
- Create: `tools/busbra_train_review_ui.py`
- Test: `tests/phase1/test_busbra_train_review_ui.py`

**Interfaces:**
- Consumes: `_verify_packet(packet_dir: Path, expected_receipt_digest: str) -> tuple[dict, dict]` and the receipt-bound asset paths in the train manifest.
- Produces: `build_review_ui(packet_dir: Path, expected_receipt_digest: str, output: Path) -> dict` returning a non-authoritative generation receipt.

- [x] Write failing tests for verified 108-style manifest rendering, receipt mismatch, symlink/non-PNG rejection, HTML escaping, no-network CSP, closed vocabularies, exact `VISUAL_FIELDS`, foreign-draft rejection markers, note/export guards, and no-overwrite publication.
- [x] Run `PYTHONPATH=src python3 -m unittest tests.phase1.test_busbra_train_review_ui -v`; expect failures because the module does not exist.
- [x] Implement the minimal Python generator and CLI, including strict asset checks, base64 PNG embedding, escaped canonical JSON bootstrap data, embedded review logic, and atomic exclusive file publication.
- [x] Run the focused test command; expect all tests to pass.
- [x] Run `python3 tools/team.py test`; expect the full Phase 1 suite to pass.
- [x] Commit the generator, tests, spec, and plan.

### Task 2: Operational documentation and real-packet generation

**Files:**
- Modify: `docs/team/BUSBRA_TRAIN_ONLY_EVIDENCE_SPRINT.md`
- Modify: `docs/team/BUSBRA_REAL_REVIEW_PACKET_2026-10-26.md`

**Interfaces:**
- Consumes: Task 1 CLI and the independently validated real train packet receipt.
- Produces: exact offline-generation instructions and a receipt for the real reviewer HTML artifact.

- [ ] Add fail-closed generation/opening/export instructions and the authority boundary to both documents.
- [ ] Extract the validated tar on node-local or local storage, generate the real HTML, verify its generation receipt and SHA-256, and publish it without overwriting prior evidence.
- [ ] Run focused tests, the full suite, link verification, compilation, and `git diff --check`.
- [ ] Commit and push the evidence/documentation update to PR #29.
