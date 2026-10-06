# Model metadata preflight — no weights or runtime

The working order stays Qwen2.5-VL-7B-Instruct for the first compatibility baseline, Qwen3.5-9B as the first challenger, and Qwen3-VL-8B-Instruct as the fallback. This is an execution order, not evidence that the first model will win. Final base selection requires the same reviewed development cohort, paired baseline/adapted predictions and measured resource use.

| Exact model | HF-reported checkpoint parameters | Reported tensor storage, GiB |
|---|---:|---:|
| [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) | 8,292,166,656 | 15.45 |
| [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | 9,653,104,368 | 17.98 |
| [Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) | 8,767,123,696 | 16.33 |

These counts come from the saved public Hugging Face API `safetensors` metadata. The arithmetic multiplies each reported dtype count by its storage size (BF16 two bytes, F32 four), then divides by 2^30. It has not independently enumerated loaded tensors, verified active parameters, or measured GPU memory. Tensor storage omits activations, gradients, optimizer states, image-token costs, caches, workspaces and framework overhead. Do not tell IT that a 16 GB GPU can train the first model based on this table.

Eight small configuration files were retrieved at the exact revisions in `configs/model-registry.json`; retrieval URLs, hashes, sizes and the one failed request are in `evidence/model-configs/retrieval.json`. Qwen3.5's pinned `generation_config.json` returned HTTP404; no replacement or generation defaults were guessed. No weights were downloaded.

Qwen3.5's config uses alternating linear/full attention, so assumptions from the two earlier Qwen architectures must be tested rather than carried over. The two Qwen3 configs identify different vision/deep-stack arrangements. Their native processor and chat-template behavior has now been exercised on CPU in the pinned environment; see `processor-compatibility.md`. Actual model loading and architecture-specific adaptation still require runtime checks. The `transformers_version` saved in a model config is serialization provenance; it is **not** a verified minimum working package version and should not be used as the installation requirement.

When Einstein returns, record GPU model/count/VRAM, quota, scheduler and wall-time limits first. Run a clean, pinned native loader and a small image forward pass; measure memory before selecting an adaptation strategy. Then verify task/context isolation, checkpoint initialization identity, bounded visual-adaptation support, and a BF16/FP16 reload/export path. The adaptation score rewards both final performance and measured improvement over the model's own base, so parameter count alone cannot select our entry.
