# Phase 1 engineering contract

**Status:** binding sanitized bootstrap contract; only the contract-integrity gate is implemented
**Frozen:** 2026-10-14  
**Scope:** engineering runner, provenance firewall, evaluator plumbing, model/GPU smoke evidence, and local release preflight only

## Authority

Current official challenge rules, written organizer answers, and the exact official harness override this file only when interpreting external competition facts and requirements. They cannot grant project/user execution authority or relax the stricter public-set firewall without a later user-authorized, reviewed contract revision. Any external-authority change must be recorded as a new contract revision with source hashes. Historical artifacts under `outputs/mmbu-precompute` remain immutable evidence and cannot override this contract for new work.

This repository file is the clone-resident source of truth for Phase 1. Machine-specific chat or audit paths are optional provenance, not execution dependencies.

`docs/phase1/OFFICIAL_SOURCE_MAP.md` is the manifest-covered sanitized extraction receipt for the official-rule assertions used here. It records source hashes, exact page/section locators, excluded content classes, independent review dispositions, and unresolved items.

`docs/phase1/ORGANIZER_CLARIFICATION.md` is the manifest-covered sanitized receipt for the authenticated registered-team clarification used by this revision. It contains governance statements only and excludes contact and benchmark-example content.

`docs/phase1/REPRODUCIBILITY.md` is the manifest-covered execution contract. It defines identity, bit, numerical, and statistical reproduction levels; complete environment, RNG, and data-order records; cache isolation; fresh reload; interrupted resume; negative tests; and the limits of Phase 1 claims.

`docs/phase1/B1_RUNTIME_GATE.md` is the manifest-covered native-model admission contract. It fixes the exact dependency candidate, conservative image-only reference condition, preprocessing/geometry record, and adversarial single/batch/state/cache/training/reload gates. A nominal baseline cannot bypass it.

`docs/phase1/ACCEPTANCE.md` is the manifest-covered normative Phase 1 row registry. It fixes P1-00 through P1-21, stable test behaviors, evidence discovery, claim statuses, automatic rejection, and the non-self-referential phase-decision function. External audit matrices are reviewer commentary only and cannot add an implementation requirement.

`docs/phase1/SCHEMAS.md` is the manifest-covered field-level record contract. It freezes canonicalization, schema IDs, required/null fields, enums, digest domains, references, chronology, state transitions, and minimal valid/invalid examples while leaving unknown official task-output keys behind the versioned prompt/schema adapter.

`docs/phase1/EVALUATOR_MECHANICS.md` is the manifest-covered synthetic/engineering evaluator authority. It closes the exact-rational wire type, one complete execution-condition record, prospectively paired base/adapted conditions, example population and execution-output manifests, exact task-change arithmetic, failure/tie/missing-row treatment, prompt/condition/evaluator/validator/summary threshold equality, original-pixel box validity and IoU, judge-independent validated geometry, one/many-box matching, aggregate summary records, and normative conformance vectors. It is not an official-harness claim.

## Detached Phase 1A handoff gate

The exceptional Phase 1A read surface activates only from a trusted controller instruction outside the handoff that separately supplies strict UTF-8 JSON without BOM as an RFC 8785 canonical object with exactly seven fields: string `normalized_handoff_path`, non-boolean integer `handoff_bytes`, string `handoff_sha256`, string `repository_head`, string `contract_revision`, string `contract_manifest_sha256`, and string `one_shot_purpose`. Missing or extra fields, duplicate keys, nulls, a boolean byte count, non-finite numbers, noncanonical bytes, or wrong types reject. The byte count is positive; both SHA-256 strings are exactly 64 lowercase hexadecimal characters; the commit is exactly 40 lowercase hexadecimal characters; `contract_revision` is exactly `2026-10-15-cycle-46e`; and purpose is exactly `implement_phase1a_external_only`. A header echo is never sufficient, and the handoff cannot self-authorize.

