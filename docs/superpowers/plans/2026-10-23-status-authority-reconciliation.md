# Current-status authority reconciliation plan

## Goal

Advance the sole `config/phase1/current-status.json` authority from its October 16 bootstrap state to the bounded
October 23 native evidence without changing the frozen Phase 1 contract, creating a second authority, or promoting
account, data, scientific, or competition readiness.

## Invariants

- Keep schema version 1 and `phase=design_only`.
- Keep MOCS account/allocation and GPU-allocation facts unknown: job receipts do not prove durable entitlement.
- Keep real-source admission `blocked_external`.
- Admit only four machine-readable runtime facts: B1 synthetic runtime/packaging, B2-P synthetic projector runtime,
  B2 singleton dual-objective runtime, and the negative heterogeneous-batch-equivalence result.
- Bind a transport copy containing the exact predecessor canonical bytes plus one terminal LF, and bind every exact
  repository evidence file by SHA-256.
- Preserve both failed B2 heterogeneous-batch attempts in the admitted manifest.
- Do not modify historical native receipts or any historical evidence bundle.

## TDD sequence

1. Add failing tests for the intended repository authority and for forged/missing receipt digests, missing failed B2
   predecessors, account promotion, source promotion, and predecessor mismatch.
2. Add a repository-aware status-evidence validator and invoke it from authority loading.
3. Preserve the exact predecessor bytes, generate one canonical successor, and verify its record digest.
4. Generate and validate a fresh temporary Phase 1A evidence bundle against the successor; independently validate
   the same bundle without repository coupling.
5. Run the full historical, root, and Phase 1 suites plus links, evidence, smoke, and diff checks.
6. Obtain an independent adverse review before opening a pull request.

## Adversarial hardening gate

The first adverse review found three release blockers: reconciliation could be removed by deleting its predecessor
fact, standalone bundles skipped the frozen status schema, and a resealed status could select skeletal replacement
manifests. The release gate therefore additionally requires an exact closed bootstrap-or-successor fact set, fixed
contract pins in both validation modes, immutable hashes for every retained subordinate native receipt, semantic
checks for optimizer/reload/failure evidence, and regression tests that reproduce all three attacks.

## Stop condition

Stop and redesign if the successor requires weakening canonical byte identity, accepting a second status authority,
dropping predecessor evidence, fabricating an account/source authorization, or rewriting any historical receipt.
