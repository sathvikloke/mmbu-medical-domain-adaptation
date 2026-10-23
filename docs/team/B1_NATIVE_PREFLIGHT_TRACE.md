# B1 native preflight trace

**Observed:** October 23, 2026

**Evidence class:** exact pinned model/runtime on one real MOCS A100, generated synthetic engineering inputs only

**Terminal result:** job `85434` completed with exit `0:0`; fresh network-denied reload passed

**Admission decision:** the extended synthetic native gate passed; the broader competition and biomedical gates remain partial

## Claim boundary

This trace proves that the exact pinned Qwen2.5-VL-7B runtime can load on the observed MOCS node, process the frozen
synthetic still-image fixtures, execute the declared forward/cache/backward/one-step path, export an exact
language-only LoRA adapter, and reproduce three greedy tokens in a fresh socket-denied process. It does **not**
establish medical correctness, biomedical-data validity, MMBU performance, official-evaluator equivalence,
full-training feasibility, novelty, clinical benefit, or submission readiness. No MMBU or biomedical example, label,
output, embedding, or derivative entered any attempt.

## Frozen identity and scheduler receipt

| Item | Observed value |
|---|---|
| Model | `Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5` |
| Concrete model/processor | `Qwen2_5_VLForConditionalGeneration`; `Qwen2_5_VLProcessor`; `Qwen2VLImageProcessorPil` |
| Runtime | Python 3.12.12; Torch 2.11.0+cu128; torchvision 0.26.0+cu128; Transformers 5.19.0; PEFT 0.21.2 |
| Effective condition | BF16, SDPA, dynamic cache, left padding, one visible GPU, no compilation/offload/distribution |
| Scheduler | job `85434`; `epyc-gpu`; `allusers`; `u-default`; 4 CPUs; 96 GiB; one A100 80 GB |
| Node/result | `epyc09`; `COMPLETED`; exit `0:0`; scheduler elapsed 51 s |
| GPU/runtime | NVIDIA A100 80 GB PCIe; driver 595.71.05; CUDA 12.8; compute capability 8.0 |
| Measured native section | 12.883 s; peak allocated 18,427,891,712 bytes; peak reserved 18,677,235,712 bytes |

The run-9 config canonical digest is
`264d94b750e7aed56172088699f42e7e2787b3e6e77946aa2b027b0dd353309e`. Model and wheel bytes were reverified before
submission using the immutable run-1 inventories; local and remote executable source hashes matched before the job.

## Executed checks

| Check | Result | Evidence |
|---|---|---|
| Ten generated fixture classes | passed | small, large, non-square, extreme aspect, grayscale, RGBA, real EXIF orientation, and 27/28/29 boundaries |
| Per-fixture geometry | passed | processed dimensions, grid/token identity, scaling, and coordinate round-trip emitted for all ten fixtures; max round-trip error `0` |
| Visual path dependence | passed | fixed-text image intervention changed the declared logit slice by `2.5` |
| Single vs heterogeneous batch | passed | maximum observed BF16 drift `0.125`, below frozen `0.5` tolerance |
| Reverse call order | passed | maximum drift `0.09375` |
| Cache and interleaving | passed | repeated prefill drift `0`; text-only interleave drift `0`; first cached-step drift `0.0625` |
| MRoPE still-image temporal origin | passed | ten grid counts and ten position counts were all `1`; integer shapes/dtypes matched |
| Target-only shifted loss | passed | framework `10.575214385986328`; manual `10.575215339660645`; delta `9.5367431640625e-07` |
| Full batch vs two weighted microbatches | passed | loss delta `0.0014858245849609375 ≤ 0.00390625`; gradient max `0.014532973524183035 ≤ 0.03125`; relative L2 `0.04882238470030118 ≤ 0.05`; cosine `0.9988091154245559 ≥ 0.99875` |
| One full-batch optimizer step | passed | repeated full-batch loss delta `0`; one AdamW step only |
| Trainable/optimizer inventory | passed | 112 trainable parameter/gradient rows and 336 finite optimizer-state tensor rows with names, shapes, and dtypes |
| Three-step cached generation | passed | cached token, generated token, and full teacher-forced argmax were exactly equal at all three steps; full-vocabulary drift retained diagnostically |
| Language-only LoRA scope | passed | 56 exact q/v module paths; vision paths excluded |
| Gradient/update closure | passed | 112/112 finite declared gradients; expected 56 zero-B first-step B matrices changed; no undeclared update |
| Minimal export | passed | only `adapter_config.json` and `adapter_model.safetensors` |
| Serialized scope/state | passed | config retained all 56 exact paths; 112 exact language-only state keys |
| Fresh offline reload | passed | fresh process, empty job cache, socket denial proven, token/pixel identities equal, three generated tokens exact, logit drift `0` |
| Full local software suite | passed | 326 Phase 1 CPU tests in the final pre-submit run |

