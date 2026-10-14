# Start here

The clone-resident [acceptance contract](../phase1/ACCEPTANCE.md) and [schema contract](../phase1/SCHEMAS.md) are the binding P1-00 through P1-21 decision authority and field-level interoperability contract. Read both with the Phase 1 contract before implementation.

This handoff is ready for CPU development and review. The next step is Phase 1 engineering under the clone-resident [Phase 1 contract](../phase1/CONTRACT.md), [official-source map](../phase1/OFFICIAL_SOURCE_MAP.md), and [B1 pin](../phase1/b1-pin.json). The historical package remains reproducible but is not the destination for new code. There is no trained model or baseline performance result yet.

## Access and clone

Owner: `sathvikloke`. Invited collaborators (write access): `adityaraut09`, `s1g6r`, `suhritb`, `nmovva-lab`. Each account must accept its GitHub invitation before private repository and release access works. Being named in this document does not establish accepted access; inspect GitHub's current status.

After accepting access, clone with your own authenticated GitHub account:

```sh
gh repo clone sathvikloke/mmbu-medical-domain-adaptation
cd mmbu-medical-domain-adaptation
```

The historical tests and demo need only this checkout. New work uses `src/mmbu_phase1` and `tests/phase1` once those paths are implemented. Real-image and cached native-processor replays also need the private release inputs described in [Data and models](DATA_AND_MODELS.md). Credentials and installed environments are never shared through the repository.

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

The current `python3 tools/team.py test` is historical-only and can pass while every Phase 1 path is absent. That is expected before implementation and is not an acceptance signal. Phase 1 must change the root test command to fail closed when `src/mmbu_phase1`, `tests/phase1`, `config/phase1/current-status.json`, `config/phase1/authorization-registry.json`, or `config/phase1/opening-receipt-registry.json` is absent; include a missing-file negative test for each registry; always run `PYTHONPATH=src python3 -m unittest discover -s tests/phase1 -v`; and report a nonzero Phase 1 test count. Model and GPU checks remain a separate explicit entry point and environment; ordinary CI must not pretend to provide that evidence.

For native processors, use the separate environment and exact pins in [processor compatibility](../../outputs/mmbu-precompute/docs/processor-compatibility.md). Do not install the entire native stack just to run the standard-library demo. Native probes use tokenizer/config/template artifacts; they do not load model weights.

## Read in this order

1. [Phase 1 contract](../phase1/CONTRACT.md): follow the new package, firewall, evidence, and acceptance boundaries.
2. [Official-source map](../phase1/OFFICIAL_SOURCE_MAP.md): see which official pages support each sanitized rule assertion and what remains unresolved.
3. [B1 pin](../phase1/b1-pin.json): use the exact model and processor identity; never float to `main`.
4. [Results and limits](RESULTS.md): distinguish verified CPU work from pending research.
5. [Repository map](REPOSITORY_MAP.md): locate the historical module, raw result, and script relevant to compatibility work.
6. [Audited strategy v2](../../outputs/MMBU-domain-adaptation-plan-v2.md): treat this as historical scientific context, not the current implementation contract.
7. [Decisions](DECISIONS.md) and [experiment workflow](EXPERIMENT_WORKFLOW.md): identify what evidence permits your next action.
8. [Contributing](../../CONTRIBUTING.md): open a scoped branch and request review.

## Choose a first contribution

Research ownership is currently unassigned. Agree an owner for model/evaluation, data/provenance, and review/release; one person may hold multiple roles. Record that assignment in an issue or decision record rather than inferring it from account names.

Useful work can proceed in parallel:

| Workstream | Concrete starting point | Completion evidence |
| --- | --- | --- |
| Contract | Review the [organizer question draft](../../outputs/mmbu-precompute/docs/organizer-questions.md) and six protocol conflicts | Authoritative reply, pinned harness, and fixtures; the draft has not been sent |
| Data | Inspect the BBBC039 and ROCO review queues in [Results](RESULTS.md) | Recorded source decisions and suitable biomedical review; records remain pending meanwhile |
| Compute | Use the current UTC MOCS runbook supplied with the Phase 1 work order; treat the historical [Einstein preflight](../../outputs/mmbu-precompute/docs/einstein-preflight.md) as obsolete context only | Hardware, allocation, runtime, quota, scheduler, and cost facts from the actual MOCS account |
| Software | Reproduce a focused test or investigate a recorded counterexample | New command/output receipt and a reviewed regression fix |

Do not run every historical acquisition script as an onboarding step. Some scripts access upstream networks or refer to old local paths. Start with the packaged CLI, then select a documented replay with its required inputs.
