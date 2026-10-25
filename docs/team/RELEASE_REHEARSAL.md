# Release and submission rehearsal

**Status:** planning runbook; no artifact is release-ready and no upload is authorized  
**Audience:** model operator, release reviewer, compliance reviewer, and final human submitter  
**Use:** after one candidate has passed the frozen confirmation rule; never to select a model

## Outcome

A successful rehearsal produces one immutable release-candidate directory, one evidence bundle, and one human-readable
submission worksheet. It does **not** publish a model or prove organizer acceptance. Upload remains a separate named
human decision after the official loader, form, visibility, edit policy, and exact cutoff are bound.

The current state is `blocked_before_rehearsal`: there is no selected checkpoint, native export, official loader, final
form, exact cutoff clock time, or human release authorization.

## State machine

Only the following forward transitions are valid:

```text
blocked_before_rehearsal -> frozen_candidate
frozen_candidate -> rehearsal_failed | rehearsal_passed
rehearsal_passed -> human_release_approved
human_release_approved -> upload_failed | uploaded
uploaded -> uploaded_unverified | receipt_verified
```

- Any pre-upload failure transitions that exact candidate revision to terminal `rehearsal_failed`; it never edits or
  returns the frozen revision to an earlier state. A new revision begins separately at `blocked_before_rehearsal`.
- A failed or unavailable post-upload verification transitions to terminal/escalated `uploaded_unverified`, never back
  to `human_release_approved` or forward to `receipt_verified`.
- A mechanical export/package repair creates a new candidate revision and repeats every rehearsal step.
- A weight, data, prompt, processor, generation, or inference change retires the confirmation claim and requires the
  applicable development/confirmation process again.
- `rehearsal_passed` is not permission to upload. `uploaded` is not proof that the submitted artifact is retrievable or
  loadable. Only `receipt_verified` closes the local procedure.

## Binding prerequisites

Stop before opening a release workspace unless every item has an immutable digest and reviewer:

1. one selected candidate, checkpoint, seed, base revision, method, and confirmation decision receipt;
2. exact admitted training-source and preservation-set manifests with active rights/purpose authorization;
3. frozen prompt/schema, processor, image transform, generation, evaluator, and runtime contracts;
4. exact organizer model-format, loader, dependency, hardware, precision, visibility, and form requirements;
5. exact deadline timestamp and timezone from the final submission surface or later written clarification;
6. named human owners for model release, source-rights review, medical review, team/prize eligibility, and submission;
7. a clean release environment with no ambient credentials exposed to the model process; and
8. a rollback location distinct from the candidate directory and upload destination.

The dated [organizer register](ORGANIZER_CLARIFICATIONS.md) and [task-protocol snapshot](TASK_PROTOCOL_SNAPSHOT.md) do
not currently satisfy items 3–5. Unknowns remain unknown; do not fill them with common Hugging Face defaults.

## Immutable artifact inventory

The release candidate manifest contains exact relative path, byte count, SHA-256, media/type role, producer command
digest, and required/optional status for every file. It must cover, as applicable:

This inventory is the project's conservative release standard. The organizer has not confirmed that the final form
will request these fields or this granularity.

| Class | Required contents |
|---|---|
| Identity | candidate ID/revision, base model ID and immutable revision, method/condition ID, checkpoint and seed |
| Weights | every byte needed for offline load: merged weights, or adapter plus pinned base weight blobs unless the official loader supplies a hash-bound base cache; vision tower, projector, all trainable modules, tensor dtype and shape inventory |
| Model configuration | model/config classes, architecture/config JSON, adapter configuration, generation configuration |
| Input pipeline | processor/tokenizer, chat template, image decoder/backend, resize/crop/normalization policy, coordinate transforms |
| Runtime | exact dependency lock, package artifacts/source, Python/framework/CUDA stack, launch configuration, allowed hardware |
| Evidence | confirmation receipt, fresh-load receipt, resource measurements, raw smoke outputs, logs, failure ledger |
| Disclosure | every training dataset/version/license, starting checkpoint, changed modules, external code, team members, limitations |
| Submission | frozen form worksheet, destination, visibility, upload action digest, remote revision, timestamps, receipt hashes |

Unlisted executable code, remote-code dependency, nested adapter, tokenizer/template mutation, or weight tensor is a
hard failure. QUILT should package as ordinary fixed-`A` LoRA or a merged checkpoint with no training-only projector.
MOSAIC cannot enter rehearsal until the organizer confirms that its custom router/module layout is loadable.

## Rehearsal procedure

### 1. Refresh authority without changing the candidate

- Capture current official rules/card/form/loader revisions and compare them with the bound release contract.
- Record every drift. Material drift blocks; it does not trigger an automatic configuration repair.
- Confirm the public-set firewall and source/custody registries remain unchanged since candidate selection.

### 2. Freeze and copy once

- Copy the selected candidate into a new read-only staging directory through a digest-verifying operation.
- Generate the complete inventory before execution and reject symlinks, aliases, undeclared files, mutable remote
  references, and files outside the candidate root.
- Record repository commit, dirty-state report, contract revision, and producing experiment/decision lineage.

### 3. Structural package inspection

- Recompute parameter totals, active parameters, tensor shapes, dtype, and changed-module inventory from the saved
  artifact rather than the training configuration.
- Prove exactly one final model is represented and that no optimizer state, training-only gradient basis, source data,
  secrets, caches, or development outputs are packaged.
