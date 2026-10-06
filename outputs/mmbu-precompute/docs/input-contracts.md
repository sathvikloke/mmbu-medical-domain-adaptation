# Input, output-diagnostic and geometry contracts

This module provides offline engineering checks. The official final input/output contract remains ambiguous and pending organizer confirmation. A successful local parse is not a correct answer, an official score, or evidence of harness compatibility. No model or judge is loaded or invoked.

## Evidence and unresolved differences

The implementation was checked against two saved sources on 2026-10-03 (America/Chicago), without retrieving gated examples:

- [Challenge brief, saved extraction](../../../work/MMBU_challenge_update.txt), pages 6–7: separate task and context passes; task returns a JSON object with an answer and rationale; neither pass uses the other pass's output or state. The brief does not establish exact task-answer key names. Its context example uses `predicted_metadata` and `perception_rationale`, with precisely the requested metadata keys.
- [Public dataset card, saved visible text](../../../work/audit-2026-10-03/mmbu-public-card-visible.txt), corresponding to [mmbu/mmbu-public](https://huggingface.co/datasets/mmbu/mmbu-public): model input contains image/question, never options or reference answer. The card shows rationale before a terminal single-line `{"answer": ...}` object, task-specific suffixes, and pixel `[x, y, width, height]` boxes. It describes raw-reply fallback if JSON is missing/invalid; the brief describes no credit for malformed output in the affected pass.

These differences remain open. This package does not select one source as authoritative. In particular, `brief_json` is an explicitly chosen engineering convention: `answer` is required and `rationale` is optional. Those names, strict key policy, answer types and rationale optionality are not claims about the final harness. The local `public_card` profile checks a conservative reading of the visible layout; it does not implement the card's grading fallback. Organizer confirmation is needed for prompts, suffix routing, task schema, invalid-output policy, metadata name mapping, detection matching and pass execution.

## Input boundaries

All functions operate on generic Python mappings and return fresh dictionaries. They neither require nor construct Hugging Face objects, image tensors or model-specific chat messages. They do not open images or establish source permissions; manifest/file checks are separate.

| Function | Returned keys | Boundary |
| --- | --- | --- |
| `build_task_input(record, system_prompt) -> dict` | `system_prompt`, `image_path`, `question` | Only the current image reference and question enter task input. |
| `build_context_input(record, requested_fields, system_prompt) -> dict` | `system_prompt`, `image_path`, `requested_fields` | Reference metadata values, task question, task type, reference answer, options, and earlier-pass state are never read into the context output. |
| `build_judge_input(record, raw_prediction) -> dict` | `question`, `options`, `reference_answer`, `reference_context`, `raw_prediction` | Adjudication-only container. Never supply it to the evaluated model. |

Both model builders require a nonblank caller-supplied `system_prompt` and a nonblank string `image_path`. Task input also requires a nonblank string `question`. Text is preserved, without trimming or rewriting. There is no default prompt and no automatic task suffix. Record keys such as `system_prompt`, `history`, `messages`, `previous_prediction`, `predicted_metadata`, `options`, `answer` and `context` cannot override or enrich the model-input dictionaries.

Context requests accept a nonempty sequence of distinct internal field names:

```text
modality, submodality, specimen, body_part, stain, medical_domain
```

Unknown names, duplicate names and a string supplied in place of a sequence raise `ValueError`. Caller order is preserved in a fresh list. The underscore spellings are internal; mapping to the brief's spaced labels such as “body part” is not implemented. Fields are supplied explicitly rather than derived from reference metadata. A record containing only `image_path` is sufficient for a context request.

The judge builder requires a question, an `answer` key and string `raw_prediction`; an empty raw prediction is retained. Absent `options` and `context` become an empty list/dictionary. Present `options` must be a list and present `context` a mapping. Option texts and reference values are copied without interpretation. Mutable options, answer and reference context are deep-copied, so later mutation cannot alter the source record. The builder does not validate reference-label truth or perform semantic adjudication.

These helpers enforce field selection, not safe content or runtime isolation. A caller can put inappropriate material into the supplied prompt/question/image; this layer cannot infer such contamination. A future inference adapter must supply a new model request for each pass, clear conversation/KV state as required, and avoid reusing prior outputs. No inference adapter or state-reset verification exists here.

## Diagnostic parser

`parse_task_output(raw: str, profile: str) -> dict` accepts one of two explicitly selected profiles:

| Profile | Local accepted shape |
| --- | --- |
| `brief_json` | The complete response, apart from whitespace, is one JSON object containing required `answer` and optional string `rationale`. |
| `public_card` | Optional preceding rationale text and one terminal single-line JSON object containing only `answer`. JSON-only output is accepted. |

The parser returns:

```json
{
  "profile": "brief_json",
  "raw": "{\"answer\":\"2\"}",
  "ok": true,
  "parsed": {"answer": "2"},
  "diagnostics": []
}
```

`raw` is always the original string. On a local syntax/schema failure, `ok` is `false`, `parsed` is `null`, and `diagnostics` contains a `{code, message}` object. Codes currently include `invalid_json`, `ambiguous_objects`, `not_object`, `unexpected_keys`, `missing_answer`, `invalid_answer`, `invalid_rationale`, `duplicate_key`, and `nonfinite_number`. Unknown profile names and non-string raw input raise `ValueError` as caller errors.

Both profiles reject duplicate keys at any JSON nesting level, nonfinite literals, floating-point overflow such as `1e999`, unknown top-level keys, and absent/null/empty answers. Local answers may be nonblank strings, JSON integers/floats or nonempty lists; top-level boolean/object answers are rejected. Accepted values are not coerced: the integer `2`, string `"2"`, and coordinate list remain their distinct original JSON types. An empty string rationale is syntactically accepted if present.

This is not a per-task answer schema. Lists are retained without box-shape or class-label interpretation. Box length, numeric coordinates, bounds, count integrality, taxonomy, and semantic correctness require separate checks; `ok: true` establishes none of those properties. Context-output parsing is not implemented.

The parser does not remove Markdown fences, add missing braces, choose among several answers, rewrite labels, round coordinates, or retry a model. `brief_json` rejects leading/trailing prose and multiple objects. `public_card` rejects prose after the object, multiline final objects and multiple decoded objects. Its conservative ambiguity check also rejects an otherwise valid JSON object quoted in the rationale, even if the author did not intend it as an answer. Prefix detection is used only to reject ambiguity; it never contributes an extracted answer. The raw-reply fallback described by the public card is not graded or silently emulated. A local parse failure does not assert an official zero score.

## Pixel geometry

`validate_xywh(box, width, height) -> tuple` accepts a four-element sequence `[x, y, box_width, box_height]` in pixel units. Coordinates and image dimensions must be finite Python integers/floats, with booleans rejected. Origin coordinates must be nonnegative; extents and image dimensions must be strictly positive. The box must fit inside the image, including its right and bottom edges. Valid values are returned unchanged as a tuple.

No clamping, normalization conversion, rounding or boundary tolerance is applied. Fractional pixel values are permitted; numeric values alone cannot reveal whether a caller mistakenly supplied normalized coordinates. Image dimensions must correspond to the actual image shown to the model; resize/back-projection logic is not supplied.

`box_iou(a, b) -> float` computes intersection area divided by union area for two valid positive-area pixel boxes. It validates shape/numeric/origin/extent constraints but has no image dimensions and therefore cannot check image bounds. Exact rational intermediates prevent area overflow for large finite inputs. It returns only a geometric value between 0 and 1 and applies no threshold or multi-box matching policy.

The hand-derived boundary fixture uses `(0, 0, 3, 2)` and `(1, 0, 3, 2)`: each area is 6, intersection is 4 and union is 8, giving IoU 0.5. A slight increase in horizontal separation moves below 0.5; a slight decrease moves above. This is an engineering geometry check, not an official detection score.

## Verification and limits

Run from the package root:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p test_contracts.py -v
```

The 31 tests cover input allowlists, context invariance under changes to task/reference/history fields, missing required inputs, duplicated/unknown metadata fields, mutable-reference isolation, exact raw/value preservation, malformed/ambiguous JSON, duplicate keys, nonfinite numbers, unsupported schemas, unsafe coordinates and hand-derived IoU boundaries. The initial run failed 31 tests because the module was absent; the post-implementation run passed all 31. Both full outputs, Python version and process exit codes are retained in [contracts-test-log.txt](../evidence/contracts-test-log.txt). The recorded interpreter is Python 3.14.7; the module uses only standard-library features available in Python 3.11+, but that run is not a separate Python 3.11 execution.

Native processor rendering is now documented in `processor-compatibility.md`, and explicit image presentation in `supervision-and-presentation.md`. Remaining work includes official schema/prompt confirmation, independent inference execution, official context-output diagnostics, a calibrated judge and official scoring behavior. This module does not establish GPU readiness, model quality, official-protocol equivalence or completion of the model/export gate.
