# Pending ROCO input encoding on CPU

The 24 prepared RGB PNGs were encoded with each of the three pinned native processors under two image-size policies. All 144 image/model/policy cases passed the repeated-encoding, finite-value, CPU-device, image-grid/token-count, and excluded-input-field checks. Each case was encoded twice, for 288 processor calls per full run. No model was loaded or executed. No source status or allowed purpose changed.

The current machine-readable result is `evidence/source-processor-final-v2.json`; `source-processor-probe.json` and `source-processor-final.json` retain earlier runs. The v2 run follows repairs to JSON exponent-overflow rejection and bounded file reads. Its complete model observations equal the earlier final run. `evidence/source-processor-tests-log.txt` records ten passing focused safeguard tests. `evidence/source-processor-verification.json` records artifact hashes and the final run/replay checks.

## Inputs and isolation

The input is `work/roco-quarantine/prepared/pending-manifest.jsonl`, SHA-256 `fa6e591fea3b1cec61c87e0eef87959028c88afb4f6904c144c5bee666fed327`. The script requires exactly 24 records by default, each with `review_status: pending` and `allowed_purposes: []`. The existing image inspector checks actual file hashes, declared dimensions, integrity and complete decoding before processor loading. This probe accepts only RGB, single-frame PNGs without an orientation transform. Reads are capped at 16 MiB plus one detection byte; decoded inputs are capped at four million pixels. The manifest, registry and image bytes are checked again after encoding.

The existing contact sheet was visually inspected for layout and decode sanity. It is not encoded; all processor calls use the individually hash-checked prepared PNGs. No biomedical label correctness was assessed. Three source images (`046920`, `011831`, `055358`) retain ICC-profile notices; no color-management transform was applied. The inspection's general limit notice also remains in the report. Native processor loading and encoding emitted no captured Python warnings or Transformers warnings in this run.

`build_task_input` selects the prepared image path, question and caller-supplied system prompt. The system prompt is the provisional synthetic engineering fixture:

> Engineering preprocessing probe. This request measures input encoding only. Use only this image and question.

The native template uses `add_generation_prompt=True`, `tokenize=False`, and default template kwargs `{}`; encoding uses `padding=False`, `truncation=False`. Every record's render is compared with a version whose answer, options, context, caption, raw caption, article ID, source IDs, record ID, history, messages and previous prediction have been replaced with a sentinel. All renders remain identical. Reference answers and captions are never encoded, and no assistant answer is appended. Qwen3.5's native default generation marker includes its thinking opener. This task measures only that input; it does not establish an assistant-target loss boundary. See `docs/processor-compatibility.md` for the separate default/non-thinking boundary checks.

## Native revisions and observations

The registry snapshot is `evidence/source-processor-registry.json`. Before loading, `processor_probe.artifacts(..., download=False)` verifies the exact revision, downloaded-file hashes and closed local artifact set. `AutoProcessor` uses `local_files_only=True`, `trust_remote_code=False`; Python DNS/socket-connect/urllib network entry points are denied, and the Hugging Face and Transformers offline flags are set. The report records zero attempted network calls. This is an in-process guard, not an operating-system network sandbox.

| Processor | Exact revision |
| --- | --- |
| Qwen/Qwen2.5-VL-7B-Instruct | `cc594898137f460bfe9f0759e9844b3ce807cfb5` |
| Qwen/Qwen3.5-9B | `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Qwen/Qwen3-VL-8B-Instruct | `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` |

Tested runtime: Python 3.12.14, Transformers 5.18.0, torch 2.14.1, Pillow 12.3.0, one CPU thread. The existing isolated runtime and processor artifact cache are used; this probe installs or downloads nothing. The complete prior environment freeze is `evidence/processor-requirements.txt`.

`native_default` preserves each cached processor's size configuration. The optional common policy passes `size={"shortest_edge": 65536, "longest_edge": 262144}`. These processor fields represent image pixel-area bounds in this runtime, not literal edge lengths. The same area interval is diagnostic only; patch rounding and aspect ratio still affect effective dimensions. It is not a chosen production resolution policy.

Every row below includes all 24 images. Input tokens include visual tokens, system/question text, native wrappers and generation markers. The nonvisual count is 43 per image for Qwen2.5 and Qwen3-VL, and 45 for Qwen3.5 under these fixed inputs.

| Processor | Policy | Visual min–max | Visual total | Input min–max | Input p50 | Input p95 | Input total |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen2.5-VL-7B | Native | 77–870 | 9,256 | 120–913 | 412 | 767.95 | 10,288 |
| Qwen2.5-VL-7B | Common bound | 96–324 | 6,422 | 139–367 | 349 | 367 | 7,454 |
| Qwen3.5-9B | Native | 70–650 | 7,051 | 115–695 | 325 | 574 | 8,131 |
| Qwen3.5-9B | Common bound | 70–256 | 4,885 | 115–301 | 279 | 299.55 | 5,965 |
| Qwen3-VL-8B | Native | 70–650 | 7,051 | 113–693 | 323 | 572 | 8,083 |
| Qwen3-VL-8B | Common bound | 70–256 | 4,885 | 113–299 | 277 | 297.55 | 5,917 |

Percentiles use Hyndman–Fan type 7: sort the 24 counts, calculate `(n−1)*p`, and linearly interpolate the adjacent order statistics. The report preserves binary floating-point results without rounding; the table displays two decimal places where needed. Fractional percentiles are interpolation, not fractional tokens in an individual input. Totals count each image once per model/policy, excluding the deterministic replay call. These are sample descriptions, not population confidence intervals.

Per-image evidence contains raw PNG and decoded-representation hashes, original dimensions, `image_grid_thw`, effective resized height/width computed from grid times patch size, visual token count verified against grid product divided by merge-size squared, total input token count, array shapes/dtypes/hashes, finite-value checks and exact repeated-output equality. The comparison observes native resizing; it does not establish preservation of diagnostic detail.

## Reproduction

Run from the project root, using a **new** output filename:

```sh
PYTHONDONTWRITEBYTECODE=1 work/processor-probe/.venv/bin/python \
  outputs/mmbu-precompute/tools/source_processor_probe.py \
  --manifest work/roco-quarantine/prepared/pending-manifest.jsonl \
  --image-root work/roco-quarantine/prepared \
  --registry outputs/mmbu-precompute/evidence/source-processor-registry.json \
  --artifacts work/processor-probe/artifacts \
  --include-common-bound \
  --output /tmp/source-processor-new-report.json

PYTHONDONTWRITEBYTECODE=1 work/processor-probe/.venv/bin/python \
  outputs/mmbu-precompute/evidence/source-processor-tests.py
```

The script exits 0 only when all cases and final integrity checks pass. Missing dependencies, invalid inputs, unavailable snapshots, failed encodes and existing output paths return 2. A partial per-model failure is recorded explicitly; success counts and failure counts accompany any summary. Existing output files are rejected before execution and publication uses exclusive creation. No source image or manifest is rewritten.

Token counts do not establish GPU memory fit, throughput, model quality or a preferred model. No model weights, activations, optimizer, training step, answer grading or evaluation were involved. These pending files remain unavailable for training, evaluation or release until the separate required reviews and approvals are satisfied.