- Reconcile base, vision, projector, language, adapter/router, processor, tokenizer, template, and generation components
  against the disclosure worksheet.

### 4. Network-denied fresh load

- Start from an empty cache and clean process/container matching the allowed runtime. A remote base reference is not a
  loadable artifact and cannot substitute for required local base bytes.
- Deny network access at the environment boundary; an offline flag alone is insufficient.
- Install only inventoried dependencies, load through the organizer-prescribed entry point, and prove zero hidden
  fetches, remote requests, undeclared imports, or writes outside the run directory.
- Record concrete classes, tensor/config hashes, device placement, effective dtype, and peak host/device memory.

### 5. Deterministic non-benchmark smoke

- Use only synthetic or separately authorized non-MMBU fixtures.
- Verify image decoding, tokenization, task routing, JSON commitment, original-pixel `xywh` round trip, one/many-box
  shapes, zero/unknown-context failure behavior, and raw-output preservation.
- Repeat from a second clean process and compare all fields covered by the reproducibility contract. Do not call this an
  official-score or biomedical-performance test.

### 6. Resource and failure envelope

- Measure cold/warm load time, first/subsequent inference latency, peak CPU/GPU memory, output-token ceiling, artifact
  bytes, and timeout/OOM behavior on the allowed hardware.
- Test interrupted load, corrupt/missing file, wrong revision, unavailable network, malformed request, and unsupported
  task routes. Every case must fail closed with a preserved log and no silent fallback.

### 7. Disclosure reconciliation

- Rebuild dataset, base-model, code, license, changed-module, and team disclosures from immutable lineage—not memory or
  a hand-edited training note.
- Diff the generated worksheet against the artifact inventory and confirmation receipt. Any unexplained item blocks.
- Obtain named human sign-off for source rights, medical/data review, model release, team/prize eligibility, and the
  accuracy of organizer-form answers.

### 8. Form and upload dry run

- Bind the exact final form schema, destination, field limits, artifact visibility, edit policy, and cutoff timestamp.
- Populate a local worksheet and validate required fields without submitting it.
- Produce the proposed upload action, expected remote repository/revision behavior, verification steps, and
  rollback/withdrawal procedure. Do not store credentials in the worksheet or evidence bundle.

### 9. Human release decision

The reviewer signs one of `approve_exact_candidate`, `reject`, or `return_for_new_revision`. Approval names the exact
manifest digest, worksheet digest, destination, visibility, and latest safe upload time. Any later byte or answer change
voids approval. AI review cannot supply this decision.

### 10. Upload and verify

Only after explicit human approval, upload the exact inventoried bytes, submit the exact worksheet, and retain local and
remote receipts. Then use the permitted verification route, pin the returned remote revision, download those exact
bytes into quarantine, verify the inventory hashes, copy them into a fresh verification cache, disable network, and
repeat structural load plus synthetic smoke. Record remote file hashes, form confirmation,
timestamp, visibility, and any organizer-generated submission ID.

If verification cannot be performed without violating rules or visibility, transition that revision to
`uploaded_unverified`, preserve all receipts, and escalate; never relabel it `receipt_verified`.

## Failure and rollback

- Never overwrite or delete the last rehearsed candidate, evidence bundle, or remote receipt.
- A failed local rehearsal produces a new failure record and leaves the candidate immutable.
- A failed upload verification uses the official edit/withdraw path only after human review; do not patch the remote
  artifact ad hoc.
- Keep the previously validated loader-compatible candidate available until the new upload is receipt-verified,
  where compatibility is established by the final official load path rather than inferred from architecture, subject to
  the one-model and edit rules in force.
- Credential exposure, rights uncertainty, unexpected remote code, hash drift, or submission-surface ambiguity stops
  the procedure and escalates immediately.

## Rehearsal evidence bundle

The final bundle contains the immutable inventory, authority snapshot, decision lineage, environment and dependency
receipts, structural inspection, two clean-load runs, resource/failure results, disclosures, human approvals, dry-run
worksheet, upload action digest, remote receipt, post-upload verification, and one limitation statement. Every claim is
tagged `planning`, `synthetic_engineering`, `native_mechanics`, `confirmation`, or `release`; evidence classes are never
silently promoted.

## Current blockers observed October 18, 2026

| Blocker | Present state | Unblocking evidence |
|---|---|---|
| Candidate | none selected | Frozen development/confirmation decision receipt |
| Artifact | none trained/exported | Immutable candidate manifest and saved bytes |
| Loader/runtime | unresolved | Organizer loader plus exact dependencies/hardware/precision contract |
| Form/destination | High-level route confirmed as Google Form plus Hugging Face model upload | Exact schema, destination, ownership/visibility, layout, edits, validation, and receipt behavior |
| Deadline | Best current written answer: December 31, 2026 at 23:30 PST | Exact final-form displayed timestamp and timezone |
| Data disclosure | policy designed, no admitted training set | Generated lineage-backed disclosure from admitted sources |
| Human authority | not recorded | Named rights, medical, release, eligibility, and submitter sign-offs |
| Upload verification | impossible before a real artifact/destination | Remote revision and clean-reload receipt under final rules |

No blocker in this table authorizes guessing. If the promotion candidate fails, no adapted runner-up is promoted from
the same confirmation opening. B0 is the only possible fallback without a new untouched confirmation population, and
only if the rules permit it and B0 independently passes the mechanical and release gates.
