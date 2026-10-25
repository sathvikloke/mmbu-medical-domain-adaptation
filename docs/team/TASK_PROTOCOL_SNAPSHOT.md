# MMBU task-protocol snapshot

**Observed:** October 17, 2026; metadata-drift recheck October 23, 2026, America/Chicago
**Source:** rendered public card at `https://huggingface.co/datasets/mmbu/mmbu-public`  
**Visible README revision:** `b2faa99129cc5635d0de18cea5abd2ad1189c325`  
**Current repository head:** `d11326436d37a9a560549156bf205ef1b120aa36` (API observation October 23)
**Metadata drift observed:** `metadata.jsonl` and `metadata.tsv` first displayed later commit
`3c09f48d7972bc570d97e9527e24001621b2de5e`; both now display `d11326436d37a9a560549156bf205ef1b120aa36`
**Read-only drift recheck:** October 17, 2026 23:01 CDT; the authenticated Files and versions page still showed
91 commits, README at `b2faa991...`, both metadata files at `3c09f48d...`, 3,103 rows, and no later visible file
revision. No examples or answers from the viewer were used for model, data, prompt, or recipe decisions.  
**Scope:** task pass and judge only; gated examples were not opened or downloaded

**October 21 metadata-only drift:** the Files and versions listing attributes the current metadata files to commit
`d1132643...`. Its commit message says 904 open-row judge label sets gained reviewed closed-VQA options that had been
missing, while rows already covering those options were unchanged. The listing still attributes `README.md` to
`b2faa991...`; the rendered prompt and judge transcription below therefore remains the current visible card contract.
This observation records organizer-published file metadata only. No affected row, option, answer, image, output, or
frequency was opened or used.

This is a manual transcription of the rendered card, not a downloaded raw-file byte snapshot or executable official
harness. The visible README revision identifies the displayed card file; the later metadata commits prove that the
dataset rows changed after the project's older `d09ff622...` pin. The October 21 change alters judge candidate sets for
904 rows, so scores from earlier metadata revisions are not directly comparable even when model outputs are unchanged.
Do not transfer observations from the changed public rows into model, recipe, prompt, or hyperparameter selection.
Context-prompt bytes, evaluator runtime, dependencies, and submission loader remain unresolved.

## Input boundary and routing

Send the image with the row `question`. Do not send `options` or `answer`; `options` is judge-only. Append exactly one
task suffix after a blank line:

| Route on `task` | Suffix |
|---|---|
| starts with `object detection` | object-detection suffix |
| contains `from segmentation` | multi-label-classification suffix |
| contains `from detection` | single-label-classification suffix |
| starts with `counting`, or any other classification task | single-answer-classification suffix |

`from detection` and `from segmentation` images already contain the region overlay. Only `object detection` asks the
model for coordinates.

## System message

```text
You are a medical vision-language assistant evaluating biomedical images.
Analyze the image and question carefully and provide a concise rationale.
After the rationale, put your final committed answer in one JSON object on
its own line: {"answer": ...}. Put only that object after the rationale—no
reasoning, explanation, or surrounding text inside or after it. Follow the
answer-format instructions in the user message.
```

The user message is `{question}`, a blank line, then the routed suffix.

## Task suffixes

Single-answer classification, including ordinary classification, `classification | ...`, `counting | ...`, and
fine-grained classification from detection:

```text
Output format: After your rationale, output only the concise class label
as JSON, for example {"answer": "glioblastoma"}. Do not
include a letter, rationale, or additional explanation in the JSON.
```

For counting, the `answer` value contains only the integer; the card example serializes it as a string.

Fine-grained classification from segmentation:

```text
Output format: After your rationale, output the applicable class label or
labels as JSON. If multiple labels apply, separate them with a
comma and a space, for example {"answer": "effusion, cardiomegaly"}. Do
not include rationale or additional explanation in the JSON.
```

Object detection:

