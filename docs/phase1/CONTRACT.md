# Phase 1 engineering contract

**Status:** binding sanitized bootstrap contract; no Phase 1 implementation exists yet  
**Frozen:** 2026-10-14  
**Scope:** engineering runner, provenance firewall, evaluator plumbing, model/GPU smoke evidence, and local release preflight only

## Authority

Current official challenge rules, written organizer answers, and the exact official harness override this file. Any override must be recorded as a new contract revision with source hashes. Historical artifacts under `outputs/mmbu-precompute` remain immutable evidence and cannot override this contract for new work.

This repository file is the clone-resident source of truth for Phase 1. Machine-specific chat or audit paths are optional provenance, not execution dependencies.

`docs/phase1/OFFICIAL_SOURCE_MAP.md` is the manifest-covered sanitized extraction receipt for the official-rule assertions used here. It records source hashes, exact page/section locators, excluded content classes, independent review dispositions, and unresolved items.

## Fixed repository layout

- new package: `src/mmbu_phase1/`
- dependency-light CPU tests: `tests/phase1/`
- current-status source: `config/phase1/current-status.json`
- governing contract: `docs/phase1/`
- generated evidence: outside tracked source unless a reviewed fixture is intentionally committed
- historical compatibility reference: `outputs/mmbu-precompute/`, read-only

`python3 tools/team.py test` must run, in order:

1. historical `outputs/mmbu-precompute/tests`;
2. repository `tests`;
3. `PYTHONPATH=src python3 -m unittest discover -s tests/phase1 -v`.

The CPU package remains standard-library-only unless a reviewed extra is frozen. Native model/GPU probes use a separate environment and explicit `python3 -m mmbu_phase1.gpu_probe ...` entry point. They never run implicitly in ordinary CI.

## Nonnegotiable boundaries

1. Do not edit tracked bytes under `outputs/mmbu-precompute` or weaken its verification.
2. Do not use MMBU public examples, labels, annotations, outputs, statistics, or derivatives for training, prompt/base/checkpoint/seed/hyperparameter selection, early stopping, or promotion.
3. Developer-facing firewall tests use synthetic canary identities. Only a restricted role may compare against a real official hash index, without exposing example bytes or outcomes to developers.
4. Do not download or train on a real biomedical source until its exact version has signed rights, lineage, grouping, QA, and purpose approval. Clearly unrelated sources need not wait for a blanket contributor ruling; known or suspected MMBU-contributing sources do.
5. Do not start serious training, implement the final research loss, upload an external repository, or claim model improvement in Phase 1.
6. Task and context inference are separate stateless calls. Neither sees the other's output, label, grade, or hidden metadata.
7. No silent retry, JSON repair, answer extraction, coordinate clamping, field dropping, or denominator removal is allowed.

## Canonical purpose and origin vocabulary

Purposes are independent of dataset split:

- `engineering`
- `quarantine_inspection`
- `train`
- `adaptive_dev`
- `confirmation`
- `official_audit`
- `release`

Canonical origin classes are:

- `mmbu_official`
- `mmbu_derivative`
- `official_rule_summary`
- `external_reviewed`
- `external_quarantine`
- `synthetic_engineering`
- `unknown`

Unknown values fail closed. Legacy `development`, `dev`, `external-development`, `official_dev`, and split-as-purpose values require explicit migration rows and never map silently.

An `official_rule_summary` must contain only challenge rules, contract language, organizer answers, or non-example release metadata. It records source hashes and exact spans and cannot contain example IDs, images, labels, answers, outcome statistics, or example-derived choices.

Governance authority is not training ancestry. Every reference edge is typed as `governance`, `data`, `model`, `prompt`, `processor`, `judge`, or `decision`. A valid sanitized `official_rule_summary` may be bound in the `governance` role for any run purpose without entering the data/model/selection purpose intersection. It supplies constraints, never examples, targets, statistics, or preference signals. Untyped edges and attempts to relabel content-bearing or decision-bearing material as governance fail closed.

## Executable V2 schemas

Publish strict JSON Schemas or equivalent typed validators for source, split, purpose, lineage, experiment, run, current-status overlay, legacy migration, prompt/schema contract, prospective lock, opening receipt, and the four evaluation layers. Every schema fixes:

- schema name and version;
- required, optional, and nullable keys;
- unknown-key policy;
- canonical JSON encoding used for digests;
- cross-record reference targets;
- legal state transitions;
- digest and ancestry rules.

The runner validates and consumes the exact experiment-record digest, traverses all registered ancestors, verifies the requested purpose, and emits the consumed digest. A valid record beside an unrelated command proves nothing.

A prospective lock records its decision scope, source state, inputs, excluded results, exact opening event, candidates, seeds, thresholds, groups, evaluator, multiplicity family, compute plan, deterministic decision function, and claim boundary. An opening receipt binds the lock digest, source state, manifests, command/environment, operator, first output or protected-access time, expected runs, failures, and retries. Phase 1 implements only the schemas, chronology validator, and synthetic positive/negative tests; it does not fabricate an empirical lock. A late or changed lock can support a new exploratory lineage but cannot rescue the governed confirmatory result.

`config/phase1/current-status.json` is the only repository status authority. Evidence bundles contain only a byte-identical copy and digest.

## Prompt and schema authority

Every run binds one contract status:

- `synthetic`: engineering fixture only;
- `brief_snapshot`: faithful to published prose but not official-equivalent;
- `organizer_confirmed`: exact organizer-confirmed contract.

