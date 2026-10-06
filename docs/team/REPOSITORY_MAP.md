# Repository map

Paths in this guide are relative to the repository root. The historical layout is preserved so prior commands and provenance remain interpretable. [Publication redactions](../../research/publication-redactions.json) bind original and exported hashes where captured transport cookies were removed from staged evidence or archived members; original historical receipts remain intact.

## Top-level navigation

| Location | Purpose |
| --- | --- |
| [README.md](../../README.md), [CONTRIBUTING.md](../../CONTRIBUTING.md) | Entry point and contribution/review expectations |
| [docs/team](.) | Team onboarding, evidence navigation, decisions, workflow, and data/model notes |
| [outputs/MMBU-domain-adaptation-plan-v2.md](../../outputs/MMBU-domain-adaptation-plan-v2.md) | Current prospective research strategy; supersedes the original plan where revised |
| [outputs/MMBU-precompute-v0.3-status.md](../../outputs/MMBU-precompute-v0.3-status.md) | Historical CPU completion status and limitations |
| [outputs/mmbu-precompute](../../outputs/mmbu-precompute) | Version 0.3 package: source, tests, examples, configs, documentation, tools, and evidence |
| [outputs](../../outputs) | All preserved plan/audit/status documents, v0.1–v0.3 portable ZIPs, and verification receipts |
| [work](../../work) | Authored acquisition/analysis/review drivers and reports; original input paths restored by `workspace-data.zip` |
| [tools/team.py](../../tools/team.py) | Root test, smoke, link, and saved-evidence checks |
| [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) | Attribution and recorded rights constraints; no blanket license grant |

## Package modules

All module links below are under `outputs/mmbu-precompute/src/mmbu_prep/`.

| Modules | Responsibility | Read alongside |
| --- | --- | --- |
| [__main__.py](../../outputs/mmbu-precompute/src/mmbu_prep/__main__.py), [_cli_experiments.py](../../outputs/mmbu-precompute/src/mmbu_prep/_cli_experiments.py) | CLI routing, explicit workspace lookup, and experiment commands | [Package README](../../outputs/mmbu-precompute/README.md) and `--help` |
| [contracts.py](../../outputs/mmbu-precompute/src/mmbu_prep/contracts.py), [serialization.py](../../outputs/mmbu-precompute/src/mmbu_prep/serialization.py) | Separate task/context/judge inputs, provisional response parsing, target serialization, pixel geometry | [Input contracts](../../outputs/mmbu-precompute/docs/input-contracts.md), [target serialization](../../outputs/mmbu-precompute/docs/target-serialization.md) |
| [data.py](../../outputs/mmbu-precompute/src/mmbu_prep/data.py) | Source/purpose validation, lineage components, hashes, and grouped split assignment | [Data contract](../../outputs/mmbu-precompute/docs/data-contract.md) |
| [images.py](../../outputs/mmbu-precompute/src/mmbu_prep/images.py), [duplicates.py](../../outputs/mmbu-precompute/src/mmbu_prep/duplicates.py) | Decode/metadata checks and perceptual duplicate-review candidates | [Image inspection](../../outputs/mmbu-precompute/docs/image-inspection.md), [duplicate triage](../../outputs/mmbu-precompute/docs/near-duplicate-triage.md) |
| [acquisition.py](../../outputs/mmbu-precompute/src/mmbu_prep/acquisition.py), [bbbc039.py](../../outputs/mmbu-precompute/src/mmbu_prep/bbbc039.py), [roco.py](../../outputs/mmbu-precompute/src/mmbu_prep/roco.py) | Bounded acquisition, source-specific quarantine conversion, and metadata inventory | [BBBC039 intake](../../outputs/mmbu-precompute/docs/bbbc039-intake.md), [ROCO intake](../../outputs/mmbu-precompute/docs/roco-intake.md) |
| [presentation.py](../../outputs/mmbu-precompute/src/mmbu_prep/presentation.py), [supervision.py](../../outputs/mmbu-precompute/src/mmbu_prep/supervision.py) | Explicit image display mapping, validated assistant boundaries, and prompt/image/padding masks | [Supervision and presentation](../../outputs/mmbu-precompute/docs/supervision-and-presentation.md) |
| [metrics.py](../../outputs/mmbu-precompute/src/mmbu_prep/metrics.py), [comparison.py](../../outputs/mmbu-precompute/src/mmbu_prep/comparison.py) | Arithmetic over supplied grades, paired group bootstrap, and candidate-specific bases | [Statistics](../../outputs/mmbu-precompute/docs/statistics.md), [candidate comparison](../../outputs/mmbu-precompute/docs/candidate-comparison.md) |
| [diagnostics.py](../../outputs/mmbu-precompute/src/mmbu_prep/diagnostics.py) | Source/task mixture sensitivity and separate random/targeted calibration summaries | [Diagnostics](../../outputs/mmbu-precompute/docs/diagnostics.md) |
| [experiments.py](../../outputs/mmbu-precompute/src/mmbu_prep/experiments.py) | Pre-run declarations, artifact receipts, and confirmation lifecycle | [Experiment records](../../outputs/mmbu-precompute/docs/experiment-records.md) |

