# Native CPU processor compatibility

The three pinned candidates completed synthetic native tokenizer, chat-template and image-preprocessor checks using CPU tensors. This establishes a usable preprocessing path for the tested environment, with the constraints below. No model class was instantiated, model weights downloaded, forward pass run, activation inspected, or GPU used. It provides no model-quality, training, memory-fit, export or official-harness evidence. The registry's earlier `runtime_verified: false` remains appropriate for model execution.

## Reproduce the tested environment

The bundled Python was inspected first: Python 3.12.14 had NumPy/Pillow but lacked Transformers, PyTorch, torchvision, tokenizers and Hugging Face Hub. The isolated environment is at `work/processor-probe/.venv` relative to the project root, outside the release package. The tested versions are Transformers 5.18.0, torch 2.14.1, torchvision 0.29.1, Pillow 12.3.0, NumPy 2.5.3, tokenizers 0.23.2 and huggingface-hub 1.33.0 on macOS arm64. These are **tested versions**, not inferred minimum requirements. A config's `transformers_version` is not used to select dependencies.

The complete pins are in [processor-requirements.txt](../evidence/processor-requirements.txt). The [pip installation report](../evidence/processor-install-report.json) records package artifact URLs and hashes. Installed upstream source hashes and version-tagged URLs are in [processor-upstream-sources.json](../evidence/processor-upstream-sources.json).

Run from the project root, with a writable isolated Python 3.12 environment:

```sh
python3.12 -m venv work/processor-probe/.venv
work/processor-probe/.venv/bin/python -m pip install -r outputs/mmbu-precompute/evidence/processor-requirements.txt
work/processor-probe/.venv/bin/python outputs/mmbu-precompute/tools/processor_probe.py \
  --download --artifacts work/processor-probe/artifacts \
  --output work/processor-probe/reproduction-download.json
work/processor-probe/.venv/bin/python outputs/mmbu-precompute/tools/processor_probe.py \
  --offline --artifacts work/processor-probe/artifacts \
  --output work/processor-probe/reproduction-offline.json
```

Offline is also the default. `--model Qwen/Qwen3.5-9B` selects one registry entry; `--revision FULL_40_CHARACTER_SHA` can override its revision only when one explicit model is selected. Mutable names such as `main` are rejected. Different revisions or environments require fresh evidence. The full package freeze includes platform-specific availability; it is not a claim that these pins install unchanged on every platform.

Only a fixed list of tokenizer/config/template filenames is downloaded, with limits of 40 MiB per file and 96 MiB per checkpoint. The actual artifacts total 45,900,851 bytes across these three snapshots; their complete URLs, sizes, hashes and optional-file HTTP404 outcomes are in the report. No safetensors files or index files are requested. Native `AutoProcessor.from_pretrained` is always called against the local snapshot with `local_files_only=True, trust_remote_code=False`. Offline mode also sets the Hub/Transformers offline environment flags. Offline loads check recorded hashes, required files, identity and unexpected files. These hashes establish reproducibility of retrieved bytes, not independent publisher authentication.

Missing dependencies produce a machine-readable `unavailable` result and exit 2; they are not reported as passing probes. This behavior was executed with the original bundled runtime: [missing-dependency report](../evidence/processor-missing-dependencies.json). Snapshot absence, hash mismatch and loader errors are likewise explicit. The program exits 0 only when all required RGB and chat-isolation checks pass. Native16, extreme-aspect and assistant-alignment observations must still be read separately; a successful run does not certify those inputs as safe training data.

## Exact snapshots and native classes

| Candidate | Revision | Processor / tokenizer |
| --- | --- | --- |
| Qwen2.5-VL-7B-Instruct | `cc594898137f460bfe9f0759e9844b3ce807cfb5` | `Qwen2_5_VLProcessor` / `Qwen2Tokenizer` |
| Qwen3.5-9B | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | `Qwen3VLProcessor` / `Qwen3_5Tokenizer` |
| Qwen3-VL-8B-Instruct | `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` | `Qwen3VLProcessor` / `Qwen2Tokenizer` |

