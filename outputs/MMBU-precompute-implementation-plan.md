# MMBU CPU preparation implementation plan

> For agentic workers: execute the independent tasks with bounded ownership and review each result before integration. The user's request to start all work that does not need the Einstein GPU authorizes implementation of the previously audited design; no additional design approval is needed.

**Goal:** Deliver an offline, tested foundation for data validation and honest paired evaluation before GPU access is restored.

**Architecture:** A small standard-library Python package under `outputs/mmbu-precompute` separates inference inputs, dataset provenance, and arithmetic over explicitly pregraded outputs. JSON files carry unresolved protocol decisions and source eligibility. A CLI runs local checks and synthetic engineering examples without model weights or network access.

**Tech stack:** Python 3.11+, standard library, unittest, JSON/JSONL. No training framework installation, GPU use, paid APIs, or gated downloads.

## Global constraints

- Preserve the audited plan and audit artifacts unchanged; record current progress separately.
- Einstein GPU is user-reported, currently unreliable, with IT follow-up pending. Hardware, usable memory, scheduler and available hours remain unknown.
- Never label synthetic fixtures, pregraded arithmetic, or local parsing as official benchmark/model results.
- Official source conflicts remain unresolved. No claim of official-protocol equivalence and no training on challenge examples.
- Separate task, context and judge inputs. Context contains no task question, reference answer or previous-pass state.
- Do not silently repair predictions, clamp boxes, invent zero-field metadata scoring, or infer approval from public access or a split called train.
- No contacting organizers/IT, accepting terms, installing GPU stacks, or starting model training is part of this batch.
- Functional tests must exercise meaningful failures; record initial failing tests and final results. Final review must be separate from implementation.

## Task 1: Input and geometry contracts

Own `src/mmbu_prep/contracts.py`, `tests/test_contracts.py`, `docs/input-contracts.md`.

Interfaces: `build_task_input(record, system_prompt) -> dict`; `build_context_input(record, requested_fields, system_prompt) -> dict`; `build_judge_input(record, raw_prediction) -> dict`; `parse_task_output(raw, profile) -> dict`; `validate_xywh(box, width, height) -> tuple`; `box_iou(a, b) -> float`.

- [x] Write and run failing tests for leaked options/answers/history, context independence, duplicate/unknown fields, malformed JSON, duplicate JSON keys, absent answer, nonfinite numbers, unsafe boxes and IoU at a hand-derived threshold.
- [x] Implement fresh input dictionaries with explicit allowlists; parsing returns diagnostics/raw text only and never assigns semantic correctness.
- [x] Support explicitly labeled `brief_json` and `public_card` diagnostic profiles without choosing an authoritative format. Reject ambiguous multiple final objects; preserve valid values and raw text.
- [x] Document supported engineering behavior and unsupported final-harness assumptions. Run covering tests and report limits.

## Task 2: Manifest and split checks

Own `src/mmbu_prep/data.py`, `tests/test_data.py`, `docs/data-contract.md`.

Interface: `validate_manifest(records, registry, *, image_root=None, purpose="engineering") -> dict` returning `ok`, structured `errors`/`warnings`, and `counts`; `assign_splits(records, *, registry, seed, ratios) -> list[dict]` for explicitly approved external records only. The mandatory registry argument was added during implementation to enforce eligibility inside the reusable library, rather than relying on a caller's earlier check.

Registry format: `{"schema_version":1,"sources":[...]}`. Each source has `source_id`, `source_family`, `source_version`, `source_role` (`external`, `official`, or `synthetic`), `status`, `allowed_purposes`, and evidence/review fields. Candidate and quarantined sources are ineligible. Synthetic fixture source may be `engineering_only` with only engineering allowed.

Record core: `schema_version`, `record_id`, `source_id`, `source_version`, `source_family`, `split`, `image_path`, `image_sha256`, `parent_image_sha256` (nullable), `group_id`, `task`, `question`, `answer`, `context`, `annotation_origin`, `conversion_version`, `review_status`, `synthetic`. Tasks: `global_classification`, `counting`, `box_classification`, `mask_classification`, `detection`. Splits: `engineering`, `train`, `dev`, `confirmation`, `official_dev`.

- [x] Run failing tests for duplicate IDs, source quarantine, missing provenance, synthetic training misuse, split leakage through image/parent/group lineage, path traversal, hash mismatch, and invalid split ratios.
- [x] Validate source identity and version, explicit allowed purposes, file SHA-256 when image_root is supplied, and transitive leakage components. Report that perceptual duplicates and label validity are not established by byte hashes.
- [x] Implement deterministic connected-component assignment keeping lineage together, stable under input ordering; never split official or synthetic engineering data into training.
- [x] Document exact schema, approval boundaries, grouping and missing-ID behavior; run covering tests.

## Task 3: Source and protocol preparation

Own `configs/source-registry.json`, `configs/protocol-register.json`, `docs/source-screening.md`, `docs/organizer-questions.md`, `docs/data-review-checklist.md`.

- [x] Recheck primary public documentation for ROCOv2, PMC-VQA, BBBC039, BBBC041 and Chest ImaGenome; cite precise URLs and retrieval date.
- [x] Record source versions, rights evidence, annotation semantics, lineage/known overlap, proposed conversions, access requirements, and unresolved eligibility. Mark real sources candidate unless evidence actually clears intended use; no gated examples or bulk archives.
- [x] Record brief/card conflicts and what each blocks; compose a concise organizer question draft but do not send it.
- [x] Supply a source/record review checklist distinguishing mechanical validation, sampled review, biomedical judgment and official authorization.

## Task 4: Metrics, operational records and CLI

Root owns `src/mmbu_prep/metrics.py`, `src/mmbu_prep/__main__.py`, `tests/test_metrics.py`, `tests/test_cli.py`, package scaffolding, examples and remaining docs/configs.

Metrics consume explicitly pregraded rows: `record_id`, `source_id`, `group_id`, `task`, `base_correct`, `adapted_correct`, `context_correct` mapping requested field to 0/1. No semantic judge is implemented or invoked.

- [x] Test score sign/range, per-example context means, unequal fields, repeated-image rows, missing/duplicate IDs, zero-field rejection and nonfinite values.
- [x] Implement natural-mixture aggregation and explicit weights; paired cluster bootstrap within fixed sources with fixed source mass, shared draws for base/adapted, reproducible seed, and warnings for inadequate groups. Do not imply unseen-source uncertainty.
- [x] Implement CLI `status`, `validate`, `score`, `split`, and `demo` with nonzero exits for invalid input; no implicit downloads or training.
- [x] Add synthetic shape/geometry fixtures and pregraded toy scores labeled engineering-only. Real source permissions remain independent.
- [x] Supply model registry, experiment manifest, result schema, confirmation-freeze record, judge-calibration sheet and Einstein IT/handoff checklist. Unknown runtime settings remain explicit rather than fabricated.

## Task 5: Integration and independent review

- [x] Run the complete unit and CLI suite plus a clean-copy offline demonstration; preserve exact commands, outputs and exit codes.
- [x] Review score/data independence, contract ambiguities, permissions, reproducibility and failure behavior with a separate reviewer.
- [x] Fix consequential findings with regression tests; rerun affected and full integration checks.
- [x] Publish a concise status report and handoff with implemented versus blocked work, links and SHA-256 receipts. Do not call E00 complete before native model/export checks run on the restored GPU.