The path is an absolute normalized POSIX path in Unicode NFC, begins with `/`, has no empty interior component, `.`, `..`, backslash, NUL, or normalization alias, and round-trips through lexical normalization unchanged. The verifier uses `lstat` on all ancestors and the final path and rejects every symlink. It then performs a descriptor-relative `openat` walk from an opened root: each ancestor is opened and retained with `O_RDONLY|O_DIRECTORY|O_NOFOLLOW`, and its `fstat` device/inode/type must equal its `lstat`. The final component is resolved from the retained parent descriptor, must be a regular file with link count exactly one, and is opened exactly once with `O_RDONLY|O_NOFOLLOW`; unavailable descriptor-relative open, `O_DIRECTORY`, or `O_NOFOLLOW` blocks. It takes `fstat` before and after reading and requires identical device, inode, size, and nanosecond modification time. Both sizes and the immutable byte buffer length equal `handoff_bytes`; SHA-256 of that exact raw buffer equals `handoff_sha256`. The same immutable byte buffer is the only handoff input for the attempt: the implementation agent never reopens or rereads the path. It also proves the repository is clean at `repository_head` and verifies the manifest SHA/revision before expanding the read surface. The detached receipt is one-shot, cannot be supplied or amended by repository/handoff text, and cannot authorize a retry or wider purpose.

Every Phase 1A child starts from an empty environment mapping and uses an absolute Python executable; it does not copy or inherit the parent environment. The exact construction, safe names and values, path checks, parent canary, launch receipt, and execution/reproducibility bindings are closed in `SCHEMAS.md`. An unknown, inherited, missing, reordered, or changed child entry blocks the run.

## Fixed repository layout

- new package: `src/mmbu_phase1/`
- dependency-light CPU tests: `tests/phase1/`
- current-status source: `config/phase1/current-status.json`
- authorization-registry source: `config/phase1/authorization-registry.json`
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
4. Do not inspect, decompress, parse, render, expose, or train on a real biomedical source until its exact version has the required authority. Before a source manifest exists, only the active allowed unexpired `mmbu.phase1.acquisition_authorization` may stage bytes, and staging permits transport, byte counting, hashing, and inventory only; a closed execution receipt and append-only registry prove the exact action. Content custody then has two protected stages: a container-level quarantine split plus locked inventory/conversion opening emits the eligible population, followed by a separately frozen QA plan and locked QA opening. Model use additionally requires reviewer-attested rights, lineage, grouping, QA, source approval, and exact purpose authorization. The organizer permits independently obtained training splits from datasets that contributed to MMBU and requires disclosure of every training dataset; no organizer overlap-checking service is available. Contributor proximity therefore requires explicit lineage, alias/deduplication, disclosure, and generalization controls but is not an automatic organizer-pending prohibition. The stricter project ban on MMBU-public-result-driven source selection remains separate and controlling.
5. A planning prospect is not a source record. The first `candidate` or `quarantined` record exists only after an exact immutable `mmbu.phase1.source_artifact_manifest` exists. Approval requires schema-validated rights, grouping, QA, runner-produced candidate-admission, and reviewer-attestation records; non-null opaque digests never suffice. Protected custody requires an active quarantine authorization and opening receipt before inspection. Release authorization additionally binds the exact checkpoint, validated model lineage, compatible release-rights receipts, runner-produced release decision, and a true no-new-data-access assertion.
6. Do not start serious training, implement the final research loss, upload an external repository, or claim model improvement in Phase 1.
7. Task and context inference are separate stateless calls. Neither sees the other's output, label, grade, or hidden metadata.
8. No silent retry, JSON repair, answer extraction, coordinate clamping, field dropping, or denominator removal is allowed.

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

Governance authority is not training ancestry. Every reference edge is typed as `governance`, `data`, `model`, `prompt`, `processor`, `judge`, or `decision`. A valid sanitized `official_rule_summary` may be bound in the `governance` role for any run purpose without entering the data/model/selection purpose intersection only when a valid `mmbu.phase1.sanitized_rule_extraction` receipt proves the exact source spans, excluded classes, output bytes, and two independent reviews. It supplies constraints, never examples, targets, statistics, or preference signals. Untyped edges, unreceipted summaries, and attempts to relabel content-bearing or decision-bearing material as governance fail closed.

