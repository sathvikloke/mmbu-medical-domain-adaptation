# Phase 1 execution reproducibility contract

**Revision:** 2026-10-15-cycle-46e
**Status:** binding design contract; unimplemented and unexecuted  
**Scope:** engineering inference, one-step training, save/reload, resume, evidence generation, and later experiment runs

This contract distinguishes artifact identity, deterministic replay, numerical reproduction, and statistical replication. A weaker level may not be reported as a stronger one.

## Reproduction levels

| Level | Claim allowed | Required evidence |
|---|---|---|
| R-I identity | The same declared inputs exist. | Exact source state, data manifest, model/config/template/index/shard hashes, dependency artifacts, command, and environment record. |
| R-B bit replay | The same condition produced identical declared bytes. | Fresh process on the same frozen software/hardware topology; identical request bytes, token IDs, raw output bytes, checkpoint tensors/config, and evidence root where applicable. |
| R-N numerical replay | The same condition reproduced within a prospectively fixed tolerance. | Named compared tensors/metrics, tolerance and aggregation fixed before replay, environment/topology match or explicit difference, and full delta record. Never use this to excuse text/token drift in the Phase 1 deterministic inference fixture. |
| R-S statistical replication | Independent training seeds support the same decision. | Prospectively registered common seeds, unchanged estimand and decision function, per-seed results, and the required untouched confirmation. Evaluation-unit bootstrap alone is not training replication. |

Phase 1 deterministic one-image inference and same-environment reload require R-B token-ID equality. Later training claims require R-I plus the declared R-N/R-S evidence; cross-hardware bit identity is not assumed.

## Required run record

Every execution emits a schema-validated `reproducibility-record.json` before a claim can be `verified`. It contains or hash-binds:

1. UTC start/end timestamps, operator, host/job/allocation identifiers, exact command/arguments, working directory, exit code, stdout/stderr hashes, and declared purpose;
2. Git commit; clean/dirty state; canonical binary patch hash when dirty; source-state digest; contract-manifest digest; experiment/execution-condition/environment-launch-policy/environment-launch-receipt/lock/opening-receipt and opening-receipt-registry digests;
3. model, processor, tokenizer, template, tensor-index, shard, adapter, checkpoint, data, split, prompt/schema, evaluator, and output-manifest identities;
4. OS release, kernel, architecture, Python executable/hash/version, locale, timezone, filesystem type when relevant, and container image name plus immutable digest when used;
5. GPU model, UUID, compute capability, driver, CUDA runtime/toolkit, cuDNN, NCCL, compiler, PyTorch, Transformers, Accelerate/DeepSpeed/FSDP, attention kernel, quantization library, image decoder, and every imported package version;
6. dependency lock and resolver-report hashes, package artifact hashes where available, install command, index/source URL identities, and a rejection of editable, local-path, unhashed VCS, floating branch, nightly, or unconstrained dependency inputs;
7. the exact closed Phase 1A environment-launch policy and receipt: the child starts from an empty environment mapping, does not copy or inherit the parent environment, uses an absolute Python executable without a shell, and receives only the nine portable names `HOME`, `LANG`, `LC_ALL`, `PYTHONDONTWRITEBYTECODE`, `PYTHONHASHSEED`, `PYTHONPATH`, `PYTHONUTF8`, `TMPDIR`, and `TZ` with the fixed/derived values in `SCHEMAS.md`, plus only the exact UID-derived `__CF_USER_TEXT_ENCODING` row on Darwin; the launcher's passed mapping, the child's complete early `os.environ` capture, the execution condition, and this record are byte-equal, while the parent canary is present before launch and absent in the child;
8. world size, node/rank topology, launcher, rendezvous identity, visible devices and ordering, gradient-reduction policy, sharding policy, microbatch size, accumulation steps, effective batch, and uneven/remainder handling;
9. requested and effective precision, TF32 state, deterministic-algorithm state, cuDNN benchmark state, CUBLAS workspace policy, fused kernels/optimizer, compile mode, gradient checkpointing, and any fallback;
10. named seeds and RNG states for Python, NumPy if used, framework CPU, every CUDA device, sampler, data-loader generator/workers, augmentation, dropout, initialization, training, evaluation, bootstrap, and generation;
11. exact ordered independent-unit and record IDs per epoch, sampler state/epoch, batch membership, rejected/skipped rows, padding/truncation, processor outputs relevant to geometry, and realized record/target-token exposure;
12. cache roots and snapshot identities; network policy; every remote request or a verified offline replay; no hidden fetch may occur after the opening receipt;
13. optimizer, scheduler, scaler, gradient, RNG, sampler/data cursor, accumulation remainder, and checkpoint state needed for exact resume;
14. requested reproduction level, compared run, equality/tolerance rules fixed before replay, observed differences, and final reproduction status.

