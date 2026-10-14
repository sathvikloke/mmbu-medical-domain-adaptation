# B1 native runtime admission gate

**Revision:** 2026-10-14-cycle-34  
**Status:** binding Phase 1 design; unexecuted  
**Model:** `Qwen/Qwen2.5-VL-7B-Instruct@cc594898137f460bfe9f0759e9844b3ce807cfb5`

This file governs the first real model/GPU probe. A paper pin, successful import, one-image demo, or green CPU suite does not admit B1.

## Exact runtime candidate

The first candidate is Transformers `5.19.0`:

| Identity | Value |
|---|---|
| Tag | `v5.19.0` |
| Annotated tag object | `b39d97c836e8d9f0ee6035a87c7a3ce5eaea43a8` |
| Peeled commit | `c4c4605f961877852b89b97478536bb3a26b6fd1` |
| Wheel | `transformers-5.19.0-py3-none-any.whl` |
| Wheel bytes | `12599123` |
| Wheel SHA-256 | `afcd2dd5f603ed28c1e1fcb00a338ccbb4ef5f878ed289635df8b58187afb518` |
| Source distribution SHA-256 | `87f38dd25e4521151b97e94520ac457f44a0ae8a8358a5b112daff6c64a822d6` |
| Python metadata boundary | `>=3.10`; the exact interpreter remains environment-bound |
| B1 modeling source SHA-256 | `c64c794741011b27c773a1e2299d5fc2abd1e49e79f8d11ce87b2b308e9bf205` |
| B1 native test source SHA-256 | `df768c85bd6943af303fe188e11beacbad4931f07e638206b6af8cccb5f2b7ce` |
| B1 processor source SHA-256 | `dcecc3dff4ebb07c58e66923f1d62c73edee1edf572d27947c27ee5f5f2e654f` |
| Shared fast image-processor source SHA-256 | `d5558cd419c8d46bdc958064cb97f963d1ea793866414c025906ec15033512ed` |

These identities nominate D1. They do not prove compatibility. The complete resolved environment requires exact artifacts and hashes for Python, PyTorch, torchvision, Pillow, NumPy, CUDA runtime, driver, GPU, Accelerate, tokenizers, Safetensors, PEFT, optimizer, and every imported or built dependency after the MOCS route is measured. Floating branches, nightlies, editable installs, unhashed VCS dependencies, and result-selected versions fail.

## Reference condition

- concrete `Qwen2_5_VLForConditionalGeneration`; the exact model processor configuration loaded with image backend `pil`, with effective backend and resolved processor/image-processor classes asserted;
- `trust_remote_code=false`, `use_kernels=false`, and no network after artifact closure;
- BF16 on a named compatible GPU; unsupported hardware fails the reference condition. FP16 is a separately locked condition, never an automatic fallback. Capture requested and effective dtype for every model component, cache, loss, gradient, and optimizer state;
- single GPU, explicit placement, dynamic cache, and `attn_implementation="sdpa"` for the full reference path; eager is a separately labeled tiny-fixture numerical oracle, not an interchangeable full condition;
- no FlashAttention 2, static cache, chunked prefill, continuous batching, packing, compilation, gradient checkpointing, FSDP, tensor parallelism, CPU offload, speculative decoding, or silent backend fallback; gradient accumulation is 1 for the reference step;
- local decoded RGB still images only; no URL fetch, video, `qwen-vl-utils`, `decord`, or external decoder in the reference path;
- set tokenizer `padding_side="left"`, apply the exact template per logical example, and use explicit padded batching;
- use the deterministic non-inherited engineering decoding in `b1-pin.json`;
- clear or prove correct all position/cache state between logical requests.

The publisher-pinned `qwen-vl-utils==0.0.8` is a stale convenience input layer, not a required image-only model dependency or a future admission choice. If a later non-image condition needs the utility, nominate an exact stable release, preserve every utility/decoder artifact, and pass a separate input-equivalence and offline-replay gate.