```text
Output format: After your rationale, output the bounding box or boxes as JSON
using pixel coordinates from the image shown and the format
[x, y, width, height]. Do not use normalized 0–1 coordinates. For one box,
use {"answer": [x, y, width, height]}. For multiple boxes, use
{"answer": [[x1, y1, width1, height1], [x2, y2, width2, height2]]}.
Do not include rationale or additional text in the JSON.
```

Here `x, y` is the top-left pixel coordinate in the image as shown.

## Parsing and scoring

The card says to parse the committed `answer` field and, at this captured revision, says that missing or invalid JSON
falls back to the raw reply. The October 6 Discord answer explicitly states that official scoring will not fall back to
the raw reply, and the October 14 direct organizer email independently says malformed JSON is incorrect. These direct
answers control local policy: malformed committed JSON is a failure and is never repaired. Preserve the contradictory
card text as revision-drift evidence rather than implementing it.

The user-supplied October 17 Discord transcript records a further direct organizer answer: when multiple answer fields
appear, the last answer field is scored in both passes, and thinking blocks are removed before extraction. The reply's
wording does not define code-fence handling, extraction grammar, malformed thinking tags, or whether “answer field” is
shorthand for Pass 2's differently named committed field. The local serializer still emits exactly one terminal JSON
object, so it does not rely on those unresolved recovery paths.

For object detection, parse pixel `xywh` boxes, compare every predicted box with every ground-truth box, retain maximum
IoU, and mark the row correct at maximum IoU at least 0.5. The direct organizer email separately confirms that an
“any one” prompt should emit one box and match any one ground-truth box.

All other task rows use judge profile `open_per_dataset_v3`. Construct `label_set` from that row's `options`, stripping
the leading option prefix and placing one label per line. The rendered card names `claude-sonnet-5` as the official
judge. The judge requires both grounding to exactly one specific label-set concept and equivalence at the same
specificity; vague, off-taxonomy, hedged, broader, narrower, or related-but-distinct answers fail. A successful judge
line ends with `[RESULT] 1`.

This creates a second unresolved contradiction: the segmentation suffix explicitly permits multiple comma-separated
labels, while Judge Gate 1 requires the model answer to assert one specific label-set concept and rejects hedging across
multiple labels. Do not invent splitting, set matching, repeated judge calls, or partial credit. Obtain organizer
precedence or an executable harness before official-equivalent multi-label scoring.

## Change-control consequences

1. The older `d09ff622...` dataset pin is historical and cannot be called current.
2. A task-protocol proxy may use this revision-recorded manual transcription, but not protocol-equivalent language until the raw bytes,
   model chat rendering, generation configuration, judge access, and runtime are independently receipted.
3. Context scoring remains provisional because the organizer said the context prompt was unfinished, repeated on
   October 15 that it would be shared later, and the current task card does not supply it.
4. Metadata fixes after the old pin invalidate row-level duplicate counts or label audits as statements about the
   current public release. Historical findings stay historical; do not reopen the public rows for development.
5. The October 21 judge-label-set expansion invalidates score comparisons across the old and current metadata unless
   the exact metadata revision is reported. It does not authorize using public `options` as a training vocabulary.
6. Before any official local report, re-check the card and metadata revisions and fail closed on drift.

## Executable-authority status

This snapshot is documentation only. It does not activate or amend an executable prompt/schema contract.
The Phase 1 implementation currently constructs only a `synthetic` contract, binds its prompts, schemas, parser,
validator, judge policy, geometry threshold, and inference settings by digest, and unconditionally refuses to label
any Phase 1 contract official-harness equivalent. The hash-bound October 14 organizer-answer receipt remains unchanged:
it is valid evidence of the direct answer it records, not permission to silently resolve the two contradictions above.

Promoting this snapshot into an executable non-synthetic contract therefore requires a reviewed successor contract
with raw source bytes and spans, explicit precedence decisions for malformed JSON and multi-label judging, a complete
context protocol, exact generation/runtime settings, and a new digest chain. Until then, experiments may use a clearly
named protocol proxy, but official-equivalent claims must fail closed.