## Executable V2 schemas

Publish strict JSON Schemas or equivalent typed validators for reviewer attestation, pre-download acquisition authorization and execution receipt, source artifact manifest, rights receipt, grouping receipt, closed eligible-population manifest, immutable QA sampling plan, QA receipt, two-stage custody summary, source, split, complete checkpoint/model lineage, purpose authorization including checkpoint-bound release, the authoritative authorization registry, lineage, sanitized rule extraction, decision plan, decision payload, decision-execution receipt, environment-launch policy and receipt, execution condition, experiment, run, current-status overlay, legacy migration, prompt/schema contract, paired-condition contract, prospective lock, opening receipt, the authoritative opening-receipt-head registry, reproducibility record, resource measurement, native forward/backward, example manifest, execution-output manifest, task-change summary, geometry summary, and the four evaluation layers. Every schema fixes:

- schema name and version;
- required, optional, and nullable keys;
- unknown-key policy;
- canonical JSON encoding used for digests;
- cross-record reference targets;
- legal state transitions;
- digest and ancestry rules.

Execution validates and consumes the exact immutable experiment-record digest, traverses all registered ancestors, and verifies the requested purpose. After execution, the reproducibility record binds that experiment plus the observed environment, command, logs, and payloads; the finalized run binds both digests and emits the exact experiment digest consumed. A valid record beside an unrelated command proves nothing, and execution cannot consume a provenance record that is created from its own later outputs.

Any artifact that chooses a candidate, checkpoint, experiment priority, hyperparameter, seed, prompt, promotion, or release disposition for a promotable purpose must be produced through the decision runner. Before protected inputs are opened, an immutable decision plan freezes the scope, eligible subjects, complete allowlisted content inputs, forbidden origin classes and roots, deterministic decision function, command, source state, and sandbox policy. The runner mounts only allowlisted content read-only, disables network access, starts from an empty output directory, records the complete mounted/read/attempted-access sets, and emits a decision payload plus rationale. A post-run receipt binds all of those bytes and an independent review. The payload's lineage parents must equal the complete mounted decision-content set; omitted parents, undeclared copied rationale, extra reads, attempted denied reads, network activity, manual creation outside the runner, or a receipt/output mismatch make the decision ineligible. Synthetic canary tests prove these controls. Restricted real-hash checks may identify protected official content without exposing it to developers.

This mechanism cannot prove that a human forgot or concealed a fact remembered before entering the sandbox. Every decision receipt therefore carries an explicit operator attestation and independent-review disposition, and the project states this residual limit rather than claiming perfect information control.

A prospective lock records its decision scope, source state, inputs, excluded results, exact opening event, candidates, seeds, thresholds, groups, evaluator, multiplicity family, compute plan, deterministic decision function, and claim boundary. Immutable opening-receipt successors bind the lock digest, source state, manifests, command/environment, operator, first output or protected-access time, expected runs, finalized failures, stable retry chains, and attempts. `config/phase1/opening-receipt-registry.json` is the exhaustive active-head authority; every retry advances exactly one unbranched receipt chain before execution. Both authorization and opening-receipt registries form predecessor-digest-bound generation chains, and final evidence contains every referenced generation. Phase 1 implements only the schemas, chronology/head validator, and synthetic positive/negative tests; it does not fabricate an empirical lock. A late or changed lock can support a new exploratory lineage but cannot rescue the governed confirmatory result.

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