## Preprocessing and geometry record

Every input records:

```text
raw_sha256 raw_width raw_height raw_mode
exif_orientation_policy color_conversion_policy
processor_class image_processor_class image_backend processor_config_hash
tokenizer_class padding_side
min_pixels max_pixels resize_resample_rounding
processed_height processed_width processed_tensor_sha256
image_grid_thw visual_token_count
coordinate_transform_forward coordinate_transform_inverse
```

The locked fixture contains small, large, non-square, extreme-aspect, grayscale, RGBA/transparency, and EXIF-rotated images; below/above-bound cases; 27/28/29-pixel boundaries; different prompt lengths; and a heterogeneous-resolution batch. It asserts decoded RGB bytes, resized dimensions, grid, token count, pixel tensor hash, and coordinate round trip. The pixel/token policy must be frozen from publisher-documented or admitted external evidence before comparative output. MMBU public outcomes cannot select it. Detection coordinates remain original-pixel `xywh`; the recorded transformation must round-trip without clipping, silent repair, or unexplained rounding.

## Required positive and negative evidence

1. Verify `b1-pin.json`, the exact index, all five shards, all metadata, and header-derived totals before load.
2. Assert the concrete class, vision tower, processor/template resolution, image placeholders, processed grid, and visual-token count.
3. Hold text fixed and change the fixture image; prove the visual path changes the declared logits while all request identities are recorded.
4. Evaluate every fixture alone and in the same padded heterogeneous batch. Compare token IDs and prospectively bounded logits.
5. Generate twice on one object, reverse fixture order, then repeat in fresh processes. Reject stale `rope_deltas` or call-order effects.
6. Compare prefill and every cached greedy step using a fresh dynamic cache with `use_cache=false` teacher-forced logits under a precommitted tolerance; reverse call order, interleave a text-only request, and never carry caller cache across records.
7. Check expected MRoPE positions for small still-image grids and padded members, including temporal origin and dtypes.
8. Run the real native-collator forward, backward, and minimal optimizer step with `use_cache=false`, target-only labels, and `-100` for every excluded token. Require finite parameters/logits/loss/gradients/state, correct text vocabulary and loss shape, manually shifted-CE agreement, and gradients in every declared trainable module. A separately labeled check compares one full batch with equivalent accumulated microbatches.
9. Inventory serialized, retained unique, forward-active, and trainable parameters with alias handling.
10. Save the minimal adapter/config and reload the closed base, adapter, processor, and template in a fresh network-denied clean-cache process. Assert top-level and nested model/config types, concrete class, PIL backend/config hash, adapter targets, pixel tensor hash, first-step logits, token IDs, and adapter/config hashes.
11. Record peak allocated/reserved memory, timing, throughput, environment, effective settings, commands, logs, exit codes, and evidence hashes.

Batch-size-1 success cannot satisfy item 4. Requested settings cannot replace backend-effective evidence. A mock/tiny model may test plumbing but cannot verify any native B1 row.

## Dependency replacement

D1 may change only after a preserved mechanical failure. The amendment must identify an exact release or commit whose named upstream change directly addresses that failure, update this manifest-covered contract before biomedical or B1/B2 comparative output opens, and repeat every gate. Dependency versions cannot be selected for better MMBU public or external biomedical scores.

## Optimization promotion

Torchvision processing or any other excluded optimization may enter only through a prospectively locked condition with complete dependency closure and the same class/vision, decoded-pixel/tensor/grid, preprocessing, position, single/batch, repeated-call, cached/uncached, training-numerics, parameter, coordinate, save/reload, and offline tests. Any numerical tolerance names the compared object, aggregation, threshold, rationale, and hardware scope before output opens. Speed never rescues correctness.

## Claim boundary

Passing this gate proves only the declared B1 runtime condition is mechanically reproducible enough to begin allowed external engineering. It does not prove biomedical validity, model improvement, official-harness equivalence, rule eligibility, compute feasibility for the full program, or competition performance.
