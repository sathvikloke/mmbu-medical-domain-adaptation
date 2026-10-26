# Independent MMBU project audit — October 26, 2026

> **Historical snapshot, superseded for current decisions.** This report predates the later 52/100 independent audit,
> the checkout-replay boundary, and withdrawal of remote-only candidate authority. Its Qwen3.5-9B observations and
> recommended confirmation sequence have zero current model-selection or promotion authority. Use
> [current clone verification](CURRENT_VERIFICATION.md) and the active confirmation specification instead.

## Verdict

**Current evidence-backed score: 62/100.**
**Prospective ceiling after the next three real gates: approximately 82/100.**
**Decision: keep the project, but pivot the claim rather than claiming a novel learner. Do not merge the current
source-admission branch or open real BUSI-WHU pixels until the release-blocking findings below are repaired.**

This audit combined three independent read-only reviews: security/authority, correctness/testing/architecture, and
competition/scientific position. Findings were deduplicated and assigned the highest defensible severity. Passing
tests are engineering evidence, not proof that the design is complete.

## Honest ratings

| Category | Score / 10 | Current evidence ceiling |
|---|---:|---|
| Scientific / learner novelty | **2.0** | Shared LoRA plus task/context supervision is established |
| System novelty | **4.2** | The controlled interaction claim remains prospective |
| Human impact and explainability | **6.5** | Relatable clinical motivation, but no clinician-reviewed model outcome |
| Rule and track fit | **7.2** | Strong local controls; final Track 3 treatment, context evaluator, and loader remain unresolved |
| Empirical evidence strength | **6.1** | Real external-biomedical multi-seed response screen, but exploratory rather than confirmatory |
| Reproducibility / auditability | **9.3** | Strong receipts, preserved failures, deterministic tooling, and offline reload evidence |
| Implementation readiness | **8.3** | Substantial working code, but the confirmation-integrity defects below block execution |
| Present win position | **3.8** | A qualitative readiness score, not a literal probability |

The core strategy should remain: a rigorously controlled answer/context adaptation system with evidence-bound source
admission and untouched patient-level confirmation. The project should stop presenting ordinary shared PEFT as a novel
learning method.

## Release-blocking findings

### Critical: confirmation targets are mutable after the population lock

The validated review report and confirmation source manifest bind record IDs and patient ownership but not the source
benign/malignant target for each record. Result rows supply their own target and only need to agree across conditions.
A consistently flipped target map can therefore change the locked analysis. Freeze and digest the exact target map in
the task manifest, confirmation source manifest, population binding, and confirmation lock; every result row must
match it.

### Critical: real-payload decoding has no enforced protected-opening chain

The BUSI-WHU packet builder accepts paths and directly decodes the archive without requiring the active protected
opening, source manifest, acquisition receipt, artifact hashes, authority registry, tested revision, or opening scope.
The builder must reject before reading payload bytes unless the complete exact opening chain validates.

### Critical: the declared duplicate boundary is not implemented

The frozen Stage A contract requires a versioned 64-bit dHash comparison at Hamming distance at most four with an
aspect-ratio constraint and cross-source comparison. The current BUSI-WHU builder uses a different average-threshold
hash and groups only identical hashes within BUSI-WHU. The shared frozen algorithm and cross-source inventories must
replace it before confirmation opening.

### High: reviewer identities and qualifications are self-declared

The completed-review report explicitly says `reviewer_identity_authenticated=false`, yet an admission decision that
binds the report can currently feed confirmation. Every primary, secondary, adjudicator, and rights reviewer must have
a separately validated Phase 1 attestation or detached verification artifact, and the confirmation bridge must require
authenticated identity.

### High: the confirmation bridge is optional

The lower-level randomization constructor accepts an opaque digest and arbitrary patient map. Execution-facing code
can bypass the authenticated BUSI-WHU manifest. Real confirmation construction must accept and validate the actual
source manifest, report, store, source admission, and purpose authorization internally; synthetic fixtures must use an
explicitly separate interface.

### High: file identity has path-substitution windows

Several protected readers hash a pathname and later reopen the same pathname. A concurrent replacement can make the
bytes used differ from the bytes authorized or reported. Real protected access needs a single descriptor-relative,
no-follow open, regular-file/link checks, stable pre/post `fstat`, and parsing/hashing from the retained descriptor.

## Important completeness findings

- The worksheet collapses grounded-completeness, localization-completeness, and additional/incomplete-lesion risk
  into one annotation field, preventing required task-specific narrowing.
- Systematic label inversion, label leakage, and patient-identity defects cannot be recorded as source-level kill
  conditions.
- The workbook is hashed but its stored geometry is not compared with decoded dimensions and annotation geometry.
- Duplicate adjudication rows are not required to be unique; contradictory duplicates can become last-entry-wins.
- The older Stage A builder can synthesize named identity attestations from arbitrary prose and only partially
  validates historical multi-source acquisition packets.
- Branch-range whitespace checks were not part of the earlier clean-tree verification claim.

## What is genuinely strong

- The Qwen3.5-9B response screen showed positive base-relative response across the frozen adapted conditions, and all
  fourteen GPU conditions exported and reloaded deterministically.
- The repository preserves failed attempts instead of hiding them.
- The BUSI-WHU population selection, packet publication, exact coverage, reviewer-role separation, task narrowing,
  purpose separation, and patient-level locking are strong foundations.
- The post-audit branch passed 582 Phase 1 tests with two expected skips before these newly identified requirements
  were added.

## Highest-value sequence

1. Repair every decision-integrity blocker above before any real BUSI-WHU opening.
2. Complete real training-source admission and authenticated BUSI-WHU human review.
3. Freeze and run one no-rescue Qwen3.5-9B confirmation on untouched BUSI-WHU patients.
4. Resolve Track 3 parameter treatment, multi-track eligibility, context evaluator/schema, and packaging with the
   organizers, then rehearse the exact offline submission load.

If the untouched confirmation passes, the project becomes a serious competition entry despite low learner novelty.
If it fails, pivot the model/recipe from the preserved evidence; do not rescue the result by changing the confirmation
protocol.
