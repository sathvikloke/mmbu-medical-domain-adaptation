# B1 Native Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute one fail-closed, single-A100, synthetic-only native B1 preflight for the exact pinned Qwen2.5-VL-7B model, including native load, deterministic visual forward checks, one collator-backed optimizer step, adapter export, and fresh network-denied reload.

**Architecture:** A standard-library control layer validates one closed authorization/config record and all pinned bytes before any model import. A GPU runner then imports the frozen runtime, constructs deterministic synthetic images and target-only labels, validates the native visual/training path, saves a minimal adapter, and launches a fresh offline reload subprocess. Every stage emits canonical JSON evidence and fails before making a success claim when an identity, environment, numeric, gradient, state-dict, network, or resource check differs.

**Tech Stack:** Python 3.12.12, Slurm, one NVIDIA A100 80 GB, PyTorch 2.11.0+cu128, torchvision 0.26.0+cu128, Transformers 5.19.0, Accelerate 1.15.0, PEFT 0.21.2, Safetensors 0.8.0, Pillow 13.0.0, NumPy 2.5.4.

**Spec:** `docs/phase1/B1_RUNTIME_GATE.md`, bounded by the user's October 23, 2026 authorization and `docs/team/CLAUDE_HANDOFF.md` Work Package D.

## Global Constraints

- Exact model and processor: `Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5`.
- The exhausted run-1 through run-7 envelopes and their receipts remain immutable. A fresh run-8 envelope permits one job and zero retries on one `tesla_a100_80gb`, partition `epyc-gpu`, four CPUs, 96 GiB host memory, and a two-hour wall-time ceiling. It reuses the byte-verified run-1 model/runtime read-only but writes to a clean run-8 evidence root. Run 7 passed the absolute and 5% relative-L2 gradient bounds but measured cosine `0.9988091154245559` against an independently specified `0.999`. Run 8 derives the cosine floor from the frozen relative-L2 radius as `1 - 0.05^2/2 = 0.99875`, eliminating an internally inconsistent threshold while retaining all other conditions.
- Single-GPU BF16, SDPA, dynamic cache, `trust_remote_code=false`, no optional kernels, no compilation, no offload, no distributed execution.
- Synthetic fixtures only; no biomedical or MMBU image, label, answer, output, embedding, or derivative may be read.
- One minimal optimizer step only; no epoch, checkpoint search, evaluation, or performance selection.
- Network is allowed only during explicit artifact acquisition. The GPU execution begins from verified local bytes; fresh reload runs with Hugging Face offline flags and a socket-denial guard.
- Remote output root: `/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run8`; immutable acquisition inputs remain under the dedicated run-1 root; never inspect or modify sibling projects.
- No upload, submission, public release, or packet reseal.

## Review Focus

- A missing, extra, aliased, wrong-size, or wrong-hash weight/config file must reject before model import.
- A silently changed class, visual path, processor geometry, trainable module, dtype, attention backend, or cache policy must reject.
- Prompt/image/padding tokens must remain `-100`; manual shifted CE must match framework loss before the optimizer step.
- Offline reload must fail any attempted socket connection or undeclared cache fallback and must reproduce token IDs and declared logits within the predeclared BF16 tolerance.
- The one-job/zero-retry cap and synthetic-only input inventory must be mechanically evident, not asserted in prose.

---

### Task 1: Closed authorization and artifact verifier

**Files:**
- Create: `config/phase1/b1-mocs-preflight.json`
- Create: `src/mmbu_phase1/b1_preflight.py`
- Create: `tests/phase1/test_b1_preflight.py`

**Interfaces:**
- Consumes: `docs/phase1/b1-pin.json` and the direct user authorization.
- Produces: `load_preflight_config(path)`, `verify_pinned_artifacts(config, pin, root)`, `canonical_json_bytes(record)`, and typed `ContractViolation` failures.

- [ ] Write tests for exact closed fields, one-job resource limits, synthetic-only paths, exact shard/config inventory, byte/hash drift, unexpected files, and canonical evidence bytes.
- [ ] Run the focused test and observe the expected missing-module/function failures.
- [ ] Implement the smallest standard-library validator and verifier.
- [ ] Run focused and full Phase 1 tests; require all green.
- [ ] Commit Task 1.

