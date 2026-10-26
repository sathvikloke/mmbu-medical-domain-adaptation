# Real-source admission Stage A implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and execute a fail-closed, one-attempt custody path from official source identity through protected structural inventory for BUS-BRA, PathMNIST-224, and BUSI-WHU v3.

**Architecture:** A closed JSON config freezes exact source identities and proposed purposes. A pure Python module constructs and validates acquisition/custody records, while small command-line tools create the sealed packet and execute one-shot transport or post-opening inventory. Existing Phase 1 validators remain the authority; new code composes them and never bypasses human rights, grouping, clinical, or admission attestations.

**Tech Stack:** Python 3 standard library, existing `mmbu_phase1` canonical/record validators, unittest, Slurm CPU jobs, official HTTPS endpoints.

**Spec:** `docs/superpowers/specs/2026-10-25-real-source-admission-stage-a-design.md`

## Global Constraints

- Work only in the current source-admission worktree and a new `/storage/scr/npl015/mmbu-admission/<UTC timestamp>-<random UUID>/` root.
- Never read MMBU public content, PathMNIST `test_*` arrays, or model weights.
- Never use GPUs, train, infer, upload, submit, overwrite evidence, resume a partial file, or retry an acquisition automatically.
- Fresh official acquisition is mandatory; preserved home archives are historical evidence only.
- The exact acquisition packet needs one digest-bound project-owner acknowledgment and independently verified acquisition-reviewer attestation before transport.
- Rights, grouping, clinical QA, candidate admission, and model-purpose authorization remain human gates.

## File structure

- `config/phase1/source-admission-stage-a.json`: closed source identity, purpose, population, transport, and duplicate-method declaration.
- `src/mmbu_phase1/source_admission_stage_a.py`: pure config validation, record construction, custody-graph verification, and safe inventory helpers.
- `tools/source_admission_stage_a.py`: CLI for packet building, graph verification, and protected inventory.
- `tools/source_admission_stage_a.sbatch`: create-once CPU transport/inventory entrypoint with no retry or resume.
- `tests/phase1/test_source_admission_stage_a.py`: synthetic positive and adversarial coverage.
- `docs/team/SOURCE_ADMISSION_STAGE_A_2026-10-25.md`: evidence report created only after execution.

## Review focus

- An exact file identity with an unlisted redirect host must block before transport; Task 1 pins this.
- A packet whose run root, command, byte cap, or repository commit changed after acknowledgment must reject; Task 2 pins this.
- Missing or stale registry/opening heads must prevent payload access; Task 3 pins this.
- Any request to read a PathMNIST `test_*` member must fail closed even after a valid opening; Task 4 pins this.
- Partial downloads, hash mismatches, and existing output paths must be preserved and must never trigger retry or overwrite; Task 5 pins this.

---

### Task 1: Freeze and validate official identities

**Files:**
- Create: `config/phase1/source-admission-stage-a.json`
- Create: `src/mmbu_phase1/source_admission_stage_a.py`
- Create: `tests/phase1/test_source_admission_stage_a.py`

**Interfaces:**
- Produces: `load_stage_a_config(path: Path) -> dict` and `validate_stage_a_config(config: object) -> dict`.
- Produces: exact `sources` keyed by `bus-bra`, `pathmnist-224`, and `busi-whu`, each with identity evidence, artifacts, host allowlist, proposed purposes, and population rules.

- [x] **Step 1: Write failing config tests**

Add tests asserting the three exact source IDs, exact BUSI-WHU file sizes/SHA-256 values, `train/release` for the two training sources, `confirmation/release` for BUSI-WHU, a 20 GiB work margin, and rejection of unknown keys, glob artifact names, duplicate names, unlisted redirect hosts, non-HTTPS locators, missing release-purpose review, and a PathMNIST population that contains `test`.

- [x] **Step 2: Run the focused tests and verify failure**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_source_admission_stage_a.StageAConfigTests -v`  
Expected: FAIL because the module/config do not exist.

- [x] **Step 3: Implement the closed validator and config**

Implement strict key sets, normalized basenames, positive integer sizes/byte caps, 64-character lowercase SHA-256 where frozen, sorted unique hosts/purposes, exact source roles, and the PathMNIST member deny rule. The config must bind the duplicate thresholds `dhash64_hamming<=4` and `aspect_ratio_delta<=0.05`.

- [x] **Step 4: Run the focused tests**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_source_admission_stage_a.StageAConfigTests -v`  
Expected: PASS.

