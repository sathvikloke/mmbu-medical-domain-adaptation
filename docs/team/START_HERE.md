# Start here

The clone-resident [acceptance contract](../phase1/ACCEPTANCE.md) and [schema contract](../phase1/SCHEMAS.md) are the binding P1-00 through P1-21 decision authority and field-level interoperability contract. Read both with the Phase 1 contract before implementation. Candidate, experiment, hyperparameter, seed, prompt, checkpoint, promotion, and release choices are eligible only when the pre-opening decision plan and hermetic decision-execution receipt required there validate; prose decisions and manually copied rationales do not authorize execution.

This repository is ready for read-only review and contains CPU-only development contracts, tests, and registries. New
package writes require a currently approved, package-scoped launch receipt; the resealed receipt is pending. The Phase 1 package exists under the
clone-resident [Phase 1 contract](../phase1/CONTRACT.md), [official-source map](../phase1/OFFICIAL_SOURCE_MAP.md), and
[B1 pin](../phase1/b1-pin.json); extend them only under those acceptance boundaries. The historical package remains
reproducible but is not the destination for new code. There is no trained model or baseline performance result yet.

## Access and clone

Owner: `sathvikloke`. Invited collaborators (write access): `adityaraut09`, `s1g6r`, `suhritb`, `nmovva-lab`. Each account must accept its GitHub invitation before private repository and release access works. Being named in this document does not establish accepted access; inspect GitHub's current status.

After accepting access, clone with your own authenticated GitHub account:

```sh
gh repo clone sathvikloke/mmbu-medical-domain-adaptation
cd mmbu-medical-domain-adaptation
```

The historical tests and demo need only this checkout. New work uses the implemented `src/mmbu_phase1` and
`tests/phase1` paths. Real-image and cached native-processor replays also need the private release inputs described in
[Data and models](DATA_AND_MODELS.md). Credentials and installed environments are never shared through the repository.

## First local run

Use Python 3.11 or newer. From the repository root:

```sh
python3 --version
PYTHONPATH=outputs/mmbu-precompute/src python3 -m mmbu_prep --workspace outputs/mmbu-precompute demo
PYTHONPATH=outputs/mmbu-precompute/src python3 -m unittest discover -s outputs/mmbu-precompute/tests -v
```

The demo uses synthetic fixtures and pregraded toy rows. It should finish with exit code 0; any displayed score describes those fixtures, not a model. The tests intentionally exercise malformed inputs and rejected operations. Missing optional image dependencies produce explicit skips.

