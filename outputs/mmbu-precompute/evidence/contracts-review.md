# Independent contracts review

Reviewed October 3, 2026 (America/Chicago). Verdict: **no actionable defect found within the implemented engineering scope**. No official-harness, semantic-grading or model-runtime claim is supported by this review.

Reviewer: `/root/model_data_audit`, a separate agent from the contracts author. This reviewer authored source/protocol preparation files, but did not author or modify the reviewed contract code/tests. Only this review record was written. The root's reported 92-test integration result was not treated as a substitute for inspection.

## Materials and checks

Read `src/mmbu_prep/contracts.py`, all of `tests/test_contracts.py`, `docs/input-contracts.md`, root `README.md`, `examples/README.md`, and the shipped manifest/toy-grade records. Compared the design with the previously inspected brief's independent-pass requirement and visible-card ambiguity. No own source-register files were re-reviewed.

Executed from the package directory:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p test_contracts.py -v
```

Observed **31 tests passed, exit code 0**. Then ran a separate standard-library Python heredoc against the live module, exit code **0**, with these assertions:

| Check | Actual evidence |
|---|---|
| Guarded record access | Two Mapping fixtures raised on any hidden/reference/history field access. Task read only image and question; context read only image. |
| Shipped input fixtures | All five manifest rows produced exact task/context allowlists; changing answer, choices, reference metadata and previous state left context unchanged. |
| Parser counterexamples | Eight additional cases below behaved as documented and preserved the exact raw string. |
| Independent geometry oracle | Enumerated all 100 positive integer xywh boxes inside a 4×4 pixel grid. For every ordered pair, compared IoU with `len(pixel_set_a & pixel_set_b) / len(pixel_set_a | pixel_set_b)`. All **10,000 pairs** matched exactly. This discrete raster oracle does not reuse the implementation's rectangle-intersection formula. |
| Extreme valid geometry | Identity IoU was 1.0 for integer dimensions `10**100` and floating dimensions `1e-300`, avoiding ordinary area overflow/underflow. |

Additional `public_card` parser cases:

| Raw response characteristic | Observed |
|---|---|
| Earlier object with duplicate answer keys, followed by a final answer | Rejected as ambiguous. |
| Earlier object containing NaN, followed by a final answer | Rejected as ambiguous. |
| Earlier object nested in a prose-prefixed list | Rejected as ambiguous. |
| Prose after final JSON on the same line | Rejected. |
| Literal brace text inside the final answer string | Accepted, value preserved. |
| Leading tabs, CRLF and Unicode answer text | Accepted, original raw text preserved. |
| Earlier malformed non-JSON fragment followed by final JSON | Accepted as prose plus final object, consistent with detecting *decoded objects*, not every brace. |
| Answer list containing null, boolean and object elements | Accepted as a nonempty list, consistent with the explicit absence of a per-task answer schema. It is not a geometry/semantic pass. |

## Findings and scope

**No repair request retained.** The builders use fresh allowlisted outputs (contracts lines 32–90), preserve caller strings, copy mutable requested fields, and deep-copy judge-only references. Context construction does not consult the task/question/reference values. Documentation correctly makes caller prompt content and actual conversation/KV-state reset the future adapter's responsibility; neither was falsely claimed as verified.

The parser (lines 119–187) keeps raw text, rejects decoded-object ambiguity, duplicate keys and nonfinite values, and does not silently repair or grade outputs. Its intentionally permissive list content, optional engineering rationale and conservative rejection of quoted JSON objects are disclosed. Those choices are not defects against the stated local diagnostic contract. Do not later interpret `ok=true` as task validity or final-harness compatibility.

Geometry (lines 190–241) rejects booleans, nonfinite numbers, invalid origins/extents and out-of-image coordinates without clamping. Exact rational intermediates support the advertised numeric range. No threshold or multi-box policy is silently applied. Fractional-coordinate units and the image's actual resize frame cannot be inferred by these functions; the documentation acknowledges this.

Root/example descriptions explicitly identify five procedural shape fixtures and twenty hand-constructed grade rows. The examples state that their task tags exercise software categories, are not complete organizer overlays, and cannot count toward the future biomedical cohort. I found no synthetic biomedical-performance claim in the reviewed labels.

Limits: no inference adapter, image rendering/resize pipeline, context-output parser, biomedical label validity, official schema selection or semantic judge was tested. Passing this scope does not complete E00. Source permission checks, statistics and split assignment belong to other reviews.

## Reviewed snapshot hashes

```text
7c2f4a417f946e41cc2c97705b4b7edf07ae4d932e0781f60a05fddc36689db3  src/mmbu_prep/contracts.py
dc400a460b6a02cf8aa484c6a99ce435474920944f44c43fadf9f0fc3fa05803  tests/test_contracts.py
2cd0b7aca6ddc5bbc6f0a006d3072a06dc39dc2c90660f1ed47920f5e2eb9775  docs/input-contracts.md
5e04e9e179bccb2cfa3e4c84e8ce514c6c965e9d21c356d1113c8f9019e944a7  README.md
91a8fd38124ea05793d86feef83a4bc71a013bf15be04ab310af282582f0fbb0  examples/README.md
478ff45524cde596a4715455bff25f921bfecf227b52b9d71f49360749dd2f28  examples/engineering-manifest.jsonl
37a4805231a2496acbaf0084692c18e13b7ff62ce8060a2373fbd61c826beab0  examples/pregraded-toy.jsonl
```
