# Replicated external-biomedical response screen

**Date:** October 25, 2026

**Status:** terminal; all 14 replacement conditions passed every execution and receipt gate

**Scientific use:** exploratory response evidence only; this screen does not select or promote a model

**Checkout replay status:** available from a sealed, payload-minimized portable bundle

**Promotion authority:** none

The exact execution manifest, all 14 primary result receipts and raw development predictions, all 14 fresh-process
reload receipts and predictions, the post-output analysis, and the relevant logs are now present in a sealed portable
bundle. The bundle also contains a narrow 256-row development projection sufficient to replay task and context scoring;
it excludes source images and archives, the compiled portfolio, model weights, adapter payloads, and caches. The local
verifier authenticates every member, rejects additions and heavy artifacts, checks every frozen condition and receipt
claim, matches primary and reload predictions, recomputes all 14 metrics, and recomputes both candidates' paired
bootstrap analyses.

This makes the historical experiment independently auditable from the checkout. It does not change its scientific
status: the screen used a fixed development population, its bootstrap literals were selected after outputs existed,
source admission remained incomplete, and model promotion was prohibited before launch.

## Portable cold-review bundle

- Bundle: `outputs/replicated-response-screen-2026-10-25-portable/bundle`
- External retention receipt: `outputs/replicated-response-screen-2026-10-25-portable/retention-receipt.json`
- Evidence-root SHA-256: `cd62e3a67169434f29a3d710603d11ccaf851e1dcc529b54326b5dd2c8bd0e56`
- Bundle members including the manifest: 62
- Total bundle size: 4,116,144 bytes
- Remote export root: `/storage/scr/npl015/mmbu-response-export/2026-10-26-portable-7756918`

Cold replay command:

```bash
python3 tools/verify_replicated_response_evidence.py \
  --bundle outputs/replicated-response-screen-2026-10-25-portable/bundle \
  --receipt outputs/replicated-response-screen-2026-10-25-portable/retention-receipt.json
```

The expected verified summary is 14 conditions, 256 development rows, all metrics replayed, analysis replayed, and
`promotion_eligible=false`. The portable export was derived into a new MOCS root; neither the preserved replacement
run nor its predecessor was modified.

## Bottom line

Matched dual-endpoint LoRA training produced near-perfect or perfect context scores in every adapted seed for both frozen Qwen3.5 candidates. Against the matched task-only condition, all three 9B seeds and two of three 4B seeds met the predeclared rule of at least a one-point context gain with no more than a one-point task drop. The remaining 4B seed gained 100 context points but lost 2.734 task points, so the effect isn't uniformly free of a task tradeoff.

This is useful evidence that the dual objective can teach the requested structured context behavior on the frozen development population. It does not establish generalization, clinical validity, source admission, official MMBU performance, or a winning checkpoint. Confirmation partitions remained unopened, `source_admission_complete` is false in every receipt, and model promotion was prohibited before launch.

## Frozen run identity

- Replacement Slurm array: `85889`
- Replacement run root: `/storage/scr/npl015/mmbu-response/2026-10-25-8cba5ab`
- Repository snapshot: local commit `8cba5ab6ee22465c0b9117b8f4110763ba67759d`
- Manifest SHA-256: `9bd53c828cc24d5a8a52c77f52afffad64dbde26b2508a31f165ae0304e8aed5`
- Compiled portfolio SHA-256: `1a68cdc9b3e4ea3a8d75c75d46d6fc583ee261b5ce82bffb258f20f130a3c092`
- Training-ID digest: `4d4892e5700484f878d261d17ad2bf79a1add63be57f16be6cfe8e8be54b3e6b`
- Development-ID digest: `43faf1efd475079b0bc1567e528f6d658642144c78285e7c96833dc41c2179fc`
- Data used: pinned external-biomedical working copies of BUS-BRA and PathMNIST only
- Public-set flag: `mmbu_public_content_used=false` in all 14 receipts
- Confirmation use: prohibited and not performed

The closed manifest fixed two exact model revisions, one unchanged-base condition per model, task-only and dual profiles, three seeds, 1,024 optimizer updates per adapted condition, LoRA rank 8 on `q_proj` and `v_proj`, and one attempt per condition.

## Exact condition outcomes

Task and context values are the exact receipt rationals rendered as percentages. Peak memory is allocated CUDA memory, converted to GiB for readability.

