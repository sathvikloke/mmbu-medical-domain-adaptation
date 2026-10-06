# MMBU preparation package

Version 0.3 provides executable CPU preparation for the Medical Domain Adaptation entry: provenance and split checks, separate task/context inputs, provisional target serialization, native processor probes, assistant masks, loss arithmetic, source intake and paired score analysis. It is not an official evaluator, medical-label approval, training run or evidence of model quality.

The working model order is **Qwen2.5-VL-7B-Instruct**, then **Qwen3.5-9B**, with **Qwen3-VL-8B-Instruct** as fallback. This is a compatibility-first execution order; final selection needs matched adaptation results and measured GPU cost. Einstein access remains unreliable and no remote diagnostic has been run.

## Run locally

From this directory with Python 3.11 or newer:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m mmbu_prep status
PYTHONPATH=src python3 -m mmbu_prep demo
PYTHONPATH=src python3 -m mmbu_prep compare examples/candidate-grades-toy.json --bootstrap 1000 --seed 17
PYTHONPATH=src python3 -m mmbu_prep diagnose examples/candidate-grades-toy.json --bootstrap 1000 --seed 17
```

Core commands are offline and standard-library only. Optional image checks require Pillow 12.3 series; the native processor and synthetic loss probes use the separately pinned CPU environment described in `docs/processor-compatibility.md`. The native probes do not download model weights. Synthetic images and pregraded toy rows demonstrate software behavior, not biomedical performance.

```sh
PYTHONPATH=src python3 -m mmbu_prep inspect-images examples/engineering-manifest.jsonl --image-root examples
PYTHONPATH=src python3 -m mmbu_prep near-duplicates examples/engineering-manifest.jsonl --image-root examples
python3 tools/einstein_preflight.py --output NEW-local-report.json
```

Invalid command inputs produce a nonzero exit. Pass `--workspace /path/to/mmbu-precompute` before a subcommand when configuration/example lookup should use another directory. Source execution needs no editable installation. Python 3.12.14 and 3.14.7 were exercised; Python 3.11 syntax is checked but that interpreter is not installed here.

## What the preparation established

- All three pinned native processors encode the tested RGB inputs, with reproducible token/grid evidence. Qwen3.5's default thinking prompt does not prefix-match a plain JSON assistant answer; explicit `enable_thinking=False` resolves the tested mismatch. Native16 input silently loses or mis-scales intensity information through default processing, so explicit reviewed presentation is necessary.
- Target labels preserve native assistant boundaries and mask prompt/image/padding positions. A CPU synthetic loss probe verifies shifted token normalization across unequal microbatches; averaging microbatch means can produce a different objective. These checks do not validate an actual trainer or model gradient.
- BBBC039 quarantine contains 100 source-training fields and 198 pending count/box records. ROCO quarantine contains 24 source-training images from 24 articles across six modalities. Rights, figure lineage, decoding and source intersections have recorded evidence. No real record or source is approved for model use.
- Paired comparison preserves each candidate's own base, common examples, shared group resamples and fixed source mass. Diagnostics report task/source breakdowns, declared mixture sensitivity and rank reversals. Calibration accounting keeps random cases separate from targeted disagreements. No model predictions or human grades are invented.
- Experiment declarations bind explicit identities and artifacts. Receipt verification detects scoped additions, removals and changes. Confirmation records require retained freeze/latest anchors and preserve negative results. Local software cannot prevent independent access or enforce global immutability.

## Read next

| Need | Document |
| --- | --- |
| Actual remaining dependencies and next steps | `docs/next-actions.md` |
| IT/GPU facts without training or configuration changes | `docs/einstein-preflight.md`, `docs/einstein-handoff.md` |
| Native templates, image tokens and dtype hazards | `docs/processor-compatibility.md`, `docs/source-processor-probe.md` |
| Provisional targets, labels, image presentation and loss | `docs/target-serialization.md`, `docs/supervision-and-presentation.md`, `docs/causal-loss.md` |
| Data lineage, source review and quarantine evidence | `docs/data-contract.md`, `docs/data-review-checklist.md`, `docs/bbbc039-intake.md`, `docs/roco-sample.md` |
| Score comparisons, calibration and experiment records | `docs/candidate-comparison.md`, `docs/diagnostics.md`, `docs/experiment-records.md` |
| Unresolved organizer decisions | `configs/protocol-register.json`, `docs/organizer-questions.md` |

The organizer draft has not been sent. Gated terms were not accepted; no paid services, model inference, training or GPU jobs were run. Actual biomedical source images, raw metadata, virtual environments and tokenizer caches remain outside this portable bundle.

## Evidence and limits

`evidence/` retains source receipts, meaningful failing regressions, repaired findings and independent reviews. Historical failed development tests are not the final suite result. Version 0.3's final suite is recorded in `evidence/batch3-final-test-runs.json`; clean archive verification is in the parent `MMBU-precompute-v0.3-verification.json`. Earlier version 0.1/0.2 ZIPs and receipts remain unchanged. The current bundle manifest binds the exact packaged files.

A passing manifest validator verifies declared policy and lineage, not legal rights or medical truth. A perceptual hash proposes review candidates, not independent patients or absence of leakage. A parsed answer is not a correct answer. The score tools consume already supplied grades and reject unresolved zero-context handling. No baseline score, adaptation gain, ranking, GPU fit or BF16/FP16 export is established by this release.