## Configurations, tools, and evidence

The [configs directory](../../outputs/mmbu-precompute/configs) contains source/model registries, the unresolved protocol register, resource facts, and historical planning templates. Registries are declarations tied to cited evidence; they do not approve themselves. The templates intentionally contain unresolved values.

The [examples directory](../../outputs/mmbu-precompute/examples) holds synthetic inputs and toy grades for engineering checks. The [tests directory](../../outputs/mmbu-precompute/tests) tests both accepted and rejected behavior. The [evidence directory](../../outputs/mmbu-precompute/evidence) contains receipts, raw logs, counterexamples, model metadata, and AI-agent review reports. Use the [results ledger](RESULTS.md) to identify the final report for each result rather than treating any file named `green` as the latest overall status.

| Package tool | Purpose and dependencies |
| --- | --- |
| [processor_probe.py](../../outputs/mmbu-precompute/tools/processor_probe.py) | Pinned native tokenizer/template/image processing; separate CPU dependencies and cached artifacts |
| [source_processor_probe.py](../../outputs/mmbu-precompute/tools/source_processor_probe.py) | Replay real ROCO image preprocessing; restored quarantine inputs and native environment |
| [causal_loss_probe.py](../../outputs/mmbu-precompute/tools/causal_loss_probe.py) | Synthetic shifted-token loss/gradient arithmetic; PyTorch, no model |
| [prepare_roco_sample.py](../../outputs/mmbu-precompute/tools/prepare_roco_sample.py) | Convert fixed acquired source-training images to pending review records |
| [einstein_preflight.py](../../outputs/mmbu-precompute/tools/einstein_preflight.py) | Read local hardware/runtime/allocation state and write a new report; remote GPU facts require running it remotely |

## Original work areas

`work/audit-2026-10-03/` and `work/protocol-recheck-2026-10-04/` preserve source captures and protocol research. `work/source-expansion/` contains metadata analysis and protocol/supervision review drivers. `work/roco-upstream-rights/` contains publisher/figure-lineage analysis, acquisition, verification, duplicate review, and source-processor review drivers. `work/roco-quarantine/` contains acquisition and contact-sheet work; `work/bbbc039-quarantine/` retains BBBC preparation outputs. `work/processor-probe/` retains processor test/install reports and the original helper test driver.

Original raw inputs, source images, and tokenizer/config snapshots live in the private release asset. Directory contents therefore grow after restoration; empty or absent raw-input paths in a plain clone are expected. The [data guide](DATA_AND_MODELS.md) explains restoration and boundaries. Historical absolute paths identify the original run, not a required checkout location.
