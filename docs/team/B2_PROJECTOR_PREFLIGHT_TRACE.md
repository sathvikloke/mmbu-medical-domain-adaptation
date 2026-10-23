# B2-P native projector preflight trace

**Date:** October 23, 2026

**Scope:** synthetic engineering feasibility only

**Model:** pinned `Qwen/Qwen2.5-VL-7B-Instruct` revision `cc594898137f460bfe9f0759e9844b3ce807cfb5`

**Successful MOCS job:** `85459`

## Result

The base-architecture-preserving B2-P mechanical path passed on one MOCS A100. The run used two generated RGB fixtures,
one optimizer step, no biomedical or MMBU inputs, and network-denied model and adapter reload.

| Gate | Recorded result |
|---|---|
| Exact trainable scope | 117 tensors: 112 language `q_proj`/`v_proj` LoRA tensors plus five native `model.visual.merger` tensors |
| Finite backward | Every declared trainable tensor had a finite gradient; the manual shifted-token cross entropy differed from framework loss by `9.5367431640625e-7` |
| First-step update | Exactly 61 expected tensors changed: 56 zero-B-initialized LoRA-B tensors and all five projector tensors |
| Standard export | 117 exact state keys; no vision block outside the merger was serialized; adapter payload is 91,689,000 bytes |
| Fresh reload | Separate process, local files only, socket denial proven, maximum absolute logit drift `0` |
| Native resource envelope | 23.874 seconds inside the measured native section; peak CUDA allocated 17,592,894,976 bytes and reserved 18,056,478,720 bytes |
| Scheduler result | `COMPLETED`, exit `0:0`, elapsed `00:01:16` on `NVIDIA A100 80GB PCIe` |

The cluster's low-frequency `jobstats` sampler reported zero percent utilization and 1.2 GiB maximum GPU memory for
this short job. That conflicts with the in-process CUDA allocator receipt and is retained as a monitoring limitation,
not silently substituted for the direct measurement.

## Preserved failure

Job `85458` failed before model load because the richer paper pin was passed directly to a closed six-field artifact
verifier. The terminal receipt is preserved. A regression test now requires an explicit projection of the full pin into
the verifier shape. Attempt 2 used a new run directory; it did not overwrite attempt 1.

## Evidence

- [Evidence manifest](../../outputs/b2-projector-preflight/manifest.json)
- [Failed terminal receipt](../../outputs/b2-projector-preflight/attempt-1/terminal-run.json)
- [Native preflight receipt](../../outputs/b2-projector-preflight/attempt-2/native-preflight.json)
- [Offline reload receipt](../../outputs/b2-projector-preflight/attempt-2/offline-reload.json)
- [Successful terminal receipt](../../outputs/b2-projector-preflight/attempt-2/terminal-run.json)
- [Exported adapter configuration](../../outputs/b2-projector-preflight/attempt-2/adapter/adapter_config.json)

The 91.7 MB adapter tensor file remains at the recorded MOCS path and is represented by exact size and SHA-256 in the
manifest rather than duplicated in Git.

## Claim boundary

This establishes only that the selected native projector-plus-language-LoRA mechanism can load, receive gradients,
take one synthetic step, export through standard PEFT, and reload offline in the tested environment. It does not show
answer/context benefit, biomedical validity, official-loader acceptance, benchmark performance, novelty, clinical
impact, private-set generalization, or competition readiness.