The run also binds exact task/context prompt and schema bytes, requested context fields per record, parser, validator, judge policy, inference settings, source hashes, and a contract digest. Unknown or mismatched contracts fail before inference. Do not guess task JSON property names or hard-code four or six context fields globally.

## Immutable evaluation layers

1. Raw: request/input hashes, token IDs, decoded text, finish reason, settings, timing, and runtime status.
2. Parsed: direct raw parent, parser version/status, parsed fields.
3. Validated: direct parsed parent, schema/field/geometry status.
4. Judged: direct validated parent, transitive raw/parsed ancestry, judge version/status, and grades.

When runtime fails before generation, generation fields may be null and downstream states must be `not_run`. Parse failure forces validation and judging to `not_run`; validation failure forces judging to `not_run`. Only valid validation may be judged. A frozen terminal policy keeps every manifest row in the denominator and assigns the declared no-credit outcome without manufacturing empty output.

## Required mechanics

- exact pinned B1 model and processor load from `docs/phase1/b1-pin.json`: model and processor `Qwen/Qwen2.5-VL-7B-Instruct` at repository revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`; floating revisions are forbidden; `trust_remote_code` is false unless a later reviewed pin explicitly changes it;
- native one-image preprocessing and stateless task/context calls;
- synthetic fixture covering classification, counting, one/many boxes, dynamic context subsets, malformed output, missing/inapplicable context, and failure states;
- fractional and weighted task-change identity;
- primary continuous task-change states `{positive, zero, negative}` plus a separate optional binary transition table;
- acquired/retained/lost/never visual-benefit states on verified answer-changing pairs;
- no silent box repair;
- real native collator, forward/backward, declared trainable-module gradients, minimal adapter save, and fresh-process reload;
- same-environment greedy token-ID and adapter/config hash replay;
- measured GPU/runtime record rather than estimates;
- local dummy release preflight only.

Multi-image support is out of Phase 1 unless an official need, ordered-image schema, fixture, and acceptance test are added.

## Evidence root

Each return contains a strict `evidence-manifest.json` governed by an executable schema. It lists every other bundle member's unique normalized POSIX relative path, byte size, SHA-256, media type, and `schema_id`/`schema_version` for schema-governed records or explicit nulls for raw logs and prose. Entries are regular files only: no absolute paths, empty components, `.`, `..`, backslashes, Unicode-normalization aliases, case-colliding aliases, symlinks, hard-link aliases, directories, or self-entry. Sort entries by UTF-8 bytes of the normalized path. Serialize the manifest as duplicate-key-free RFC 8785 canonical JSON encoded as UTF-8 with no BOM; the SHA-256 of those bytes is the deterministic bundle-root digest stored independently before review. Deleting, replacing, renaming, reordering, or aliasing a member must change or invalidate the root.

The bundle also contains `source-state.json`. It records the commit SHA, clean/dirty state, canonical binary patch hash when dirty, and path/size/SHA-256 inventory for every Phase 1 source, test, configuration, contract, and lock file. Test-command records and run manifests bind the source-state digest. Any source drift after evidence generation invalidates the bundle.

Every claim is exactly `verified`, `failed`, `untested`, or `blocked_external`. The overall phase decision is:

- `accepted`: all mandatory engineering, native model, GPU backward, reload, firewall, evaluator, schema, source-state, and evidence-root rows verify; the local release-preflight subclaim verifies while only the separate external-release lifecycle subclaim and real-source purpose controls may be blocked;
- `returned_blocked`: no rejection condition occurs, but at least one mandatory row lacks evidence;
- `rejected`: a mandatory row fails, public data contaminates development, historical bytes change, task/context state leaks, raw output is repaired or missing, failed rows disappear, evidence integrity fails, or unsupported claims are made.

Only `accepted` can advance to Phase 2. A clean narrative or generic green test suite cannot substitute for row-level evidence.

## Competition release boundaries

The current sub-27B candidates require public, ungated Hugging Face access and anonymous clean download. The published brief has a separate API route for models above 27B active parameters; such a branch requires organizer-compatible immutable endpoint/model and base access. Quantized-model eligibility is unresolved even though organizer inference is described as BF16/FP16, so disclose every dtype and do not invent a blanket ban.

The submitted system must be one end-to-end VLM. Ensembles, cascades, auxiliary models, external OCR, retrieval, learned preprocessing or postprocessing, and multi-model orchestration are prohibited. Multiple vision encoders are permitted only inside that one submitted VLM and every active parameter must be counted. The prohibition on external information or tool APIs during evaluation does not erase the separately published model-serving endpoint for a submitted model above 27B active parameters.

Every candidate and release record includes a component-wise active-parameter ledger for the vision encoder or encoders, language model, multimodal projector, and adapters. It declares how shared or tied parameters are counted and records the aggregation rule. Any MoE active-parameter interpretation remains unresolved until organizer-confirmed. Adapter-only repository eligibility is also unresolved; unless written organizer guidance says otherwise, release planning assumes merged or otherwise complete loadable weights rather than an adapter-only repository.

The exact Track 2 checkpoint revision cannot be entered in another track. Final records also require confidential team conflict/prize-eligibility review, anti-collusion attestation, official outputs/write-up disposition, and a submission receipt.

## Scientific boundary

Phase 1 prepares measurement only. The provisional two-budget method uses train-time compatibility surrogates, not direct control of continuous judge-score mass. Open-generation pairwise two-string margins are not binding because a third answer can win. Continuous negative mass, visual acquisition/loss, an independent secondary judge, a blinded human sample, and a repeated comparison against the strongest non-A4 baseline are later promotion gates.

Do not describe Phase 1 as scientific evidence, model readiness, official-evaluator equivalence, or competition improvement.