- exact pinned B1 model and processor load from `docs/phase1/b1-pin.json`: model and processor `Qwen/Qwen2.5-VL-7B-Instruct` at repository revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`; floating revisions are forbidden; before model load, the downloaded tensor index must match its recorded size/hash, name exactly the five pinned shards and no others, and every local shard must match its recorded byte size and SHA-256; range/header parsing must reproduce the recorded tensor count, BF16 element count, and payload bytes; config, preprocessor, generation, tokenizer, and chat-template metadata must also match the recorded hashes; the runner records which template source the processor resolved and its canonical hash; `trust_remote_code` is false unless a later reviewed pin explicitly changes it;
- exact B1 runtime admission under `docs/phase1/B1_RUNTIME_GATE.md`: Transformers 5.19.0 D1 is a candidate, not proof; use the concrete multimodal class, PIL image backend, left padding, BF16 on a named compatible GPU, one GPU, SDPA, dynamic cache, and local decoded images; remote/optional kernels, the convenience vision utility, packing, static cache, chunked/continuous generation, distributed execution, compilation, gradient checkpointing, and FlashAttention 2 stay outside the reference path; bind raw-to-processed geometry and visual tokens; pass image-intervention, heterogeneous single/batch, repeated-call/order, MRoPE, cached/uncached, label/CE/accumulation, finite native forward/backward, parameter, identity-preserving save/reload, offline, and resource gates before calling B1 mechanically admitted;
- explicit engineering decoding from the pin: never inherit the repository `generation_config.json`; construct the call from the allowlisted fields, including `do_sample=false`, one beam/return sequence, neutral sampling fields, and `repetition_penalty=1.0`; bind task-specific token and stop limits in the versioned prompt contract. A missing, extra, silently ignored, or upstream-inherited generation setting rejects the run. This is the external engineering/tournament condition, not a claim about the still-unpublished official harness;
- native one-image preprocessing and stateless task/context calls;
- synthetic fixture covering classification, counting, one/many boxes, dynamic context subsets, malformed output, missing/inapplicable context, and failure states;
- exact manifest-population and output-layer set equality under `docs/phase1/EVALUATOR_MECHANICS.md`;
- one closed prospective execution-condition record, transitively bound by experiments, raw records, output manifests, runs, and reproducibility evidence, plus one paired-condition contract that permits differences only in the fixed five-field model-identity allowlist and rejects every condition-leaf mismatch;
- fractional and weighted task-change identity with frozen positive weights, exact failure/tie/missing-row rules, and no result-dependent denominator;
- primary continuous task-change states `{positive, zero, negative}` plus a separate optional binary transition table;
- acquired/retained/lost/never visual-benefit states on verified answer-changing pairs;
- canonical reduced rational objects for every division-derived aggregate, rate, pair IoU, and row IoU; no decimal approximation;
- no silent box repair, fabricated empty prediction, undefined match encoding, open-ended geometry reason, or parse/validation failure relabeling;
- real native collator, forward/backward, declared trainable-module gradients, minimal adapter save, and fresh-process reload;
- same-environment explicit-decoding token-ID and adapter/config hash replay;
- complete execution provenance and determinism classification under `docs/phase1/REPRODUCIBILITY.md`, including backend-effective kernel, precision, and distributed settings; purpose-namespaced seeds; ordered data exposure; cache/network state; exact command/log/exit-code capture; and an interrupted native-collator resume comparison that preserves optimizer, scheduler, scaler when used, RNG, sampler/cursor, accumulation, and exposure state;
- measured GPU/runtime record rather than estimates;
- local dummy release preflight only, including canonical closed-file inventory, safe-serialization allowlist, path/symlink/alias rejection, secret/private-path scan, dependency-closure checks, synthetic unresolved-blob and hidden-fetch failures, and a dummy build receipt. Phase 1 does not create or upload a Hugging Face repository.

Multi-image support is out of Phase 1 unless an official need, ordered-image schema, fixture, and acceptance test are added.

## Evidence root

Each return contains a strict `evidence-manifest.json` governed by an executable schema. It lists every other bundle member's unique normalized POSIX relative path, byte size, SHA-256, media type, and `schema_id`/`schema_version` for schema-governed records or explicit nulls for raw logs and prose. An evaluator run separately binds one closed execution-output manifest whose entry `sha256` set equals its reproducibility `output_digests` set and whose four layer populations equal the frozen example population; aggregate task-change and geometry summaries bind already-complete condition manifests without entering those manifests. Entries are regular files only: no absolute paths, empty components, `.`, `..`, backslashes, Unicode-normalization aliases, case-colliding aliases, symlinks, hard-link aliases, directories, or self-entry. Sort entries by UTF-8 bytes of the normalized path. Serialize the manifest as duplicate-key-free RFC 8785 canonical JSON encoded as UTF-8 with no BOM; the SHA-256 of those bytes is the deterministic bundle-root digest stored independently before review. Deleting, replacing, renaming, reordering, or aliasing a member must change or invalidate the root.

The bundle also contains `source-state.json`. It records the commit SHA, clean/dirty state, canonical binary patch hash when dirty, and path/size/SHA-256 inventory for every Phase 1 source, test, immutable implementation configuration, contract, and lock file. Mutable execution-state authorities—current status, source/authorization heads, and opening-receipt heads—are explicitly excluded from `source_state` to avoid provenance cycles; the evidence manifest covers their exact bytes, and status, experiment, and reproducibility records bind their appropriate digests separately. Test-command records and run manifests bind the source-state digest. Any immutable source/configuration drift after evidence generation invalidates the bundle.

Every claim is exactly `verified`, `failed`, `untested`, or `blocked_external`. The overall phase decision is:

- `accepted`: all mandatory engineering, native model, GPU backward, reload, firewall, evaluator, schema, source-state, and evidence-root rows verify; the local release-preflight subclaim verifies while only the separate external-release lifecycle subclaim and real-source purpose controls may be blocked;
- `returned_blocked`: no rejection condition occurs, but at least one mandatory row lacks evidence;
- `rejected`: a mandatory row fails, public data contaminates development, historical bytes change, task/context state leaks, raw output is repaired or missing, failed rows disappear, evidence integrity fails, or unsupported claims are made.

Only `accepted` can advance to Phase 2. A clean narrative or generic green test suite cannot substitute for row-level evidence.

## Competition release boundaries

The current sub-27B candidates require public, ungated Hugging Face access and anonymous clean download. The published sources conflict on whether an above-27B API supplements or replaces that public-release obligation, and their below/above wording leaves exactly 27B uncovered. Quarantine any exactly-27B or above-27B branch until written organizer disposition. Provisionally require an above-27B branch to satisfy both public/ungated Hugging Face closure and organizer-compatible immutable endpoint/model/base access; only a written organizer exception may narrow that requirement. Quantized-model eligibility is unresolved even though organizer inference is described as BF16/FP16, so disclose every dtype and do not invent a blanket ban.

The submitted system must be one end-to-end VLM. Ensembles, cascades, auxiliary models, external OCR, retrieval, learned preprocessing or postprocessing, and multi-model orchestration are prohibited. Multiple vision encoders are permitted only inside that one submitted VLM and every active parameter must be counted. The prohibition on external information or tool APIs during evaluation does not erase the separately published model-serving endpoint for a submitted model above 27B active parameters.

Every candidate and release record includes a component-wise active-parameter ledger for the vision encoder or encoders, language model, multimodal projector, and adapters. It declares how shared or tied parameters are counted and records the aggregation rule. Any MoE active-parameter interpretation remains unresolved until organizer-confirmed. Adapter-only repository eligibility is also unresolved; unless written organizer guidance says otherwise, release planning assumes merged or otherwise complete loadable weights rather than an adapter-only repository.

The exact Track 2 checkpoint revision cannot be entered in another track. Final records also require confidential team conflict/prize-eligibility review, anti-collusion attestation, official outputs/write-up disposition, and a submission receipt.

## Scientific boundary

Phase 1 prepares measurement only. The provisional two-budget method uses train-time compatibility surrogates, not direct control of continuous judge-score mass. Open-generation pairwise two-string margins are not binding because a third answer can win. Continuous negative mass, visual acquisition/loss, an independent secondary judge, a blinded human sample, and a repeated comparison against the strongest non-A4 baseline are later promotion gates.

Do not describe Phase 1 as scientific evidence, model readiness, official-evaluator equivalence, or competition improvement.