Peak memory, wall time, throughput, and the native forward/backward result do not enter this closed record as ad hoc fields. They are separate `mmbu.phase1.resource_measurement` and `mmbu.phase1.forward_backward` execution payloads under `SCHEMAS.md`, created before and hash-bound through this record's `output_digests`. For an evaluator run, `output_digests` is set-equal to the complete set of entry `sha256` values in the run's `mmbu.phase1.execution_output_manifest`; that manifest's four per-example layer populations are each set-equal to the governing `mmbu.phase1.example_manifest`. The execution-output manifest itself and later aggregate summaries are not members of `output_digests`, preventing self-reference. Raw counters and logs remain separate evidence members. This one-way binding prevents a provenance cycle while making estimated resources, changed synchronization, denominator drift, omitted output rows, undeclared gradients, and result-chosen tolerances mechanically rejectable.

A base/adapted task-change summary additionally binds one pre-output `mmbu.phase1.paired_condition_contract`, its complete `mmbu.phase1.execution_condition`, and both finalized runs. Each experiment, raw record, output manifest, run, and reproducibility record binds that same condition digest. Each reproducibility record carries the complete closed observed-condition projection and its ordinary environment fields independently agree with it leaf-for-leaf; digest equality alone is insufficient. Only the pairing contract's closed five model-identity fields may differ. A matching example manifest with different decoding, processor, prompt/schema, evaluator, parser, validator, judge, seed/RNG, retry/failure policy, runtime/software/device/topology, precision/backend, batching/order, request set, cache, network, or other effective condition is not a paired comparison.

The prospective execution condition binds `environment_launch_policy_digest`. The reproducibility record repeats it and binds the unique `environment_launch_receipt_digest`; the receipt resolves that policy and records exact passed and child mappings. The child's environment array is the policy's platform-specific `name`/`value` projection and no other entry. An unknown, inherited, missing, duplicated, reordered, or changed entry, policy/receipt mismatch, late child capture, or parent canary in the child fails closed. This construction replaces self-declared secret classification: the child cannot label an ambient value safe because ambient values never enter its mapping.

`pip freeze` alone is insufficient: it does not prove resolver inputs, wheel/source bytes, system libraries, drivers, build flags, or imported runtime state.

## Randomness and data-order registry

- One root experiment seed is expanded by a documented deterministic function into purpose-specific seeds. Reusing one integer everywhere without namespace separation is rejected.
- Seed names and values are frozen before the governed opening event. A seed selected after viewing outcomes creates a new exploratory lineage.
- Data-loader workers derive seeds from the frozen worker rule and record worker count, persistent-worker state, prefetch factor, and multiprocessing start method.
- Distributed samplers record epoch and ordered group/record IDs. World-size or rank-order changes create a new execution condition.
- Every failed, filtered, duplicated, or resampled record remains traceable. Silent replacement of a failed row or batch is prohibited.

## Kernel and precision policy

The runner requests deterministic algorithms where supported and fails closed on an unapproved nondeterministic operation in the Phase 1 replay fixture. It records backend-effective settings rather than configuration intent.

If a required training kernel is nondeterministic:

1. identify the exact operation and authoritative runtime warning/log;
2. use a deterministic supported alternative when it does not change the declared scientific condition;
3. otherwise declare R-B unavailable for that training path before results, freeze an R-N tolerance or R-S rule, and retain the operation as a named limitation;
4. never relax tolerance after seeing the replay delta.

Precision, attention implementation, compile mode, optimizer fusion, resolution, sequence length, device count, or gradient-reduction changes are new conditions, not invisible repairs.

## Cache and network isolation

The first authorized acquisition records exact URLs/revisions, resolved files, sizes, and hashes. A clean-cache replay then uses only the closed local artifact set with network denied. Hugging Face/Transformers offline modes and cache roots are explicit, but environment flags alone are not evidence; a network-denial probe must fail any attempted fetch.

The replay must not depend on a developer home cache, mutable symlink, local absolute path, credential, or unrecorded file. Missing content produces a failure, not a fallback to a moving remote revision.

## Save, reload, and interrupted-resume tests

Phase 1 requires two separate tests:

1. **Fresh reload:** a new process with empty runtime state loads the pinned base, saved adapter/modules, and processor from the closed artifact set; deterministic fixture token IDs and checkpoint/config hashes match.
2. **Interrupted resume:** on a synthetic native-collator training fixture, compare an uninterrupted short run with a run interrupted only at a declared checkpoint-safe boundary and resumed in a fresh process. The saved state includes optimizer, scheduler, scaler when used, every RNG, sampler/data cursor, accumulation state, and exposure counters. Require exact final tensor bytes when the frozen deterministic stack supports R-B; otherwise use a predeclared tensor/metric R-N rule and preserve the exact delta.

Restarting an epoch, changing batch order, repeating/dropping examples, or restoring weights without optimizer/RNG/data state fails resume equivalence.

## Required negative tests

Stable tests or an explicit behavior map must cover:

- dirty source state hidden or patch digest changed;
- wrong model index/shard, processor/template, data, prompt/schema, evaluator, or lock digest;
- floating/unhashed dependency, editable/local-path install, or resolver drift;
- warm-cache-only success and an attempted hidden network fetch;
- changed GPU order/world size, precision, TF32, attention kernel, compile/fusion, or deterministic flag;
- missing or colliding seed namespace; changed worker count/order; sampler epoch or record-order drift;
- failed row silently removed, duplicated, or replaced;
- checkpoint missing optimizer, scheduler, scaler, RNG, sampler/cursor, accumulation, or exposure state;
- resumed run repeating or skipping a batch;
- tolerance absent, result-chosen, applied to the wrong object, or used to excuse deterministic token drift;
- stdout/stderr/exit code omitted or a failed command reported as successful;
- child launch copies the parent mapping; the fixed parent canary is absent before launch or reaches the child; an unknown, inherited, missing, duplicated, reordered, or changed environment entry appears; `PATH` is added; a fixed value or derived path drifts; a path is relative, pre-existing where freshness is required, nonempty, hard-linked, symlinked, differently owned, or has the wrong permissions; Python is relative or invoked through a shell; policy, receipt, condition, and reproducibility projections disagree;
- resource record uses an estimate/public hardware specification, omits counter reset or synchronization, changes its condition, or reports throughput whose numerator and wall time do not recompute;
- forward/backward record omits a declared trainable pattern, records an undeclared gradient/update, lacks target-mask/manual-shifted-CE proof, or chooses its accumulation tolerance after the result.

## Acceptance and claim boundary

A generic green test suite, identical final scalar, or matching filename is insufficient. Each accepted claim maps to exact code, command, environment, inputs, outputs, logs, and hashes through the evidence trace.

Phase 1 may verify the schema, negative tests, B1 deterministic inference replay, fresh reload, and a bounded synthetic interrupted-resume test. It must not claim cross-hardware determinism, statistical replication, medical performance, or final training reproducibility. Those remain `untested` or `blocked_external` until the corresponding real run is repeated.