| Index | Frozen condition | Slurm job | Status | Updates | Adapter files | Reload match | Task | Context | Peak GiB | Elapsed min |
|---:|---|---:|---|---:|---:|---|---:|---:|---:|---:|
| 0 | `rr-qwen35-9b::base` | `85890` | Passed | 0 | 0 | Yes | 62.891% | 8.691% | 17.71 | 26.26 |
| 1 | `rr-qwen35-9b::task_only::20261025` | `85891` | Passed | 1,024 | 3 | Yes | 85.547% | 3.125% | 21.84 | 32.90 |
| 2 | `rr-qwen35-9b::task_only::20261026` | `85892` | Passed | 1,024 | 3 | Yes | 84.766% | 6.445% | 21.84 | 44.29 |
| 3 | `rr-qwen35-9b::task_only::20261027` | `85893` | Passed | 1,024 | 3 | Yes | 86.719% | 0.488% | 21.84 | 40.90 |
| 4 | `rr-qwen35-9b::dual::20261025` | `85894` | Passed | 1,024 | 3 | Yes | 85.156% | 100.000% | 22.51 | 37.45 |
| 5 | `rr-qwen35-9b::dual::20261026` | `85984` | Passed | 1,024 | 3 | Yes | 87.109% | 99.902% | 22.51 | 29.96 |
| 6 | `rr-qwen35-9b::dual::20261027` | `85986` | Passed | 1,024 | 3 | Yes | 86.719% | 99.902% | 22.51 | 29.41 |
| 7 | `rr-qwen35-4b::base` | `85988` | Passed | 0 | 0 | Yes | 81.250% | 0.000% | 8.72 | 32.09 |
| 8 | `rr-qwen35-4b::task_only::20261025` | `85991` | Passed | 1,024 | 3 | Yes | 82.031% | 0.000% | 12.55 | 40.33 |
| 9 | `rr-qwen35-4b::task_only::20261026` | `85993` | Passed | 1,024 | 3 | Yes | 82.422% | 0.391% | 12.55 | 44.98 |
| 10 | `rr-qwen35-4b::task_only::20261027` | `86016` | Passed | 1,024 | 3 | Yes | 82.422% | 4.264% | 12.55 | 32.76 |
| 11 | `rr-qwen35-4b::dual::20261025` | `86017` | Passed | 1,024 | 3 | Yes | 79.297% | 100.000% | 13.20 | 29.11 |
| 12 | `rr-qwen35-4b::dual::20261026` | `86019` | Passed | 1,024 | 3 | Yes | 82.031% | 100.000% | 13.20 | 32.40 |
| 13 | `rr-qwen35-4b::dual::20261027` | `85889` | Passed | 1,024 | 3 | Yes | 82.422% | 100.000% | 13.20 | 29.94 |

Every adapted receipt contains `README.md`, `adapter_config.json`, and `adapter_model.safetensors`. Every fresh-process offline reload reproduced the saved development predictions exactly. Every run used an NVIDIA A100 80GB PCIe GPU and recorded nonzero allocated and reserved CUDA memory.

## Matched response analysis

### Qwen3.5-9B

| Seed | Task-only task | Dual task | Task change | Task-only context | Dual context | Context change | Frozen seed rule |
|---:|---:|---:|---:|---:|---:|---:|---|
| `20261025` | 85.547% | 85.156% | -0.391 pp | 3.125% | 100.000% | +96.875 pp | Pass |
| `20261026` | 84.766% | 87.109% | +2.344 pp | 6.445% | 99.902% | +93.457 pp | Pass |
| `20261027` | 86.719% | 86.719% | 0.000 pp | 0.488% | 99.902% | +99.414 pp | Pass |

The three-seed task-only mean was 85.677%, and the dual mean was 86.328%. The context means were 3.353% and 99.935%, respectively. All three seeds satisfy the frozen response rule.

### Qwen3.5-4B

| Seed | Task-only task | Dual task | Task change | Task-only context | Dual context | Context change | Frozen seed rule |
|---:|---:|---:|---:|---:|---:|---:|---|
| `20261025` | 82.031% | 79.297% | -2.734 pp | 0.000% | 100.000% | +100.000 pp | Fail: task drop exceeds 1 pp |
| `20261026` | 82.422% | 82.031% | -0.391 pp | 0.391% | 100.000% | +99.609 pp | Pass |
| `20261027` | 82.422% | 82.422% | 0.000 pp | 4.264% | 100.000% | +95.736 pp | Pass |

The three-seed task-only mean was 82.292%, and the dual mean was 81.250%. The context means were 1.552% and 100.000%, respectively. Two seeds satisfy the frozen response rule, exactly meeting the predeclared minimum of two supporting seeds. The failed seed stays part of the evidence.

## Post-output paired uncertainty analysis

Commit `6ef06ab` repaired an implementation gap in the frozen analysis plan: the plan required a group-aware paired uncertainty calculation, but the launch snapshot contained no aggregate implementation. The repair grades the saved raw predictions against the same 256-row development population, pairs every adapted prediction with its unchanged-base prediction, resamples the 128 independent units within each source, balances the two sources equally, and averages the paired delta across the three fixed seeds.

