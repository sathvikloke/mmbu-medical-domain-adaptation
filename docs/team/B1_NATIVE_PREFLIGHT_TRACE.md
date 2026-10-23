# B1 native preflight trace

**Observed:** October 23, 2026  
**Evidence class:** exact pinned model/runtime on one real MOCS A100, generated synthetic engineering inputs only  
**Terminal result:** job `85418` completed with exit `0:0`; fresh offline reload passed  
**Admission decision:** the implemented bounded preflight passed; the broader `B1_RUNTIME_GATE.md` remains partial where explicitly listed below

## Claim boundary

This trace proves that the exact pinned Qwen2.5-VL-7B runtime can load on the observed MOCS node, process the frozen
synthetic still-image fixtures, execute the declared forward/cache/backward/one-step path, export a language-only LoRA
adapter, and reload that adapter in a fresh socket-denied process. It does **not** establish medical correctness,
biomedical-data validity, MMBU performance, official-evaluator equivalence, full-training feasibility, challenge-loader
acceptance, novelty, clinical benefit, or submission readiness. No MMBU or biomedical example, label, output,
embedding, or derivative entered any attempt.

## Frozen identity and scheduler receipt

| Item | Observed value |
|---|---|
| Model | `Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5` |
| Concrete model | `Qwen2_5_VLForConditionalGeneration` |
| Processor | `Qwen2_5_VLProcessor`; `Qwen2VLImageProcessorPil`; left padding |
| Runtime | Python 3.12.12; Torch 2.11.0+cu128; torchvision 0.26.0+cu128; Transformers 5.19.0; PEFT 0.21.2 |
| Effective condition | BF16, SDPA, dynamic cache, one visible GPU, no compilation/offload/distribution |
| Scheduler | job `85418`; `epyc-gpu`; `allusers`; `u-default`; 4 CPUs; 96 GiB; one A100 80 GB |
| Node/result | `epyc08`; `COMPLETED`; exit `0:0`; scheduler elapsed 49 s |
| Measured native section | 11.118 s; peak allocated 18,335,417,344 bytes; peak reserved 18,652,069,888 bytes |

The run-3 config canonical digest is
`6bf2ce0ff2bfac3677c526de5843250a58b4cc4f46fdcbc3dedbbbe80353cb2b`. Model and wheel bytes were reverified before
submission using the immutable run-1 acquisition inventories; local and remote source SHA-256s matched before the job.

## Executed checks

| Check | Result | Evidence |
|---|---|---|
| Ten generated fixture classes | passed | small, large, non-square, extreme aspect, grayscale, RGBA, real EXIF orientation, and 27/28/29 boundaries |
| Visual path dependence | passed | fixed-text image intervention changed the declared logit slice by `2.5` |
| Single vs heterogeneous batch | passed | maximum observed BF16 drift `0.125`, below prospective `0.5` tolerance |
| Reverse call order | passed | maximum drift `0.09375`, below tolerance |
| Repeated uncached prefill | passed | zero drift |
| Cached vs uncached prefill | passed | zero drift |
| First cached greedy step vs teacher-forced step | passed | maximum drift `0.0625`, below tolerance |
| MRoPE still-image temporal origin | passed | ten grid counts and ten position counts were all `1`; integer shapes/dtypes matched |
| Target-only shifted loss | passed | framework `10.575214385986328`; manual `10.575215339660645`; absolute delta `9.5367431640625e-07` |
| Language-only LoRA scope | passed | 56 exact q/v module paths; vision paths excluded |
| Gradient/update closure | passed | 112/112 finite declared gradients; expected 56 zero-B first-step B matrices changed; no undeclared update |
| Minimal export | passed | only `adapter_config.json` and `adapter_model.safetensors` |
| Serialized scope/state | passed | config retained all 56 exact paths; 112 exact language-only state keys; no suffix-broadened target |
| Fresh offline reload | passed | new process, empty job-specific cache, socket negative control proven, token/pixel identities equal, logit drift `0` |
| Full local software suite | passed | 322 Phase 1 CPU tests in the final pre-submit run; repository smoke, evidence, links, and contract checks also passed |

## Evidence hashes

| Artifact | SHA-256 |
|---|---|
| `native-preflight.json` | `51dd575cdb5049f8a46a7468a2a6125696d298be0cec8dc831f49a844d4b272f` |
| `offline-reload.json` | `309973ec9e21997b2bb78f3e387c06987798e4ab974b22003a97e3b2c57ce4e9` |
| `terminal-run.json` | `1e232240f973d1216cbb2349ae9ca4509ed06af60fd1316b70fe4bf8aa683fa6` |
| `adapter_config.json` | `214f13249893af445c9081a16d9a9d27e52e0b9c2796e2e626943771b236bf3b` |
| `adapter_model.safetensors` | `c0541a95026a1e54198b1e1d443c59e47a977ae25a854ea616917bce66a61084` |
| `slurm-85418.out` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `slurm-85418.err` | `911c7e541a444e8f7df444f6cb7a77931adbda097141c87d7ffdcb89c5440c8f` |

The canonical records, their embedded source/evidence inventories, the adapter file inventory, exact target list, and
state-key list were independently re-read and recomputed after transfer from MOCS. The local verification did not trust
the job's terminal label alone.

## Preserved adverse history

| Attempt | Outcome | Disposition |
|---|---|---|
| `85410` | failed before model load because the script replaced Slurm's assigned GPU visibility | preserved as `outputs/B1-native-attempt-85410.json`; no scientific output |
| `85413` | reached the synthetic optimizer step, then an invalid all-tensors-must-update assertion rejected standard zero-B LoRA behavior | preserved as `outputs/B1-native-attempt-85413.json`; validator corrected prospectively |
| `85415` | runtime and offline replay completed, but independent review found PEFT had serialized exact targets as broad suffixes | preserved as `outputs/B1-native-attempt-85415.json`; packaging not admitted |
| `85418` | exact-target export and reload passed | admitted only for the bounded implemented checks above |

No result value selected a model, target, seed, optimizer, tolerance, or scientific recipe across these envelopes.
Each successor changed only a preserved mechanical failure condition and wrote to a clean evidence root.

## Remaining B1 contract gaps

The following `B1_RUNTIME_GATE.md` requirements are not fully discharged by job `85418` and remain blocking for a
claim that the entire broader gate passed:

1. generation was not compared over a multi-token greedy sequence in two fresh processes; only prefill and the first
   cached step were checked;
2. cached execution was not interleaved with a text-only request and was not checked at every generation step;
3. per-fixture processed dimensions, resize rounding, forward/inverse coordinate transforms, and coordinate round-trip
   evidence were not emitted as a closed record;
4. a full batch was not compared with equivalent accumulated microbatches;
5. every base/cache/loss/gradient/optimizer tensor dtype and optimizer-state shape was not inventoried individually;
6. throughput, CUDA driver/runtime identity, command-line receipt, and complete post-run resource accounting were not
   captured in one canonical record;
7. neither an official challenge loader nor any biomedical or MMBU evaluation was run.

These gaps do not invalidate the bounded runtime result. They prevent promotion from “native path demonstrated” to
“complete B1 gate passed” and prevent any competition-performance or medical claim.
