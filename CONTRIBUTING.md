# Contributing

Use [Start here](docs/team/START_HERE.md) to run the package and [the repository map](docs/team/REPOSITORY_MAP.md) to locate the relevant module. Claim an issue or record the scope and owner before beginning overlapping work. No research roles have been assigned to the listed collaborators.

## Make a reviewable change

1. Create a short branch from the current default branch. State the problem, expected behavior, affected files, and evidence needed in the issue or pull request.
2. Keep one coherent change per pull request. A new research claim needs its inputs, commands, environment, raw outputs, exit codes, and limitations alongside the explanation.
3. For a behavior fix, preserve the counterexample and add a focused regression. Run the relevant tests and the root checks below; documentation-only changes need link checks, not invented unit tests.
4. Ask another contributor to review the diff and the evidence. Mark AI-generated implementation or review accurately; never describe AI review as expert or human approval.
5. Merge only when failed checks and relevant open decisions have a recorded disposition. Report failures and null results instead of replacing them with a favorable rerun.

From the repository root:

```sh
python3 tools/team.py test
python3 tools/team.py smoke
python3 tools/team.py verify-links
python3 tools/team.py verify-evidence
```

Use the Pillow environment in [Start here](docs/team/START_HERE.md) for full image coverage; `python3 tools/team.py test --images` requires the supported Pillow version to be installed and fails if it is missing. The root test helper runs the package suite plus team-tool tests; the historical 277 count refers to the package suite alone. See [Development](docs/team/DEVELOPMENT.md) for command and CI details. Native processor, source-image, and future GPU experiments need their own pinned environment and separate evidence; the fast test suite does not replay them.

## Preserve historical evidence

The initial `outputs/` tree is a versioned research handoff, including old ZIPs, manifests, logs, failed regressions, and final receipts. Publication removes captured transport session cookies from staged copies, including affected archived members; [publication-redactions.json](research/publication-redactions.json) records original and exported hashes. Original historical receipts remain as provenance, and the publication verifier accounts for the transformed copies. The original local workspace was not edited.

Do not overwrite historical receipts or edit an archive to make a check pass. Make new evidence files or a new release, recording the base commit, changed code, and superseded receipt. If changing the active package under `outputs/mmbu-precompute/`, deliberately version the change and update its current manifest/release procedure; retain the initial published ZIPs and their redaction provenance.

Some historical logs contain the original author's absolute paths. Treat them as provenance. For reruns, use repository-relative commands and write new reports. Do not rewrite a historical log merely to make its paths local to your machine. Authored `work/` drivers may contain historical local paths; inspect and adapt a copy before replaying one.

## Review authority and data handling

| Change | Evidence or review required |
| --- | --- |
| Code, parser, or numerical behavior | Counterexample, relevant tests, and another contributor's review |
| Source or record approval | Source version, intended purposes, rights basis, overlap disposition, conversion QA, and named reviewer/date; suitable biomedical review for label semantics |
| Official-contract claim | Authoritative organizer clarification and pinned harness/fixtures |
| New model or preprocessing policy | Pinned revisions, matched base/adapted settings, tested masks/presentation, and actual resource measurements |
| Confirmation analysis | Preselected candidate and seed, frozen cohort and thresholds, externally retained anchors, and every outcome preserved |
| Public release or submission | Team release decision, applicable upstream permissions, eligibility, export/reload evidence, and disclosure |

A passing validator does not grant these approvals. Keep real records pending until the relevant reviewers document a decision. Do not train on the official challenge split because it is named `train`. Keep reference answers and judge-only metadata outside inference inputs.

Do not commit credentials, access tokens, installed environments, bytecode, model weights, or raw source imagery. Keep large inputs in the controlled private release workflow, with file hashes and attribution. Access to this private repository is not a new license for third-party data. Do not upload restricted inputs to unrelated services or publish team strategy outside the registered team.

## Experiment pull requests

Use [the experiment workflow](docs/team/EXPERIMENT_WORKFLOW.md). State whether the result is an engineering diagnostic, external-development proxy, or official-protocol local result. Include the untouched baseline, population and independent groups, failure handling, seeds, paired uncertainty, source/task regressions, and actual cost. Do not call a result “official” while the [protocol register](outputs/mmbu-precompute/configs/protocol-register.json) remains unresolved.

The historical configuration templates deliberately contain unresolved values and are not executable experiment declarations. Use the documented schema and checked examples; do not make a template pass by inventing reviewer identities, permissions, model results, or revisions.