- [x] **Step 5: Commit**

Commit message: `feat: freeze stage a source identities`

### Task 2: Build the sealed acquisition packet

**Files:**
- Modify: `src/mmbu_phase1/source_admission_stage_a.py`
- Create: `tools/source_admission_stage_a.py`
- Modify: `tests/phase1/test_source_admission_stage_a.py`

**Interfaces:**
- Consumes: validated Stage A config.
- Produces: `build_acquisition_packet(config: dict, repo_commit: str, launch_id: str, run_root: str, created_at: str) -> dict`.
- Produces: `validate_acquisition_packet(packet: object, config: dict) -> dict`.
- CLI: `python3 tools/source_admission_stage_a.py build-packet --config ... --run-root ... --output ...`.

- [x] **Step 1: Write failing packet tests**

Test deterministic packet creation, independent timestamp-plus-UUID launch IDs, exact run-root binding, exact repository commit, per-source artifact basenames/byte caps/commands/hosts, global forbidden operations, and rejection after any change to command, root, cap, source purpose, artifact identity, or repository commit.

- [x] **Step 2: Run the packet tests and verify failure**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_source_admission_stage_a.StageAPacketTests -v`  
Expected: FAIL because packet functions are absent.

- [x] **Step 3: Implement packet construction and CLI**

Seal the packet with RFC 8785 canonical hashing. Commands must use create-new output semantics, no retry/resume flags, one exact URL per artifact, and a staging path inside the sealed root. The CLI writes with exclusive creation and prints both canonical digest and full-file SHA-256.

- [x] **Step 4: Run packet tests and CLI smoke**

Run the packet test class, then build a temporary packet twice with identical inputs and assert byte-for-byte equality; both checks must pass.

- [x] **Step 5: Commit**

Commit message: `feat: seal stage a acquisition packet`

### Task 3: Compose and verify the mandatory custody graph

**Files:**
- Modify: `src/mmbu_phase1/source_admission_stage_a.py`
- Modify: `tools/source_admission_stage_a.py`
- Modify: `tests/phase1/test_source_admission_stage_a.py`

**Interfaces:**
- Produces: `build_preopening_records(packet: dict, acknowledgment: dict, acquisition_attestations: list[dict]) -> list[dict]`.
- Produces: `verify_inventory_opening(records: list[dict], source_id: str, now: str) -> dict` returning the validated active opening only.
- CLI: `verify-opening --records ... --source-id ... --now ...`.

- [ ] **Step 1: Write failing custody-chain tests**

Use synthetic artifacts to require the exact chain: acquisition attestation, acquisition authorization, registry head, execution receipt, source artifact manifest, candidate/quarantined source, quarantine split, quarantine-purpose authorization, successor registry, inventory lock, opening receipt, and opening-registry head. Add negatives for missing, stale, superseded, late, wrong-purpose, wrong-source, and post-lock record changes.

- [ ] **Step 2: Run tests and verify failure**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_source_admission_stage_a.StageACustodyTests -v`  
Expected: FAIL because custody composition is absent.

- [ ] **Step 3: Implement composition using existing Phase 1 validators**

Do not duplicate admission validation rules. Construct records with existing canonical helpers and validate them through `mmbu_phase1.admission`, `mmbu_phase1.locks`, and `RecordStore`. The project-owner acknowledgment is evidence of scope only; acquisition attestations must independently satisfy the existing role and verification contract.