The calculation used 10,000 shared group-resampling draws, bootstrap seed `20261025`, and a two-sided 90% percentile interval. Those literals were selected after model outputs existed because the original design did not freeze them. The intervals are therefore **post-output exploratory evidence**, not a preregistered promotion test.

| Candidate | Profile | Base-relative task delta | Exploratory 90% interval | Interpretation |
|---|---|---:|---:|---|
| Qwen3.5-9B | Task-only | +22.786 pp | [+18.099, +27.344] pp | Positive throughout |
| Qwen3.5-9B | Dual | +23.438 pp | [+18.750, +27.995] pp | Positive throughout |
| Qwen3.5-4B | Task-only | +1.042 pp | [-3.906, +5.990] pp | Includes zero |
| Qwen3.5-4B | Dual | 0.000 pp | [-5.078, +4.948] pp | Includes zero |

The canonical analysis artifact is `/storage/scr/npl015/mmbu-response-analysis/2026-10-25-6ef06ab/post-output-bootstrap.json`, SHA-256 `2aeeb194baa2a95af09e14e5b0a96788bf55af7af2f853638f63362cc51a12ef`. It reads the preserved run without changing any receipt, prediction, log, or model artifact.

The reported 9B result is a large and replicated response on this fixed development population. Its primary prediction
and receipt evidence is now locally replayable, but it still cannot establish candidate priority or authorize a
confirmation candidate. It does not retroactively satisfy a binding confidence-bound gate, prove transfer to another
source or partition, or authorize checkpoint promotion.

## Predeclared descriptive checks

| Check | Result | Evidence |
|---|---|---|
| Track 2 response signal | Direction passes; confidence component remains exploratory | All six adapted 9B task scores exceed the unchanged base. Both post-output 90% lower bounds are above zero. |
| Dual-objective value | Pass for both candidates | Dual `Q` exceeds matched task-only `Q` by more than 0.01 with at most a 0.01 task loss in three of three 9B seeds and two of three 4B seeds. |
| Small-route competitiveness | Fail on raw `Q` | The 4B task-only route is within 0.03 of the 9B route in only one seed; the 4B dual route is more than 0.03 lower in all three seeds. No unresolved Track 3 size multiplier was applied. |
| Instability flag | No 9B direction reversal observed | Every adapted 9B seed has a positive base-relative task delta, and fresh reload matched exactly. |

These checks describe the historical screen only. They cannot prioritize a candidate, compare separate official
leaderboards, or choose the final competition track.

## Preserved predecessor failure

The first array, job `85873` at `/storage/scr/npl015/mmbu-response/2026-10-25-6eca07f`, is preserved unchanged. Conditions 0 through 4 completed their main evaluation but failed at the fresh-process reload stage with exit code 2 because the reload entry point did not add the repository `src` directory before importing `mmbu_phase1`. Once the shared launcher defect was isolated, the remaining work was cancelled rather than consuming more GPUs on the same known failure.

A regression test reproduced the missing-path failure with `PYTHONPATH` removed. Commit `8cba5ab6ee22465c0b9117b8f4110763ba67759d` added the entry-point bootstrap, the regression test passed, and the exact staged command passed before replacement launch. The replacement array then passed the reload gate in all 14 conditions. No failed predecessor receipt or log was overwritten or deleted.

## What this establishes

- Both exact model revisions can complete the frozen external-biomedical screen within the declared A100 envelope.
- The adapted conditions performed exactly 1,024 optimizer updates, exported nonempty adapters, and reloaded deterministically in a fresh offline process.
- Dual training caused a large, replicated increase in the frozen context score for both models.
- The 9B dual conditions preserved matched task performance within the frozen tolerance in all three seeds.
- The 4B dual conditions preserved matched task performance within the frozen tolerance in two of three seeds.
- On the fixed development population, the exploratory group-aware interval for the 9B base-relative task gain stayed above zero for both adapted profiles, while both 4B intervals included zero.

## What this does not establish

- It doesn't establish performance on MMBU, because no MMBU public example, label, derivative, or result was used.
- It doesn't establish hidden-set or confirmation-set generalization.
- It doesn't complete source admission or prove that either source may be used in a final training release.
- It doesn't validate the context targets clinically or prove that the output is grounded rather than learned from source regularities.
- It doesn't choose between Track 2 and Track 3, select a checkpoint, authorize model promotion, or justify a readiness or novelty score increase by itself.

## Decision boundary

The response screen completed its historical narrow purpose, and the checkout can now independently establish its
recorded execution, reload, scoring, and exploratory-analysis claims. It still does not support choosing a winner,
candidate, objective, or track from these development results. A future decision-bearing experiment must independently
justify and freeze the candidate set, source admission, held-out confirmation population, task and context endpoints,
complete resampling algorithm and literals, and seed-level acceptance rules before any confirmation labels are opened.
