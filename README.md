# MMBU Medical Domain Adaptation

Private team workspace for a reproducible Medical Domain Adaptation entry. It contains the research plan, CPU preparation package, source-review material, implementation history, and verification receipts produced so far.

**Current milestone: Phase 1 contract engineering plus prospective competition design.** The preserved CPU-preparation
v0.3 package passed its historical 277-test suite, and the clone now also contains the fail-closed Phase 1 package,
registries, tests, organizer-reply register, competition manifest specification, and MOCS access audit. Native
processors previously completed 144 real-image/model/policy compatibility cases, each encoded twice. The pinned B1
model/runtime has now been acquired on MOCS and bounded synthetic single-GPU preflights have exercised native image
processing, B1 and B2-P updates, export, offline reload, and the answer/context objective. **No biomedical training or
MMBU public-set model evaluation has run.** All real biomedical records remain pending, and no real source has an
allowed model-use purpose. This is preparation evidence, not a model-performance result.

The handoff covers all 852 original research files: code and reports in Git, plus a 175 MB private release with the complete research inputs. See [publication receipts](research/README.md).

Start with [team onboarding](docs/team/START_HERE.md), then the [verified results ledger](docs/team/RESULTS.md) and [open decisions](docs/team/DECISIONS.md). The competition shortlist is intentionally empty until a prospectively frozen model-selection decision and its receipt exist. The three pinned Qwen snapshots are processor/runtime engineering subjects, not a performance ranking; B1 is the exact Phase 1 native-runtime fixture, not a selected competition base.

## Run the preparation package

Use Python 3.11+ and run these commands from the repository root. The core package is offline and uses only the standard library; no GPU or model download is needed.

```sh
PYTHONPATH=outputs/mmbu-precompute/src python3 -m mmbu_prep --workspace outputs/mmbu-precompute demo
PYTHONPATH=outputs/mmbu-precompute/src python3 -m unittest discover -s outputs/mmbu-precompute/tests -v
```

Image tests additionally require `Pillow>=12.3,<13`. Without Pillow, optional image tests are skipped; read the skip count before comparing your run with the historical 277-test result. See [environment setup](docs/team/START_HERE.md) for an isolated environment and [native processor reproduction](outputs/mmbu-precompute/docs/processor-compatibility.md) for the separately pinned CPU stack.

The root helper provides team checks:

```sh
python3 tools/team.py test
python3 tools/team.py smoke
python3 tools/team.py verify-links
python3 tools/team.py verify-evidence
python3 tools/protocol_drift.py
```

The protocol-drift check reads only the public Hugging Face repository metadata endpoint. It does not open dataset
files or rows, and it exits nonzero if the pinned revision, dataset identity, or gated/public state changes.

These checks validate software and saved artifacts. They cannot establish source clearance, medical correctness, model quality, or official protocol equivalence.

## Find what you need

| Need | Entry point |
| --- | --- |
| Five-minute project idea, impact, novelty, and next gates | [Executive project dossier](docs/team/EXECUTIVE_PROJECT_DOSSIER.md) |
| Descriptive public model-repository observation and firewall disposition | [Public model repository audit](docs/team/PUBLIC_MODEL_REPOSITORY_AUDIT.md) |
| First contribution and access | [Start here](docs/team/START_HERE.md), [contributing](CONTRIBUTING.md) |
| Root commands, dependencies, and CI | [Development guide](docs/team/DEVELOPMENT.md) |
| Code, scripts, and artifact locations | [Repository map](docs/team/REPOSITORY_MAP.md) |
| Results, limitations, and evidence receipts | [Results](docs/team/RESULTS.md), [v0.3 status](outputs/MMBU-precompute-v0.3-status.md) |
| Historical research rationale and current E00–E05 sequence | [Audited strategy v2](outputs/MMBU-domain-adaptation-plan-v2.md), [experiment workflow](docs/team/EXPERIMENT_WORKFLOW.md) |
| Organizer, source, review, and compute gates | [Decision register](docs/team/DECISIONS.md), [competition manifest](docs/team/COMPETITION_MANIFEST_SPEC.md), [MOCS access audit](docs/team/MOCS_ACCESS_AUDIT.md) |
| Data restoration, model revisions, and rights | [Data and models](docs/team/DATA_AND_MODELS.md), [third-party notices](THIRD_PARTY_NOTICES.md) |

`outputs/` preserves the historical portable packages and evidence, with documented transport-cookie redactions for safe private sharing. [Publication redactions](research/publication-redactions.json) record original and exported hashes; the original local workspace remains unchanged. `work/` retains authored analysis/acquisition/review scripts and results; large original inputs, source imagery, and processor snapshots are supplied separately as the private release asset `workspace-data.zip`, which restores original `work/` paths. Installed environments and bytecode are excluded. Follow the [restoration instructions](docs/team/DATA_AND_MODELS.md) when a replay needs those inputs.

## Team and research boundaries

Repository owner: **sathvikloke**. Invited collaborators (write access): **adityaraut09**, **s1g6r**, **suhritb**, and **nmovva-lab**. Access acceptance is separate from being listed here; verify the current invitation or collaborator status in GitHub. The [publication-time access receipt](research/github-access.json) records the sent invitations; GitHub shows current acceptance. Research roles are unassigned until the team records them.

Historical “independent reviews” were performed by separate AI agents. They are not human peer review, biomedical
adjudication, or legal approval. The October 14 organizer reply is transcribed in the current team register, and the
authenticated Hugging Face page reports that this account has dataset access. Neither fact admits the public set for
training or model selection under the project's stricter firewall, supplies a raw terms-acceptance receipt, or resolves
the remaining protocol and packaging contradictions.

Keep non-public challenge work within the registered team. This repository grants no blanket license over its contents: project-authored work is shared privately for internal team collaboration, and third-party material retains its original terms. See [third-party notices](THIRD_PARTY_NOTICES.md) before reuse or redistribution.
