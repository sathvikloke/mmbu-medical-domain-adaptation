# Track decision and bounded F0 design

**Date:** 2026-10-25  
**Status:** approved by the user for bounded overnight execution

## Intent

Produce a defensible Track 2 versus Track 3 decision, replace the invalid Lane 1 context proxy with a tested official-style evaluator, freeze a fair cross-model feasibility screen, and run only one bounded engineering F0 attempt per candidate. The work must reduce uncertainty without pretending that a smoke test identifies a winning model.

## Required outcome

By the stopping point, the repository must contain:

1. an amended Track 1/2/3 decision that separates verified rules, measured evidence, assumptions, and unresolved organizer questions;
2. an official-style context evaluator using the six published field classes, dynamic applicable-field subsets, strict raw JSON, field-level credit, and explicit validity reporting;
3. one immutable F0 screen configuration fixing candidate IDs and revisions, generated-only input, prompt, LoRA profile, pass/fail rules, one-hour GPU ceiling, and the no-rescue rule;
4. one preserved receipt per attempted candidate, including terminal failure stage when a candidate fails; and
5. a plain morning report that recommends a primary and backup track from rules and incentives, not from F0 quality outputs.

## Decision stance

- Track 1 is inactive because the team does not satisfy the same-organization pretraining/mid-training/post-training rule.
- Track 3 is the provisional primary hypothesis because it rewards final task/context quality and provides a modest efficiency multiplier without requiring a fragile positive base-relative delta.
- Track 2 is the serious backup and potential second entry. It becomes primary only after a later matched multi-seed adaptation experiment demonstrates a stable positive base-relative task gain.
- A dual-track plan is conditional on written confirmation that the team's registration covers both tracks and on clarification of award stacking and checkpoint rules.

## Official-style context evaluator

The evaluator recognizes exactly these published field classes: `modality`, `submodality`, `specimen`, `body_part`, `stain`, and `medical_domain`. Each example supplies a nonempty applicable subset and source-authoritative target values for exactly that subset. The model must emit one raw JSON object with exactly the requested keys. Markdown fences, duplicate keys, unknown keys, missing keys, non-string values, non-finite constructs, and trailing material are invalid and score zero for that pass. A valid object receives the mean exact normalized field match across requested fields. Validity and correctness remain separate outputs.

This is a faithful implementation of published prose under `brief_snapshot`; it is not claimed to be the unpublished official harness. Real source labels may enter only after their authority and applicability are separately admitted. Tests use synthetic values only.

## F0 screen

The screen uses five frozen public model revisions:

- `Qwen/Qwen3.5-9B` at `c202236235762e1c871ad0ccb60c8ee5ba337b9a`
- `Qwen/Qwen3-VL-8B-Instruct` at `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`
- `Qwen/Qwen3.5-4B` at `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`
- `Qwen/Qwen3-VL-2B-Instruct` at `89644892e4d85e24eaac8bacfd4f463576704203`
- `OpenGVLab/InternVL3_5-2B-HF` at `3f301ffcf3dcbb47893afae6650ea3e78d96fb6d`

Every candidate gets one attempt, one A100 80GB, and at most one GPU-hour. It must load from a verified local snapshot with network disabled, process the same generated RGB image and frozen prompt/target, run a finite forward/backward pass and exactly one matched LoRA optimizer step, save the adapter, start a fresh offline process, reload, reproduce the deterministic prediction, and record peak memory and runtime. Candidate-specific model/processor adapters are allowed only to bridge documented public APIs; the functional LoRA scope, rank, alpha, dropout, optimizer, input, and target stay matched. No failed candidate is repaired or rerun automatically.

F0 establishes loader and training-path feasibility only. It cannot rank biomedical capability, select a winner, raise novelty/readiness, or authorize full training.

## Boundaries

- No MMBU public examples, rows, labels, outputs, statistics, or derivatives.
- No real biomedical input in F0.
- No full training, multi-seed adaptation, hyperparameter search, upload, or submission.
- No deletion or rewriting of earlier evidence.
- Every failure is retained.
- The next larger experiment requires new user approval.

