# Current clone verification

## October 25 BUSI-WHU confirmation-admission addendum

The current source-admission branch adds a synthetic-tested, fail-closed BUSI-WHU review path: deterministic
927-record primary coverage, a frozen 249-record independent second-review population, strict BMP and annotation
integrity checks, exact/perceptual duplicate disposition, qualified-reviewer chronology, complete disagreement
adjudication, separate purpose decisions, task-specific eligible patient/record manifests, and a minimal bridge into
the pre-existing patient-resampled confirmation lock. The bridge accepts only a Phase 1 admission decision that
cryptographically binds the exact completed-review report plus a purpose binding for `confirmation`; it rejects
training authority, fewer than 60 independent patients,
cross-patient duplicate constraints, MMBU content use, and post-lock mutation.

Fresh verification after the independent audit repair passed **636 Phase 1 CPU tests** with two expected skips,
maintained Markdown-link verification, Python compilation of `src`, `tools`, and `tests`, working-tree
`git diff --check`. Historical branch-range whitespace findings remain outside this bounded repair. The audit-triggered
tests cover exact authority-bound review
inputs, persistent one-attempt consumption, descriptor-relative ancestor traversal, cross-source duplicate blocking,
full authentication-chain re-resolution, and reviewer-to-credential identity binding. This is engineering and governance
evidence only: the real BUSI-WHU pixels have not been opened by this workflow, reviewers have not completed the
forms, no source has been admitted, and no confirmation/model output has run.

**Observed:** October 26, 2026
**Runtime:** Python 3.14.6
**Status snapshot code revision (historical):** `b3e8fdb`
**Status authority digest:** `be1f935c954017ab28f9d8a48a5f2dba39beb1befc6057bc52e2d7b555f03730`
**Scope:** repository integrity plus the bounded synthetic native receipts listed below

## Fresh local results

| Check | Result | Interpretation limit |
|---|---|---|
| Historical preparation suite | **277 tests passed; 44 optional-Pillow image tests skipped** | Re-executes the preserved CPU package without Pillow; it does not replace the image-enabled CI lane or test a model |
| Root repository/tool suite | **75 tests passed; 13 optional-Pillow image tests skipped** | Covers repository, publication, scope, receipt, and authorization tooling; it is not scientific evidence |
| Current Phase 1 suite | **636 tests passed; two expected optional-dependency tests skipped** | Covers current fail-closed contracts, manifests, registries, evidence chains, geometry, bundles, synthetic orchestration, external-trust primitives, and evidence-documentation boundaries; native model execution is evidenced separately below |
| Offline smoke workflow | **passed** | Replays historical synthetic demonstrations and toy arithmetic only; it reports `model_executed=false` and `official_evaluation=false` |
| Maintained local Markdown links and anchors | **passed** | External URLs were not fetched by this check |
| Published v0.3 artifact verification | **passed** for 275 files, ZIP members, fixed transforms, and historical receipts | Establishes byte integrity only, not scientific validity or medical truth |
| Working-tree `git diff --check` | **passed** | Whitespace/error check only |

These test counts are distinct and must not be added or described as independent scientific evidence. The local
interpreter does not have the pinned optional Pillow dependency, so image tests were skipped locally. The latest
merged GitHub run passed the complete core workflow on Python 3.11, 3.12, and 3.14 and the image-required workflow on
Python 3.12 with Pillow 12.3.0.

## Native synthetic execution now established

The earlier statement that no model, GPU, or MOCS execution had occurred is superseded by three bounded native
receipts. All used generated synthetic inputs and one MOCS A100. None used biomedical or MMBU examples.

| Receipt | Established result | Preserved limit |
|---|---|---|
| [B1 native preflight](B1_NATIVE_PREFLIGHT_TRACE.md) | The exact pinned Qwen2.5-VL-7B runtime loaded; the language-only LoRA path completed forward, backward, one AdamW step, minimal export, and fresh socket-denied offline reload | Runtime feasibility only; no medical validity, benchmark score, or full-training evidence |
| [B2-P projector preflight](B2_PROJECTOR_PREFLIGHT_TRACE.md) | The 112 language-LoRA tensors plus five native visual-merger tensors received finite gradients, completed one synthetic step, exported, and reloaded offline with zero logit drift | Mechanism feasibility only; no answer/context benefit or competition-performance evidence |
| [B2 dual-objective preflight](B2_DUAL_OBJECTIVE_PREFLIGHT_TRACE.md) | Separate answer/context calls preserved the frozen weighted objective and completed one step under singleton microbatch accumulation | Heterogeneous concatenated-batch equivalence failed twice and remains unproven; singleton microbatches are the correctness reference, not a throughput recommendation |