## Evidence hashes

| Artifact | SHA-256 |
|---|---|
| `native-preflight.json` | `f37aff85a5579cb868363e15b5b9760f3ae32c109c617358880879c5b2a18fdd` |
| `offline-reload.json` | `ef67bf28e80333c2fa4afbc86b24a34f5f140b275f81bb5da1bf8d4c4801f092` |
| `terminal-run.json` | `5d4bdd612bfcdf42da3b446d17defab74a44c37ea59deba1a30f9167b16c75a6` |
| `adapter_config.json` | `214f13249893af445c9081a16d9a9d27e52e0b9c2796e2e626943771b236bf3b` |
| `adapter_model.safetensors` | `c0541a95026a1e54198b1e1d443c59e47a977ae25a854ea616917bce66a61084` |
| `slurm-85434.out` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `slurm-85434.err` | `b6c3dc9314583fd71e33a74ec036c9bec2c1d35ce3b4bfeb9bcadc85d4ca723c` |

The records, embedded source/evidence inventories, adapter file inventory, exact target list, and state-key list were
independently re-read and recomputed after transfer from MOCS. The local verification did not trust the terminal label.

## Preserved adverse history

| Attempt | Outcome | Disposition |
|---|---|---|
| `85410` | script replaced Slurm GPU visibility before model load | preserved; no scientific output |
| `85413` | invalid all-tensors-must-update assertion rejected standard zero-B LoRA | preserved; invariant corrected prospectively |
| `85415` | runtime passed but PEFT serialized exact targets as broad suffixes | preserved; packaging not admitted |
| `85418` | exact-target export and fresh offline reload passed | admitted bounded run-3 result |
| `85423` | FP32-scale microbatch loss bound rejected without reporting values | preserved; no optimizer step |
| `85425` | measured loss drift `0.0014858245849609375` | preserved; BF16-derived bound frozen afterward |
| `85427` | measured gradient max drift `0.014532973989844322` | preserved; scale/direction contract frozen afterward |
| `85429` | passed magnitude bounds; cosine `0.9988091154245559` exposed inconsistent independent floor | preserved; floor derived from frozen relative radius |
| `85432` | arbitrary-logit generation proxy failed after optimizer step | preserved; replaced by exact decision invariant |
| `85434` | extended gate and exact fresh reload passed | admitted only for the implemented synthetic checks above |

No result selected a model, checkpoint, fixture, seed, optimizer, or biomedical recipe. Each successor addressed one
preserved mechanical/measurement defect, used a clean evidence root, and retained the synthetic-only boundary.

## Remaining B1 and competition gaps

1. Base-model and cache tensor dtypes are summarized but not emitted as an individual closed row for every tensor.
2. Scheduler utilization accounting is limited to allocation, elapsed time, and process-level peak CUDA memory; it is
   not a full end-to-end training throughput or cluster-efficiency study.
3. No official challenge loader, hidden evaluator, biomedical source, MMBU public/private example, or source-data
   admission path has run.
4. No full training, model selection, ablation, calibration, clinical review, or competition-performance experiment has
   run; the evidence is runtime feasibility only.

These gaps do not invalidate the extended synthetic runtime result. They block any claim of medical validity,
competition quality, or complete launch readiness.
