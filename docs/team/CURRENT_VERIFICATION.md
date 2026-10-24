# Current clone verification

**Observed:** October 23, 2026 20:16 CDT
**Runtime:** Python 3.14.6
**Verified revision:** `a187a18e1c8e56494f24b87d6f0810f47939e0ec`
**Scope:** repository integrity plus the bounded synthetic native receipts listed below

## Fresh local results

| Check | Result | Interpretation limit |
|---|---|---|
| Historical preparation suite | **277 tests passed; 44 optional-Pillow image tests skipped** | Re-executes the preserved CPU package without Pillow; it does not replace the image-enabled CI lane or test a model |
| Root repository/tool suite | **75 tests passed; 13 optional-Pillow image tests skipped** | Covers repository, publication, scope, receipt, and authorization tooling; it is not scientific evidence |
| Phase 1 suite | **389 tests passed; one optional-Pillow image test skipped** | Covers current fail-closed contracts, manifests, registries, evidence chains, geometry, bundles, and synthetic orchestration; native model execution is evidenced separately below |
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

## Current authority mismatch

`config/phase1/current-status.json` is still the sole Phase 1 status authority under the frozen contract, but its
October 16 bootstrap record still says the MOCS account, allocation, GPU, and B1 runtime are unknown and unexecuted.
That record predates the native receipts above and is stale. It was not edited here because existing evidence bundles
bind an exact byte copy and digest; changing it without a prospective migration and replacement bundle would break the
provenance contract. Until that reconciliation is designed and verified, readers must not treat the stale status file
as proof that the later receipts do not exist, or treat the later receipts as a silent rewrite of Phase 1 acceptance.

The historical offline smoke package also retains its older Einstein-only status text. That output is a preserved
historical artifact, not the current project status.

## Current evidence boundary

- `origin/main` and this verification revision are the same merged commit. The latest merged pull request passed all
  four required CI jobs.
- The repository now has strong mechanical evidence for the pinned B1 and B2-P adapter paths, including a bounded
  answer/context objective. This raises engineering readiness, not learner novelty or biomedical evidence.
- No real biomedical source is admitted. BUS-BRA remains structural engineering evidence only, and decision-bearing
  B1-L/B2-P work requires admission of BUS-BRA plus at least two additional independently admitted semantic-breadth
  source families, with prospective development and held-out-family roles.
- No MMBU public/private example, label, output, embedding, or derivative has informed model, data, curriculum,
  hyperparameter, stopping, or promotion decisions in the native runs.
- No full training, official challenge loader, official/hidden evaluation, medically reviewed result, upload, or
  submission has occurred.
- The public model repository and MMBU paper observations are quarantined as reporting-only evidence with zero
  model-selection, recipe-selection, rating, or promotion authority.

The next honest evidence gain is not another prose score increase. It is a versioned status-authority reconciliation
followed by human-governed admission of multiple eligible external biomedical source families. Only then can a
prospective biomedical baseline/ablation program begin without contaminating the competition decision process.
