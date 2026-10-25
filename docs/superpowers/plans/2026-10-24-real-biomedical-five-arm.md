# Real biomedical five-arm implementation plan

**Goal:** Produce the first reproducible external-only biomedical base-versus-five-arm evidence and rehearse the final
artifact shape offline, while keeping MMBU public evaluation, upload, and submission disabled.

**Spec:** `docs/superpowers/specs/2026-10-24-real-biomedical-five-arm-design.md`

## Phase 1: closed source compiler

- Add fail-closed BUS-BRA and PathMNIST source declarations with exact official checksums, licenses, split roles, prompts,
  labels, exclusions, and citations.
- Compile patient-safe BUS-BRA rows directly from the verified archive and reject case leakage, label drift, missing
  members, license drift, or the unresolved duplicate pair.
- Compile PathMNIST rows from the official NPZ and reject shape, count, checksum, label, or partition drift.
- Test both compilers with tiny synthetic archives/NPZ files before opening full data.

## Phase 2: native five-arm backend

- Generalize the proven Qwen loader, target-only label masking, PEFT scopes, weighted objective, and offline reload into a
  real Lane 1 backend.
- Enforce the exact five-arm universe and common base revision, seed, data order, exposure, image budget, and optimizer.
- Implement source-stratified answer and BUS-BRA context metrics plus canonical prediction receipts.
- Add CPU contract tests with fake model/processor objects; GPU behavior remains a bounded MOCS integration test.

## Phase 3: MOCS launch

- Stage the repository, verified model cache, BUS-BRA archive, and official PathMNIST artifact under a new scratch run
  root. Never mutate the previous preflight evidence.
- Run the five-arm bounded shakedown. Fix only demonstrated wiring defects, then freeze the full-run manifest.
- Run three fixed seeds for the unchanged base and eligible adapted arms, one A100 per job within the account job limit.
- Open confirmation partitions only after the winning rule is frozen.

## Phase 4: decision and packaging

- Aggregate source-stratified results, enforce the prospective promotion/kill rule, and preserve negative outcomes.
- Reproduce the selected checkpoint by offline reload.
- Build and validate an official-shaped local package with a generated model/data card and exact dependency/runtime record.
- Stop before any MMBU public evaluation, upload, or submission.

