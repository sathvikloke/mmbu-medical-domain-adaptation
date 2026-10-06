# Explicit provisional target serialization

`mmbu_prep.serialization` turns caller-supplied reference values into deterministic strings. The caller must choose a profile. These are local engineering conventions while the official task/context contracts remain unresolved; serialization does not approve an annotation, source, split or training use.

The helper supplies no labels, rationales, unknown values or dimensions. Keep its output as a reference or assistant training target, separate from `build_task_input` and `build_context_input`. Those input builders select their existing allowlisted fields; they do not consume serialized reference fields. Tokenization, the model's native chat template, prefix verification, assistant-only masks and permission checks remain separate steps.

## Task targets

```python
from mmbu_prep.serialization import serialize_task_target

serialize_task_target("counting", "2", profile="brief_json")
# '{"answer":"2"}' — the supplied string stays a string

serialize_task_target(
    "counting", 2, profile="public_card",
    rationale="Two synthetic circles are visible.",
)
# 'Two synthetic circles are visible.\n{"answer":2}'

serialize_task_target(
    "detection", [[1, 2.5, 3, 4.0]], profile="brief_json",
    image_width=10, image_height=12,
)
# '{"answer":[[1,2.5,3,4.0]]}'
```

Signature:

```python
serialize_task_target(
    task, answer, *, profile,
    rationale=None, image_width=None, image_height=None,
) -> str
```

| Task | Accepted explicit answer |
| --- | --- |
| `global_classification`, `box_classification` | A nonblank string. Box classification remains a label, not a generated box. |
| `counting` | A nonnegative Python `int` excluding booleans, or an ASCII decimal string matching `0` or `[1-9][0-9]*`. No signs, leading zeros, whitespace, decimal points, exponents or Unicode digits. |
| `mask_classification` | A nonblank string, or a nonempty JSON-style Python list of distinct nonblank strings. Distinctness is exact; no case folding, trimming, semantic merging, sorting or comma joining. |
| `detection` | One four-number JSON-style list `[x,y,width,height]`, or a nonempty list of such lists. Every box passes `validate_xywh` with explicitly supplied positive finite image dimensions. |

Scalar values, scalar versus list answers, one-box versus one-element box-list answers, element order and integer/float/string types remain intact. Arrays must be lists; tuples and sets are not silently coerced. Duplicate detection boxes remain present because no matching or deduplication policy is inferred. Coordinates stay in the caller's stated pixel frame with no scaling, rounding or clipping. Positive box extents and in-image bounds are required. Fractional coordinates are allowed, but their units cannot be established from numbers alone. Dimensions are checked only for detection.

An empty detection list is rejected. The helper does not invent an empty-target/negative-example representation while that official policy is unknown. Passing this check does not establish that a box encloses the intended object or that a count/label is correct.

`profile` is a required keyword argument with two choices:

- `brief_json`: one JSON object with `answer`; adds `rationale` only when the caller supplies a string.
- `public_card`: an optional exact caller-supplied rationale followed by a newline, then a terminal single-line JSON object containing only `answer`.

`None` means no rationale. An explicitly supplied empty string stays empty; the helper does not manufacture explanatory prose. Any nonstring rationale is rejected. For `public_card`, a rationale containing another parseable JSON object is rejected because the existing parser treats it as ambiguous. Even a prose mention of `{}` is rejected under that conservative rule. `brief_json` can retain that same text safely inside its rationale string.

Every task result is checked with `parse_task_output` under the chosen profile before return. Ambiguity is an error, not a cue to rewrite or remove text. JSON uses compact separators and ASCII escapes, including escapes for Unicode line separators, so labels round-trip without accidentally splitting the terminal object into multiple lines. The decoded strings retain their original Unicode characters and whitespace.

## Local context targets

```python
from mmbu_prep.serialization import serialize_context_target

serialize_context_target(
    ["modality", "body_part"],
    {"body_part": "explicit reviewed label", "modality": "synthetic"},
    profile="local_internal_underscore_json",
)
# '{"context":{"modality":"synthetic","body_part":"explicit reviewed label"}}'
```

Signature:

```python
serialize_context_target(
    requested_fields, values, *, profile, rationale=None,
) -> str
```

The required profile is **`local_internal_underscore_json`**. Its local wrapper has `context` and, only if explicitly supplied, `rationale`. It is not passed to `parse_task_output`, which is a task-answer parser.

The caller provides a nonempty sequence of distinct supported field names: `modality`, `submodality`, `specimen`, `body_part`, `stain`, `medical_domain`. `values` must be a mapping with exactly the requested keys, no extras or omissions, and a nonblank string for every value. The output retains requested-field order and exact strings. Spaced aliases such as `body part` are rejected rather than guessed.

This wrapper, field spelling and string-value restriction are a local schema. They do not resolve the official context prompt, field masks, key spacing, optional annotations, unknown/absent-value meaning, missing-field scoring or zero-field policy. A caller-provided word such as `unknown` is merely preserved text; the helper never inserts it. Any rationale is explicit text, without generated clinical reasoning.

## Verification

Run from the package directory with Python 3.11 or newer:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p test_serialization.py -v
```

The 20 synthetic tests exercise both output profiles, type/cardinality preservation, invalid targets and dimensions, ambiguous JSON-bearing rationale text, exact context field matching and reference/input separation. The initial missing-module failure and passing run are retained in `evidence/serialization-red.txt` and `evidence/serialization-green.txt`. `evidence/serialization-examples.json` contains unmistakably synthetic sample outputs; `evidence/serialization-verification.json` records source hashes and executed checks. No model, GPU, network or external data is needed.
