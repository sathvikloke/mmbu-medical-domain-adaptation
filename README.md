# MMBU Medical Domain Adaptation

Private team workspace for a reproducible Medical Domain Adaptation entry. It contains the research plan, CPU preparation package, source-review material, implementation history, and verification receipts produced so far.

**Current milestone: CPU preparation v0.3.** The recorded package suite passes 277 tests; the team handoff adds 36 passing tooling/restore tests. Native processors completed 144 real-image/model/policy cases, each encoded twice. **No model weights have been downloaded; no model inference, training, or GPU experiment has been run.** All real biomedical records remain pending, and no real source has an allowed model-use purpose. This is preparation evidence, not a model-performance result.

The handoff covers all 852 original research files: code and reports in Git, plus a 175 MB private release with the complete research inputs. See [publication receipts](research/README.md).

Start with [team onboarding](docs/team/START_HERE.md), then the [verified results ledger](docs/team/RESULTS.md) and [open decisions](docs/team/DECISIONS.md). The working execution order is **Qwen2.5-VL-7B-Instruct** first, **Qwen3.5-9B** as challenger, and **Qwen3-VL-8B-Instruct** as fallback. Final selection needs matched adaptation results and measured cost.

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
```

These checks validate software and saved artifacts. They cannot establish source clearance, medical correctness, model quality, or official protocol equivalence.

## Find what you need

| Need | Entry point |
| --- | --- |
| First contribution and access | [Start here](docs/team/START_HERE.md), [contributing](CONTRIBUTING.md) |
| Root commands, dependencies, and CI | [Development guide](docs/team/DEVELOPMENT.md) |
| Code, scripts, and artifact locations | [Repository map](docs/team/REPOSITORY_MAP.md) |
| Results, limitations, and evidence receipts | [Results](docs/team/RESULTS.md), [v0.3 status](outputs/MMBU-precompute-v0.3-status.md) |
| Research rationale and E00–E05 sequence | [Audited strategy v2](outputs/MMBU-domain-adaptation-plan-v2.md), [experiment workflow](docs/team/EXPERIMENT_WORKFLOW.md) |
| Organizer, source, review, and compute gates | [Decision register](docs/team/DECISIONS.md), [next actions](outputs/mmbu-precompute/docs/next-actions.md) |
| Data restoration, model revisions, and rights | [Data and models](docs/team/DATA_AND_MODELS.md), [third-party notices](THIRD_PARTY_NOTICES.md) |

`outputs/` preserves the historical portable packages and evidence, with documented transport-cookie redactions for safe private sharing. [Publication redactions](research/publication-redactions.json) record original and exported hashes; the original local workspace remains unchanged. `work/` retains authored analysis/acquisition/review scripts and results; large original inputs, source imagery, and processor snapshots are supplied separately as the private release asset `workspace-data.zip`, which restores original `work/` paths. Installed environments and bytecode are excluded. Follow the [restoration instructions](docs/team/DATA_AND_MODELS.md) when a replay needs those inputs.

## Team and research boundaries

Repository owner: **sathvikloke**. Invited collaborators (write access): **adityaraut09**, **s1g6r**, **suhritb**, and **nmovva-lab**. Access acceptance is separate from being listed here; verify the current invitation or collaborator status in GitHub. The [publication-time access receipt](research/github-access.json) records the sent invitations; GitHub shows current acceptance. Research roles are unassigned until the team records them.

Historical “independent reviews” were performed by separate AI agents. They are not human peer review, biomedical adjudication, or legal approval. No organizer message or acceptance of gated data terms is recorded in the preparation milestone.

Keep non-public challenge work within the registered team. This repository grants no blanket license over its contents: project-authored work is shared privately for internal team collaboration, and third-party material retains its original terms. See [third-party notices](THIRD_PARTY_NOTICES.md) before reuse or redistribution.