For image support in an isolated environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'Pillow>=12.3,<13'
PYTHONPATH=outputs/mmbu-precompute/src python -m unittest discover -s outputs/mmbu-precompute/tests -v
```

The historical full run used Python 3.12.14 and Pillow and passed 277 tests with no skips. Python 3.14.7 ran the same 277 tests with 44 optional-image skips (233 passed); Python 3.11 syntax was checked but its runtime was unavailable. A different platform or dependency set requires a fresh result, not an assumption that historical evidence transfers unchanged.

Then run:

```sh
python3 tools/team.py smoke
python3 tools/team.py verify-links
python3 tools/team.py verify-evidence
```

With supported Pillow installed, `python3 tools/team.py test --images` requires image coverage rather than silently accepting a missing dependency. This helper also runs the additional team-tool tests. See [Development](DEVELOPMENT.md) for the wrapper and CI details.

The current `python3 tools/team.py test` fails closed when the Phase 1 package, tests, current-status record, authorization
registry, or opening-receipt registry is absent; it runs a nonzero Phase 1 suite in addition to the historical suite.
That is software evidence, not an acceptance signal for data, model, GPU, or official-protocol readiness. Model and GPU
checks remain a separate explicit entry point and environment; ordinary CI must not pretend to provide that evidence.

For native processors, use the separate environment and exact pins in [processor compatibility](../../outputs/mmbu-precompute/docs/processor-compatibility.md). Do not install the entire native stack just to run the standard-library demo. Native probes use tokenizer/config/template artifacts; they do not load model weights.

## Read in this order

1. [Phase 1 contract](../phase1/CONTRACT.md): follow the new package, firewall, evidence, and acceptance boundaries.
2. [Official-source map](../phase1/OFFICIAL_SOURCE_MAP.md): see which official pages support each sanitized rule assertion and what remains unresolved.
3. [B1 pin](../phase1/b1-pin.json): use the exact model and processor identity; never float to `main`.
4. [Results and limits](RESULTS.md) plus [current clone verification](CURRENT_VERIFICATION.md): distinguish the preserved
   CPU milestone and fresh software checks from pending research.
5. [Repository map](REPOSITORY_MAP.md): locate the historical module, raw result, and script relevant to compatibility work.
6. [Organizer clarifications](ORGANIZER_CLARIFICATIONS.md) and [task-protocol snapshot](TASK_PROTOCOL_SNAPSHOT.md): use
   the dated reply register and revision-recorded visible task-card snapshot; the older question draft is historical.
7. [Package A reconciliation](PACKAGE_A_RECONCILIATION.md), dated [package status](CLAUDE_PACKAGE_STATUS.md),
   [project scorecard](PROJECT_SCORECARD.md), [independent idea arbitration](INDEPENDENT_IDEA_ARBITRATION.md),
   [research portfolio](RESEARCH_PORTFOLIO.md), binding
   [base-selection frontier](BASE_SELECTION_FRONTIER.md) and [red-team](BASE_SELECTION_REDTEAM.md),
   [competition-first recipe](COMPETITION_FIRST_RECIPE.md), conditional [system-interaction hypothesis](SYSTEM_INTERACTION_HYPOTHESIS.md), [experiment-freeze contract](EXPERIMENT_FREEZE_CONTRACT.md), [closed Claude dependency manifest](../../config/claude-handoff-dependencies.json), [context objective contract](CONTEXT_OBJECTIVE_CONTRACT.md), [unit-exposure audit](UNIT_EXPOSURE_AUDIT_SPEC.md), [weight-interpolation branch](WEIGHT_INTERPOLATION_BRANCH.md), and [immutable manifest specification](COMPETITION_MANIFEST_SPEC.md), [idea-search ledger](IDEA_SEARCH_LEDGER.md), [annotation-to-task lattice](ANNOTATION_TASK_LATTICE.md), [prospective source portfolio](DATA_SOURCE_PORTFOLIO.md), [Claude handoff](CLAUDE_HANDOFF.md), [QUILT adverse review](QUILT_ADVERSE_REVIEW.md), preserved [QUILT design](../superpowers/specs/2026-10-17-quilt-design.md), [MOSAIC research design](../superpowers/specs/2026-10-17-mosaic-design.md), [novelty audit](NOVELTY_AUDIT.md), [data-identifiability gate](MOSAIC_DATA_GATE.md), and [MedQwen reproduction-gap audit](MEDQWEN_REPRODUCTION_GAP.md): review the honest evidence ceilings, dual-objective competition decision, conditional system claim, rejected alternatives, task-view derivations, source priorities, bounded next work, current hypotheses, adverse prior-art update, source-confounding preconditions, strong-baseline gaps, controls, and stop rules. None is a model result.
8. [Audited strategy v2](../../outputs/MMBU-domain-adaptation-plan-v2.md): treat this as historical scientific context, not the current implementation contract.
9. [Decisions](DECISIONS.md) and [experiment workflow](EXPERIMENT_WORKFLOW.md): identify what evidence permits your next action.
10. [Release rehearsal](RELEASE_REHEARSAL.md): use the fail-closed runbook only after one candidate passes the frozen
    confirmation rule; it is not upload authorization.
11. [Contributing](../../CONTRIBUTING.md): open a scoped branch and request review.

## Choose a first contribution

Research ownership is currently unassigned. Agree an owner for model/evaluation, data/provenance, and review/release; one person may hold multiple roles. Record that assignment in an issue or decision record rather than inferring it from account names.

Useful work can proceed in parallel:

| Workstream | Concrete starting point | Completion evidence |
| --- | --- | --- |
| Contract | Reconcile the dated [organizer reply](ORGANIZER_CLARIFICATIONS.md) with the remaining protocol conflicts; retain the older [question draft](../../outputs/mmbu-precompute/docs/organizer-questions.md) only as historical evidence | Final context prompt, raw task-card bytes plus pinned harness/runtime, duplicate-case disposition, packaging rules, and fixtures |
| Data | Adversarially review the [prospective source portfolio](DATA_SOURCE_PORTFOLIO.md), then run only the metadata-first BUS-BRA/BUS-UCLM intake gate | Exact version/terms, grouping schema, task-atom schema, source-family decision, and stop/pass receipt; no pixels or model run before that gate |
| Compute | Use the current UTC MOCS runbook supplied with the Phase 1 work order; treat the historical [Einstein preflight](../../outputs/mmbu-precompute/docs/einstein-preflight.md) as obsolete context only | Hardware, allocation, runtime, quota, scheduler, and cost facts from the actual MOCS account |
| Software | Reproduce a focused test or investigate a recorded counterexample | New command/output receipt and a reviewed regression fix |

Do not run every historical acquisition script as an onboarding step. Some scripts access upstream networks or refer to old local paths. Start with the packaged CLI, then select a documented replay with its required inputs.