The admitted B1 job was `85434`, the admitted B2-P job was `85459`, and the admitted singleton dual-objective job was
`85472`. The traces retain the exact pinned model revision, runtime, scheduler receipts, resource measurements,
artifact hashes, and adverse attempts. They do not authorize or imply a source-data decision.

## Current authority reconciliation

`config/phase1/current-status.json` remains the sole Phase 1 status authority under the frozen contract. Its October 26
successor, record digest `be1f935c954017ab28f9d8a48a5f2dba39beb1befc6057bc52e2d7b555f03730`, preserves the exact
October 24 predecessor and records the decision-integrity repair as engineering evidence only. It keeps
`phase=phase1_returned_blocked`; the later audit fixes do not themselves change that status or grant authority.

MOCS account, durable allocation, and account-wide GPU entitlement remain unknown; per-job scheduler receipts cannot
promote them. Real-source admission remains `blocked_external`. The successor and its exact status-evidence artifacts
are copied into new Phase 1A bundles, so standalone validation does not depend on an unbundled repository claim. The
predecessor bytes and every historical native receipt remain unchanged.

The [external trust-root requirement](EXTERNAL_TRUST_ROOT_REQUIREMENT.md) specifies the cryptographic evidence and
fail-closed verification order needed to replace self-authenticated names and digest-shaped claims in Stage A and
BUSI-WHU. Its pinned Ed25519 primitive is now bound to protected BUSI-WHU artifact opening: the production review CLI
requires the full external envelope and independently supplied pins, and descriptor access rejects an otherwise valid
repository capability when that binding is absent. Stage A structural opening now likewise requires distinct,
externally verified `data-owner` and `independent-reviewer` capabilities over the exact source-specific packet subject;
plain statements and hard-coded identities reject. Stage A acquisition authority, completed-review authentication,
source admission, and confirmation remain unbound. No real external key, signature, identity proof, or revocation evidence has been
supplied, so the executable gate is unsatisfied, grants no authority, and the project remains `blocked_external`.

The [machine-local evidence-root manifest](../../config/phase1/machine-local-evidence-roots-2026-10-26.json) records
the exact file count, byte count, and closed inventory digest of each of the six currently present Stage A output
directories. These directories remain machine-local and unversioned: another clone reports them as absent rather than
silently treating them as evidence. A matched local root has zero source-admission, model-selection, or promotion
authority; the manifest is an inventory and drift detector only, not a checkout-visible evidence bundle.

The active BUSI-WHU confirmation specification now carries no model or track selection: candidate identity, revision,
parameter count, runtime gate, and track are null, with `selection_authority=none`. The preserved provisional Qwen
lineage remains mechanics-only and the production lineage boundary rejects it until an independently justified
candidate-freeze authority exists. The specification also marks its source-wide body-part/domain/modality context
target `blocked_uninformative_constant`: because that target can be produced without inspecting an image, the public
confirmation decision now always blocks, while the preserved arithmetic remains available only for synthetic
mechanics tests. A future image-dependent, per-record, nonconstant endpoint needs independent review authority before
it can support promotion.

The historical offline smoke package retains its older Einstein-only status text. That output is a preserved
historical artifact, not the current project status.

## Current evidence boundary

- The source-specific semantic-breadth intake decision is merged at
  `4a9ada5a239d2e2b69bc63f1fc968895f442c598`. Its four required remote CI
  jobs passed on Python 3.11, 3.12, 3.14, and the image-enabled Python 3.12 lane.
- The repository now has strong mechanical evidence for the pinned B1 and B2-P adapter paths, including a bounded
  answer/context objective. This raises engineering readiness, not learner novelty or biomedical evidence.
- No real biomedical source is admitted. BUS-BRA remains structural engineering evidence only, and decision-bearing
  B1-L/B2-P work requires admission of BUS-BRA plus at least two additional independently admitted semantic-breadth
  source families, with prospective development and held-out-family roles. BUS-UCLM is the preferred independent
  ultrasound replication candidate. PathMNIST-224 / NCT-CRC is the first non-ultrasound breadth candidate only if
  complete parent grouping can be recovered; ChestMNIST is a noisy-label fallback and OrganAMNIST is context only.
- No MMBU public/private example, label, output, embedding, or derivative has informed model, data, curriculum,
  hyperparameter, stopping, or promotion decisions in the native runs.
- No full training, official challenge loader, official/hidden evaluation, medically reviewed result, upload, or
  submission has occurred.
- The public model repository and MMBU paper observations are quarantined as reporting-only evidence with zero
  model-selection, recipe-selection, rating, or promotion authority.

The next honest evidence gain is not another prose score increase. It is human-governed admission of BUS-BRA plus at
least two additional eligible external biomedical source families. Only then can a prospective biomedical
baseline/ablation program begin without contaminating the competition decision process.