All resolved to `Qwen2VLImageProcessor` with the torchvision backend in this environment. Qwen2.5 uses patch size 14; the two newer snapshots use 16. All use merge size 2 and temporal patch size 2. The class names alone do not fix preprocessing: checkpoint configuration changes bounds and normalization. [Transformers image processor source](https://github.com/huggingface/transformers/blob/v5.18.0/src/transformers/models/qwen2_vl/image_processing_qwen2_vl.py)

## RGB resizing and image tokens

Each synthetic RGB image contains a rectangle and ellipse on a solid background. Outputs were encoded twice, requiring equal dtype/shape/hash/summary for every returned tensor, finite values, CPU placement and matching image-placeholder count. The observed count equals `sum(t*h*w / merge_size**2)` for `image_grid_thw`. The corresponding height/width below are inferred from the grid times patch size. This agrees with the [native replacement code](https://github.com/huggingface/transformers/blob/v5.18.0/src/transformers/models/qwen3_vl/processing_qwen3_vl.py).

| Input width × height | Qwen2.5 output width × height / tokens | Qwen3.5 and Qwen3-VL output width × height / tokens |
| --- | --- | --- |
| 64 × 64 | 56 × 56 / 4 | 256 × 256 / 64 |
| 301 × 199 | 308 × 196 / 77 | 320 × 224 / 70 |
| 640 × 480 | 644 × 476 / 391 | 640 × 480 / 300 |
| 1024 × 256 | 1036 × 252 / 333 | 1024 × 256 / 256 |
| 1600 × 1200 | 1596 × 1204 / 2451 | 1600 × 1216 / 1900 |
| 640 × 480, explicit bounded size | 280 × 196 / 70 | 288 × 192 / 54 |

The last row sets `size={"shortest_edge":4096,"longest_edge":65536}`. For this processor these fields bound pixel **area**, despite the names. Native snapshot defaults are 3,136–12,845,056 pixels for Qwen2.5 and 65,536–16,777,216 for both newer checkpoints. Native rounding operates at patch × merge granularity, so neither exact dimensions nor exact aspect ratio should be assumed. The bounded case is an engineering probe, not a selected task preprocessing policy. Detection-coordinate conversion remains a separate contract decision.

All three rejected the synthetic 1 × 512 extreme-aspect input with the native ratio error. Its ambiguous-channel warning is retained. The test did not allocate images near the native maximum bounds.

## Task/context isolation and assistant boundaries

The script uses the package's existing `build_task_input` and `build_context_input` selectors, then constructs fresh native messages. Poison sentinels in reference answer, options, reference context, history, messages and previous prediction never appear in either rendered input. Changing those fields leaves task token IDs unchanged; changing them plus the question leaves context token IDs unchanged. Both renders contain one image placeholder; generation markers and deterministic rendering/tokenization are checked. These are selector/template checks only: they do not verify conversation-cache or model-state isolation during inference. Synthetic prompts and requested field names are engineering fixtures, not a proposed official prompt.

For the toy assistant response `{"answer": "synthetic"}`, the probe encodes both the generation prompt and full conversation with the same 64 × 64 image, then compares the actual multimodal input IDs. A label boundary is reported only when the entire prompt is an exact token prefix:

| Candidate / template arguments | Prefix outcome | Native suffix |
| --- | --- | --- |
| Qwen2.5 / defaults | Exact prefix | JSON + `<\|im_end\|>` + newline |
| Qwen3-VL / defaults | Exact prefix | JSON + `<\|im_end\|>` + newline |
| Qwen3.5 / defaults | **Mismatch; no mask boundary inferred** | Not assigned |
| Qwen3.5 / `enable_thinking=False` | Exact prefix | JSON + `<\|im_end\|>` + newline |

Qwen3.5's default generation prompt opens a thinking block. The native full conversation with a plain JSON answer inserts a closed thinking block, so simply masking the number of prompt tokens is incorrect. The evidence includes both rendered forms, full token IDs and the first differing index. With `enable_thinking=False`, the prompt includes the closed empty thinking block and the prefix check succeeds. This flag is absent from the Qwen2.5 and Qwen3-VL native template variables, so those variants are marked unsupported rather than treated as meaningful controls. A future collator must derive and validate boundaries per example; fixture token lengths are not constants. No training loss was computed.

For every supported alignment variant, integrated `apply_chat_template(..., tokenize=True, return_dict=True, return_tensors="pt", processor_kwargs={"device":"cpu"})` produced identical tensor summaries to separate native rendering plus `processor(text=..., images=...)`, for both prompt and full conversation. The image was an in-memory synthetic PIL object; no external image URL was loaded.

## Synthetic native16 and floating-point hazards

The native16 fixture has seven source levels: 0, 1, 255, 256, 1024, 32768, 65535. On all three processors:

- PIL `I;16` is accepted, but its processed tensors are exactly equal to explicitly applying PIL's RGB conversion first. All source levels above 255 collapse to 255, leaving only three distinct pixel levels. No warning was emitted for this loss.
- A two-dimensional NumPy uint16 input is rejected. Expanding it into three channels makes it accepted, but the default scale treats values as if their range were 0–255. The returned normalized maxima reach about 981.78 for Qwen2.5 and 513 for the two newer snapshots. Successful encoding is not valid native16 handling.
- Already normalized float RGB in [0,1] is rescaled again by default, without a captured warning. Passing `do_rescale=False` changes the result as expected. This still does not guarantee equality to uint8/PIL preprocessing: resizing/interpolation can differ with dtype, including float bicubic overshoot.

The underlying [RGB conversion helper](https://github.com/huggingface/transformers/blob/v5.18.0/src/transformers/image_transforms.py) invokes PIL RGB conversion for PIL inputs and leaves NumPy inputs unchanged; the [backend](https://github.com/huggingface/transformers/blob/v5.18.0/src/transformers/image_processing_backends.py) supplies the later conversion/rescaling path. Source-native16 images therefore need a reviewed, explicit display mapping with recorded provenance before any model input. This probe does not choose that mapping or interpret biomedical labels.

## Saved verification

[processor-probe.json](../evidence/processor-probe.json) is the final offline execution, including artifact and script hashes, exact environment, warnings, tensor summaries, rendered prompts and alignment diagnostics. [processor-probe-log.txt](../evidence/processor-probe-log.txt) contains its process output. [processor-verification.json](../evidence/processor-verification.json) records the executed commands and exit codes: 0 for the native probe, the expected 2 for missing dependencies, and 0 for helper tests. Eight focused artifact-helper guard tests passed: offline retrieval avoidance, tamper detection, weight-file rejection, unmanifested optional-file rejection, identity mismatch, filename allowlist, mutable-revision rejection and bounded download rejection. Their executed log is [processor-helper-tests.txt](../evidence/processor-helper-tests.txt); the original test driver is retained in `work/processor-probe/test_processor_probe.py`; the same eight guards are now included with a portable path in `tests/test_processor_artifacts.py`. No existing core module, registry or CLI was changed by this probe.