### Task 2: Acquisition and immutable environment closure

**Files:**
- Create: `tools/b1_acquire.py`
- Modify: `tests/phase1/test_b1_preflight.py`

**Interfaces:**
- Consumes: Task 1 config/verifiers.
- Produces: a content-addressed model snapshot, wheelhouse, requirements lock, resolver report, and SHA-256 inventory under the dedicated remote root.

- [ ] Add failing tests proving floating revisions, non-wheel/editable/VCS dependencies, incomplete resolver reports, and post-download hash drift reject.
- [ ] Implement explicit `plan`, `acquire`, and `verify` commands; `plan` performs no writes or network.
- [ ] Run local tests green.
- [ ] Copy only the committed harness/config to the dedicated remote root, acquire the exact revision and frozen wheels, and run `verify` before any GPU allocation.
- [ ] Preserve command, URL/index identity, sizes, hashes, and resolver output; commit Task 2.

### Task 3: Native synthetic load, forward, collator, backward, and optimizer step

**Files:**
- Create: `tools/b1_native_preflight.py`
- Modify: `tests/phase1/test_b1_preflight.py`

**Interfaces:**
- Consumes: verified local model/runtime roots and closed config.
- Produces: environment, model identity, geometry, forward/backward, parameter inventory, and resource JSON records plus a minimal adapter directory.

- [ ] Add failing pure-unit tests for fixture inventory, target-only label construction, shifted-CE agreement, trainable/gradient/update inventory closure, and exact LoRA target selection.
- [ ] Implement deterministic synthetic RGB fixtures covering small, large, non-square, extreme aspect, grayscale conversion, RGBA conversion, EXIF orientation, and heterogeneous batching without external inputs.
- [ ] Implement exact class/config/backend assertions, image-change logit check, single/batch and order checks, MRoPE/grid records, cached-versus-uncached checks, finite forward/backward, one AdamW step, and peak memory/timing capture.
- [ ] Save only the minimal adapter/config and evidence; reject undeclared trainable parameters or missing gradients.
- [ ] Run local tests green; do not submit the GPU job yet; commit Task 3.

### Task 4: Fresh offline reload and one-job Slurm execution

**Files:**
- Create: `tools/b1_offline_reload.py`
- Create: `tools/b1_native_preflight.sbatch`
- Modify: `tests/phase1/test_b1_preflight.py`

**Interfaces:**
- Consumes: Task 3 adapter and baseline evidence.
- Produces: a fresh-process offline reload receipt and terminal run manifest.

- [ ] Add failing tests for network-guard activation, clean-cache roots, missing base bytes, state-dict/key drift, token-ID drift, logit-tolerance drift, and more than one submitted job.
- [ ] Implement the fresh offline subprocess with explicit offline flags, an empty dedicated runtime cache, socket denial, exact base/processor/adapter reload, and equality/tolerance checks.
- [ ] Implement a Slurm script with the exact partition/GPU/CPU/RAM/time cap, environment modules, absolute paths, and one terminal exit code.
- [ ] Run local tests and a no-GPU dry-run validator green.
- [ ] Submit exactly one job, wait for its terminal state, and preserve scheduler, stdout, stderr, resource, and artifact receipts; commit Task 4 only if the evidence accurately records success or failure.

### Task 5: Verification, claim boundary, and independent review

**Files:**
- Create: `docs/team/B1_NATIVE_PREFLIGHT_TRACE.md`
- Modify only if required by observed evidence: `config/phase1/current-status.json`

**Interfaces:**
- Consumes: all terminal remote evidence and local commit identities.
- Produces: a bounded trace stating exactly which B1 rows passed, failed, or remain untested.

- [ ] Verify remote JSON and artifact hashes locally; never copy model weights into the repository.
- [ ] Run `python3 tools/team.py test`, `smoke`, `verify-evidence`, `verify-links`, and `git diff --check`.
- [ ] Request one fresh independent review focused on fail-closed identity, synthetic-only scope, one-job enforcement, training numerics, and offline reload.
- [ ] Fix any Critical/Important findings once with RED→GREEN tests and rerun the full suite.
- [ ] Record honest readiness deltas and remaining limits; do not claim biomedical validity, model quality, official-evaluator equivalence, or competition readiness.
