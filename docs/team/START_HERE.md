# Start here

This handoff is ready for CPU development and review. The next scientific milestone is E00–E02 once the evaluation contract, usable data, and compute are established. There is no trained model or baseline performance result yet.

## Access and clone

Owner: `sathvikloke`. Requested collaborators: `adityaraut09`, `s1g6r`, `suhritb`, `nmovva-lab`. Each account must accept its GitHub invitation before private repository and release access works. Being named in this document does not establish accepted access; inspect GitHub's current status.

After accepting access, clone with your own authenticated GitHub account:

```sh
gh repo clone sathvikloke/mmbu-medical-domain-adaptation
cd mmbu-medical-domain-adaptation
```

The core tests and demo need only this checkout. Real-image and cached native-processor replays also need the private release inputs described in [Data and models](DATA_AND_MODELS.md). Credentials and installed environments are never shared through the repository.

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

For native processors, use the separate environment and exact pins in [processor compatibility](../../outputs/mmbu-precompute/docs/processor-compatibility.md). Do not install the entire native stack just to run the standard-library demo. Native probes use tokenizer/config/template artifacts; they do not load model weights.

## Read in this order

1. [Results and limits](RESULTS.md): distinguish verified CPU work from pending research.
2. [Repository map](REPOSITORY_MAP.md): locate the module, raw result, and historical script relevant to your task.
3. [Audited strategy v2](../../outputs/MMBU-domain-adaptation-plan-v2.md): understand the hypothesis, controlled comparisons, and promotion gates.
4. [Decisions](DECISIONS.md) and [experiment workflow](EXPERIMENT_WORKFLOW.md): identify what evidence permits your next action.
5. [Contributing](../../CONTRIBUTING.md): open a scoped branch and request review.

## Choose a first contribution

Research ownership is currently unassigned. Agree an owner for model/evaluation, data/provenance, and review/release; one person may hold multiple roles. Record that assignment in an issue or decision record rather than inferring it from account names.

Useful work can proceed in parallel:

| Workstream | Concrete starting point | Completion evidence |
| --- | --- | --- |
| Contract | Review the [organizer question draft](../../outputs/mmbu-precompute/docs/organizer-questions.md) and six protocol conflicts | Authoritative reply, pinned harness, and fixtures; the draft has not been sent |
| Data | Inspect the BBBC039 and ROCO review queues in [Results](RESULTS.md) | Recorded source decisions and suitable biomedical review; records remain pending meanwhile |
| Compute | Run the [Einstein preflight](../../outputs/mmbu-precompute/docs/einstein-preflight.md) in the allocated environment | Hardware, allocation, runtime, quota, scheduler, and cost facts |
| Software | Reproduce a focused test or investigate a recorded counterexample | New command/output receipt and a reviewed regression fix |

Do not run every historical acquisition script as an onboarding step. Some scripts access upstream networks or refer to old local paths. Start with the packaged CLI, then select a documented replay with its required inputs.
