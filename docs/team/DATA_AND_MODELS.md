# Data, models, and restoration

The Git checkout holds authored code/results and historical portable outputs, with captured transport cookies removed from staged publication copies. [Publication redactions](../../research/publication-redactions.json) retain original/exported hashes; original historical receipts and the original local workspace remain intact. Large original inputs, source imagery, and pinned tokenizer/config snapshots are delivered through the private `workspace-data.zip` release asset. It restores the original `work/` paths into the repository root. Installed environments and bytecode are excluded; **model weights are absent** because none were downloaded.

## Restore only when your replay needs it

Use the [team-handoff-v0.3 release](https://github.com/sathvikloke/mmbu-medical-domain-adaptation/releases/tag/team-handoff-v0.3) with your own authenticated account after accepting repository access. The [workspace inventory](../../research/workspace-inventory.json) records which original files are in Git, in the private asset, or excluded. The [asset manifest](../../research/workspace-data-manifest.json) records the release inputs and hashes.

The [restoration helper](../../tools/restore_workspace.py) handles authenticated download, verification, and extraction into original `work/` paths. Download mode requires the GitHub CLI and your own authenticated account (`gh auth status`; use `gh auth login` if needed). From the repository root, after the release is available:

```sh
python3 tools/restore_workspace.py --download
```

The helper verifies the ZIP and every member against the repository manifest before restoring files. It accepts existing identical files and rejects changed destination files without overwriting them. `--download --dry-run` verifies the downloaded bytes and destination conflicts without restoring inputs. If you downloaded `workspace-data.zip` yourself, use `python3 tools/restore_workspace.py --archive workspace-data.zip` instead; append `--dry-run` for verification only. `--target` selects another existing destination directory, and `--help` lists the options. The standard-library tests, demo, and historical ZIP verification do not require these private source inputs.

Keep the target directory unchanged while restoration runs. Files are published individually after all content checks; this is not a transaction over the whole directory. A later disk or filesystem failure can leave some verified files restored. Resolve the cause and rerun: identical files are accepted. Dry runs still need writable temporary space for a full expanded copy; download mode also needs space for the ZIP. Use an ordinary local filesystem that supports hard links.

Restoration makes prior CPU inspection reproducible. It does not change `pending` records to approved records, grant training rights, or authorize public redistribution. Keep outputs derived from pending material under the same review boundaries.

## What data exists

This table summarizes the saved registry, not a newly issued license opinion or source approval. Every real source has `allowed_purposes: []` at handoff.

| Source | Material inspected/acquired | Recorded rights and unresolved use |
| --- | --- | --- |
| BBBC039 v1 | Official archive inputs; 100 source-training fields decoded; 198 pending count/box candidates | Source page declares CC0; challenge overlap, display/annotation review, and intended model-use approval remain unresolved |
| ROCOv2 2.0.1 | Four metadata files and 24 selected source-training JPEGs across six modalities, with receipts | Aggregate CC BY-NC 4.0; sampled articles have CC BY version evidence, but article scope, figure exceptions, aggregate terms, challenge eligibility, and public-weight release compatibility are separate unresolved matters |
| PMC-VQA pinned metadata | Training CSV, license/documentation metadata; no images acquired | Paper reports upstream CC0/CC BY and aggregate CC BY-SA; exact obligations, usable labels, and intended use require review |
| BBBC041 v1 | Public documentation only; archive not fetched | Recorded CC BY-NC-SA 3.0; noncommercial/share-alike and release compatibility unresolved |
| Chest ImaGenome 1.0.0 | Public documentation only; no credentialed data | Credentialed license/DUA requirements not completed; no access or release approval inferred |
| MMBU public set | Visible public card/API/source snapshots only; no gated examples | Access terms not accepted, files not downloaded, protocol/public-dev permissions unresolved; a technical `train` split is not training permission |
| Synthetic fixtures | Locally authored geometry and hand-derived toy answers in the package | Engineering-only fixtures; no biomedical efficacy claim |

See the [source registry](../../outputs/mmbu-precompute/configs/source-registry.json), [BBBC039 intake](../../outputs/mmbu-precompute/docs/bbbc039-intake.md), [ROCO rights review](../../outputs/mmbu-precompute/docs/roco-upstream-rights.md), and [source screening](../../outputs/mmbu-precompute/docs/source-screening.md) for exact evidence and upstream locators.

Preserve patient/study/field/article/figure/panel lineage and source splits. ROCO and PMC-VQA share 12,078 training PMCIDs in the inspected metadata; they are not independent source families. Article overlap does not establish identical images, and exact/perceptual image checks do not prove independent subjects. Pending review must address shortcuts, text overlays, correct coordinate frames, and visible support for each target.

## Model candidates and pinned snapshots

| Role | Model | Recorded processor snapshot |
| --- | --- | --- |
| Working baseline | Qwen/Qwen2.5-VL-7B-Instruct | `cc594898137f460bfe9f0759e9844b3ce807cfb5` |
| First challenger | Qwen/Qwen3.5-9B | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Fallback | Qwen/Qwen3-VL-8B-Instruct | `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` |

The [model registry](../../outputs/mmbu-precompute/configs/model-registry.json) records public, ungated repositories and Apache-2.0 card metadata as retrieved; these are historical metadata observations. The [preflight](../../outputs/mmbu-precompute/docs/model-preflight.md) distinguishes checkpoint metadata from independently measured runtime facts. These snapshots pin tokenizer, template, and configuration artifacts; no tensor checkpoint, model loading, active-parameter verification, GPU fit, or export has been established.

The private asset's processor cache contains only the probe's allowlisted files. Use the [native reproduction instructions](../../outputs/mmbu-precompute/docs/processor-compatibility.md), [dependency pins](../../outputs/mmbu-precompute/evidence/processor-requirements.txt), and [installation receipt](../../outputs/mmbu-precompute/evidence/processor-install-report.json). The tested stack was a separate Python 3.12 macOS arm64 CPU environment; exact package pins may not install unchanged on every platform. Rebuild the environment locally; do not share a virtual environment directory.

The native loader uses local files and `trust_remote_code=False`; offline replay checks identities, required files, and hashes. A new revision or environment requires fresh probe evidence. Model training additionally requires the actual trainer, model module/mask/loss integration, resource facts, and export checks described in [Experiment workflow](EXPERIMENT_WORKFLOW.md).

## Attribution and reuse

See [Third-party notices](../../THIRD_PARTY_NOTICES.md). The private repository and release give teammates access to the handoff; neither grants new rights over third-party datasets, figures, model artifacts, or dependencies. Carry source receipts and figure/article attribution into reviewed derivatives. Resolve intended-use and release conditions before promoting a source or publishing derived material.