- [ ] **Step 4: Run custody and existing admission suites**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_source_admission_stage_a.StageACustodyTests tests.phase1.test_admission -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: enforce stage a custody opening chain`

### Task 4: Add member-scoped protected inventories

**Files:**
- Modify: `src/mmbu_phase1/source_admission_stage_a.py`
- Modify: `tools/source_admission_stage_a.py`
- Modify: `tests/phase1/test_source_admission_stage_a.py`

**Interfaces:**
- Produces: `inventory_busbra(archive: Path, opening: dict, declaration: dict) -> dict`.
- Produces: `inventory_pathmnist(archive: Path, mapping: Path, opening: dict, declaration: dict) -> dict`.
- Produces: `inventory_busi_whu(archive: Path, workbook: Path, opening: dict, declaration: dict) -> dict`.
- Produces: `find_duplicate_candidates(records: list[dict], declaration: dict) -> dict`.

- [ ] **Step 1: Write failing synthetic inventory tests**

Create tiny synthetic archives. Assert complete joins, explicit exclusions, deterministic output, decoded-image hashes, dHash candidate rules, cross-source comparisons, BUSI-WHU underpowered status below 60 eligible patients, and immediate rejection of any PathMNIST `test_*` access. Assert inventory cannot start with a missing or mismatched opening.

- [ ] **Step 2: Run tests and verify failure**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_source_admission_stage_a.StageAInventoryTests -v`  
Expected: FAIL because inventory functions are absent.

- [ ] **Step 3: Implement minimal protected inventory functions**

Reuse existing BUS-BRA geometry utilities where their contracts match. Use a ZIP/NPZ member allowlist for PathMNIST and never invoke the existing full compiler. Parse BUSI-WHU joins using the frozen normalized-key algorithm. Emit evidence and blockers, never reviewer decisions.

- [ ] **Step 4: Run focused and related suites**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_source_admission_stage_a.StageAInventoryTests tests.phase1.test_biomedical_sources tests.phase1.test_heldout_confirmation -v`  
Expected: PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: add protected source inventories`

### Task 5: Add one-shot Slurm execution and evidence report

**Files:**
- Create: `tools/source_admission_stage_a.sbatch`
- Modify: `tools/source_admission_stage_a.py`
- Modify: `tests/phase1/test_source_admission_stage_a.py`
- Create after execution: `docs/team/SOURCE_ADMISSION_STAGE_A_2026-10-25.md`

**Interfaces:**
- Consumes: exact acknowledged packet and attestation records.
- Produces: one immutable run root with transport logs, receipts, manifests, custody records, inventories, and a repository-safe summary.

- [ ] **Step 1: Write failing launcher contract tests**

Assert the launcher requires an absent run root, verifies free bytes against sealed maximum plus 20 GiB, uses CPU only, uses exclusive-create outputs, contains no resume/retry flags, preserves partials and logs, validates hashes before custody construction, and exits before opening if any record fails.

- [ ] **Step 2: Run tests and verify failure**

Run: `PYTHONPATH=src python3 -m unittest tests.phase1.test_source_admission_stage_a.StageALauncherTests -v`  
Expected: FAIL because the launcher is absent.

- [ ] **Step 3: Implement the launcher and terminal receipts**

The launcher makes exactly one attempt per artifact, records the observed redirect hosts, bytes, hashes, and exit status, and never loops or submits child jobs. Post-opening inventory runs only after the complete graph verifier succeeds. Every terminal path writes a create-once status receipt.

- [ ] **Step 4: Verify locally, then execute once on MOCS after exact acknowledgment**

Run all Stage A tests, all Phase 1 tests, `python3 tools/team.py verify-links`, and `git diff --check`. After the sealed packet is acknowledged and independently attested, verify scratch capacity, stage the exact repository commit, submit one CPU job, and preserve its job ID/root.

- [ ] **Step 5: Validate results and write the report**

The report gives per-source pass/block status, exact receipts, first blocking human gate, and fixed false values for MMBU use, model loading, GPU use, training, and model-use authority. It must not raise novelty, readiness, or select a model.

- [ ] **Step 6: Commit**

Commit message: `evidence: record stage a source admission`

## Self-review result

- Spec coverage: every authorized and forbidden action maps to Tasks 1-5.
- Step scan: each task has one failing-test, implementation, verification, and commit loop.
- Type consistency: Task 2 packet feeds Task 3 records; Task 3 opening feeds Task 4 inventories; Tasks 2-4 feed Task 5 execution.
- Review focus: all five high-risk cases have an explicit owning test.
- Proportion: the plan fixes interfaces and evidence gates without transcribing implementation bodies.
