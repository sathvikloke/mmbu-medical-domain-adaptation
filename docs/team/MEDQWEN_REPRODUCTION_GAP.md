# Sparse Spectral LoRA / MedQwen reproduction-gap audit

**Inspected:** October 17, 2026  
**Sources:** [CVPR 2026 paper](https://arxiv.org/html/2604.01310v1),
[project page](https://omid-nejati.github.io/MedQwen/), and
[official repository](https://github.com/IMPACT-L/MedQwen)  
**Status:** mandatory literature baseline, not locally reproduced

## Confirmed from the paper

| Item | Reported value |
|---|---|
| Base family | Qwen2.5-VL 7B; exact repository revision not reported |
| Architecture | SVD-segment-initialized LoRA experts with residual compensation and learned top-k routing |
| VQA total rank | 32 |
| VQA alpha | 64 |
| Expert routing | 8 experts, 2 activated per token |
| Optimizer | AdamW |
| VQA batch size | 16 |
| VQA learning rate | 1e-4 |
| Warmup | 100 steps |
| Dropout | 0.05 |
| Balance-loss coefficient | 1e-3 |
| Damping parameter | rho = 10 |
| Precision | BF16 |
| Hardware | VQA/classification on one A100 40 GB; some ablations/report generation on four A100 40 GB |
| Training stages | 500K LLaVA-Med alignment; 60K instruction examples; reported 2.4M stage-3 mixture |
| Reported VQA resource point | 32.56 GB and 29h19m “epoch time” at the table's stated comparison setting |

These are paper claims. They do not establish that our hardware, software, data, or implementation will reproduce them.

## Missing or insufficient for a faithful implementation

| Gap | Why it matters | Required resolution |
|---|---|---|
| Official code | The inspected official repository has one commit and only `README.md` | Pin a later code commit if released; otherwise label any implementation independent and non-equivalent |
| Checkpoint | No official tensor checkpoint was established | Do not cite paper performance as starting-checkpoint performance |
| Exact base revision | “Qwen2.5-VL 7B” does not identify immutable weights/processor/template | Resolve model, processor, tokenizer, template, and code revisions and hashes |
| Target modules | Paper does not name exact attention/MLP/vision/projector matrices receiving experts | Derive a candidate map, then treat it as our design choice unless authors/code confirm it |
| Expert granularity | Formula is generic; exact layers and whether routing is token-, layer-, or modality-specific are incomplete | Record router location, input, sharing, and every adapted tensor |
| SVD algorithm | Exact implementation, numerical backend, full/randomized SVD choice, ordering/sign handling, dtype, and cache are absent | Specify and test deterministic initialization per tensor |
| Residual estimate | The population/sample used to estimate the router expectation for residual compensation is absent | Define a frozen eligible calibration population or derive an exact initialization rule; never use MMBU public data |
| Epoch/update counts | Hyperparameter tables omit VQA epoch count and total optimizer updates | Use a prospectively budgeted pilot; do not infer from the 29h19m table entry |
| Scheduler details | Warmup is reported, but scheduler, decay, clipping, weight decay, betas, accumulation, and seed are not fully closed | Declare every optimizer/scheduler leaf before execution |
| Data mixture | Exact versions, files, splits, deduplication, mixture weights, sampling order, prompts, transformations, and exclusions are missing | Rebuild only from independently admitted sources and publish our own lineage |
| Image/token policy | Resolution, min/max pixels, tiling, truncation, token limits, and answer templates are not closed | Bind them in the execution condition and measure native behavior |
| Save/load/export | No fresh offline reload, merged-artifact, `trust_remote_code`, or challenge-loader procedure is established | Pass the same hermetic export/reload gate as every submission candidate |
| Runtime | Paper hardware is A100 40 GB, not a guarantee for UTC MOCS queues or the organizer evaluator | Measure one authorized local load/forward/step/export/reload before estimating schedule |
| Rights/release | Paper dataset use does not grant our use or redistribution of weights | Independently review every source and final model release obligation |

## Methodological cautions

The paper's router-moment derivation assumes exchangeable/independent symmetric logits for the initialization result.
Learned router logits need not retain those assumptions. A local reproduction must directly measure initialization drift
and route balance rather than treating the theorem as runtime evidence.

The reported stage-3 corpus is roughly 2.4 million examples and the VQA comparison reports about 29 hours per epoch on
one A100 40 GB. This is not a cheap first experiment. Our pilot must use a bounded admitted subset and prove mechanics
before any scale-up. A smaller pilot tests feasibility, not the paper's reported quality.

## Exact read-only Claude work order

Claude may inspect the paper and current Qwen module tree without downloading weights or training:

1. Produce a paper-equation-to-module table, marking every unresolved mapping as `unknown`.
2. Identify which Qwen2.5-VL linear tensors could satisfy the paper equations and report shapes/counts without selecting
   them as final targets.
3. Estimate full versus randomized SVD memory/time for each candidate tensor on CPU and one A100 80 GB; label estimates.
4. Specify deterministic synthetic tests for non-overlapping spectral segments, residual initialization, top-2 routing,
   dtype/autocast, state-dict closure, and network-denied reload.
5. Compare the required custom module with the organizer's still-unknown loader contract.
6. Return a gap table; do not fill missing paper facts with defaults.

## Decision

B4 remains a literature baseline and potential independent reproduction. It is not an available drop-in model. It may
enter a biomedical comparison only after source admission, implementation review, synthetic conformance, native runtime
measurement, and packaging approval. Until then, B2 is the executable fallback and MOSAIC cannot claim superiority over
medical routed adaptation.
