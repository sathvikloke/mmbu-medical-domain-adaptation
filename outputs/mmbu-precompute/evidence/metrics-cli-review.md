# Independent metrics and CLI review

Review date: 2026-10-03 America/Chicago (2026-10-04 UTC).

Reviewer: the contracts worker, reviewing root-authored `metrics.py`, `__main__.py`, their tests, `README.md`, `docs/statistics.md`, and Task 4 of the implementation plan. The reviewer did not implement those modules. This is a scoped software cross-review, not an independent audit of the reviewer's own contracts module or a scientific validation of MMBU/model results. No implementation files were changed. Temporary reproduction fixtures were removed automatically; this report is the only persistent review artifact written.

**Verdict: changes requested for two reproducible CLI boundary defects.** The examined score formula, paired group resampling, source-mass preservation and stated scientific limits were supported by independent probes. One lower-priority numeric API inconsistency is recorded separately. Existing passing tests did not cover the two defects.

## Findings

### MCLI-001 — P2: `split` incorrectly requires training permission for a development-only assignment

Location in reviewed snapshot: `src/mmbu_prep/__main__.py:106`.

`split` calls `validate_manifest(..., purpose="train")` before considering requested ratios. An approved external source can legitimately permit only `dev`/`confirmation`; assigning its records entirely to `dev` does not require training permission. The CLI rejects that operation, even though the library's `assign_splits` correctly accepts it. This prevents an authorized held-out-data workflow and makes CLI behavior differ from its underlying permission contract. It does not leak unauthorized data into training.

Reproduction used a temporary engineering permission fixture, not an actual approved biomedical source:

```python
registry = {"schema_version": 1, "sources": [{
    "source_id": "review-only", "source_version": "v1", "source_family": "review-only",
    "source_role": "external", "status": "approved", "allowed_purposes": ["dev", "confirmation"],
    "evidence": ["temporary engineering permission-routing test, not real authorization"],
    "reviewed_by": "test-fixture", "reviewed_at": "2026-10-03"
}]}
record = {
    "schema_version": 1, "record_id": "review-only", "source_id": "review-only",
    "source_version": "v1", "source_family": "review-only", "split": "dev",
    "image_path": "review-only.png", "image_sha256": "0" * 64,
    "parent_image_sha256": None, "group_id": "review-only", "task": "global_classification",
    "question": "Engineering fixture only", "answer": "fixture", "context": {"modality": "fixture"},
    "annotation_origin": "engineering test", "conversion_version": "v1",
    "review_status": "approved", "synthetic": False
}
```

Write that registry as JSON and record as JSONL in a temporary directory, then run:

```sh
PYTHONPATH=src python3 -m mmbu_prep split RECORDS.jsonl --registry REGISTRY.json \
  --ratios '{"dev":1}' --seed 1 --output NEW_SPLIT.jsonl
```

Observed: exit **2**, `ok: false`, error code `purpose_not_permitted`, no output file. Independent library call `assign_splits([record], registry=registry, seed=1, ratios={"dev":1})` returned a record with `split == "dev"`. Adding training permission to the same fixture made the unchanged CLI command succeed.

Suggested correction: derive the file-validation purpose from an actual positive requested target after validating ratios, retaining `assign_splits` checks for every target permission. Add a CLI regression for a source with only `dev` permission and `{"dev":1}`, plus a rejection case when a requested target lacks permission.

### MCLI-002 — P2: the common JSON loader admits floating-point overflow as infinity

Location in reviewed snapshot: `src/mmbu_prep/__main__.py:24–25`.

`parse_constant` rejects literal `NaN`/`Infinity`, but the default float decoder turns a JSON number such as `1e999` into infinity. This violates the advertised strict loading behavior. Downstream grade checks reject infinity when it occupies a used grade field, and manifest validation checks whole records; however, an extra field in a score row is ignored. Thus malformed numeric content can receive a successful CLI result depending on field placement.

Minimal library reproduction:

```python
from mmbu_prep.__main__ import _decode
assert str(_decode('{"unused":1e999}')["unused"]) == "inf"
```

CLI reproduction: score a one-line file containing:

```json
{"record_id":"one","source_id":"s","group_id":"one","task":"global_classification","adapted_correct":1,"base_correct":0,"context_correct":{"modality":1},"unused":1e999}
```

Observed: exit **0**, empty stderr, `S: 1.0`. The diagnostic boundary accepted infinity internally; it did not corrupt the supplied valid grades. This is a validation-contract defect, not evidence that regular scores are numerically wrong.

Suggested correction: use a finite-checking `parse_float` callback in the common decoder so every loaded JSON number is validated, including unused configuration/record fields. Add JSON and JSONL regressions covering `1e999`, `-1e999`, and nested overflow values in otherwise valid records; ensure rejection happens before any split output is created.

### MCLI-003 — P3: extreme numeric values have inconsistent library failure behavior

Locations in reviewed snapshot: `src/mmbu_prep/metrics.py:17`, `54–59`, `131`.

The score library's ordinary invalid inputs raise `ValueError`, but sufficiently large integers cause `math.isfinite` to raise `OverflowError`. Also, finite positive weights whose sum overflows cause `math.fsum` to raise before the intended explicit check. Conversely, extreme weight ratios can silently normalize a positive weight to zero in `score_rows`, while the bootstrap rejects those normalized weights on its second validation.

Using this valid row helper:

```python
def row(i, a=1, c=1):
    return {"record_id": str(i), "source_id": "s", "group_id": str(i),
            "task": "global_classification", "adapted_correct": a, "base_correct": 0,
            "context_correct": {"modality": c}}
```

Observed independent calls:

| Call | Observed result |
| --- | --- |
| `score_rows([row(1, a=10**400)])` | `OverflowError: int too large to convert to float` |
| `score_rows([row(1), row(2)], weights=[1e308, 1e308])` | `OverflowError: intermediate overflow in fsum` |
| `score_rows([row(1), row(2, a=0, c=0)], weights=[1e-300, 1e300])` | Success, `T=C=S=0.0`, first positive weight rounded to zero |
| Same two rows/weights passed to `paired_cluster_bootstrap(..., iterations=5)` | `ValueError: Weights must be positive finite numbers` |

Importance is limited: the CLI already catches `OverflowError`, natural/balanced CLI weights do not approach these magnitudes, and a weight ratio of `1e-600` has no practically resolvable contribution to a unit-scale score. The finding concerns reusable-library contracts and consistent failure semantics, not an ordinary benchmark-result error. Reasonable correction: reject nonbinary grades before any float conversion; scale finite weights before summation; detect normalization underflow or document/reject unsupported ranges consistently. Add targeted regressions rather than a blanket broad test expansion.

## Supported behavior from independent checks

- **Signed arithmetic:** sixteen rows with adapted accuracy `6/16`, base accuracy `1`, and context score `1` returned `T=0.375`, `T_base=1`, `C=1`, `task_gain=-0.625`, and `S=-0.3125`. This independently exercises the negative range beyond the existing `-0.2` test. The product is computed after aggregation.
- **Fixed source mass:** source A had three always-correct rows in groups of sizes one and two; source B had two always-incorrect rows in two separate groups. With natural weighting, expected `T=C=3/5`, `T_base=0`, hence `S=0.36` on every draw. Two hundred draws at seed 11 produced interval `[0.3600000000000001, 0.3600000000000001]`, the expected floating-point representation. Variable group size did not alter source mass.
- **Pairing:** eight rows with identical base/adapted grades in four groups and variable context yielded `[0.0, 0.0]` across 200 bootstrap draws at seed 5. The shared draws preserve exact zero gain.
- **Cluster/unit interpretation:** code resamples complete groups uniformly within each source and retains all rows selected with a group. Base/adapted/context share each sampled index. Task weights can change within a sampled source; documentation explicitly states this limitation. Source identifiers and group correctness remain upstream assumptions.
- **Weighting:** the examined balanced proxy allocates four task-group masses, equal source mass within task, then equal row mass within source/task. Counting belongs to the global group. Partial task coverage is rejected. No source-composition inference or semantic grading is performed.
- **Insufficient groups:** a source with fewer than two groups withholds the interval. Few groups/draws get explicit warnings. Confidence intervals are conditional and percentile-based; the docs do not present them as hidden-source uncertainty or candidate-superiority tests.
- **Output protection:** for a permitted temporary split fixture, first creation exited 0. Repeating the command for the same path exited 2 with a file-exists error, and SHA-256 of the output was unchanged. Invalid permission validation produced no output. Other reviewed CLI paths are read-only apart from standard output. No evidence of downloads, model execution or training was found. Exclusive creation does not promise atomic completion after an OS interruption/disk failure; the docs do not claim that guarantee.
- **Readiness limits:** README, status and statistics documentation consistently distinguish pregraded arithmetic from an official harness/semantic judge. They retain source review, authoritative protocol, GPU access, model loading, calibration and export as outstanding. Optional image hashing without `--image-root` is documented; its absence is not treated here as a defect.

## Executed existing tests

Working directory: package root. Interpreter: Python 3.14.7. Each command ran independently and exited 0:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_metrics.py' -v
Ran 14 tests in 0.004s — OK

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_cli.py' -v
Ran 7 tests in 0.389s — OK
```

The review did not rerun or rely on the reported complete integrated suite. Counterexample script exited 0; its deliberate failing API/CLI calls were captured and classified above. No network, GPU, real source review, official evaluator, or learned model was used.

## Reviewed snapshot receipts

SHA-256 captured after the independent probes and before this report. Findings refer to these snapshots; fixes require a new run/re-review before these findings can be marked resolved.

```text
523affe16345c9cc9e1fad13d1acd86c9cc6a3eb000f7e27e23908a86f45387c  src/mmbu_prep/metrics.py
c22c5266de06bbb310cfa80963cdf913008fe1f55f1b8163631fda678a421802  src/mmbu_prep/__main__.py
4f90da7e0f543054314b2f89cc31e3a9638545766f249be3eb9c5b8381cc78b2  tests/test_metrics.py
f7388bb22dfbaaebf45387babbbc411c70873060049578e7d245c24a49273474  tests/test_cli.py
5e04e9e179bccb2cfa3e4c84e8ce514c6c965e9d21c356d1113c8f9019e944a7  README.md
87fde332e3086da7301a3883f97c3dbeaa7f3019dc7c2ccb890ce4e0458820ca  docs/statistics.md
```

## Scoped repair closure

The original findings and snapshot receipts above are retained as historical evidence. The implementing root agent subsequently changed the common decoder, split validation routing, grade validation and weight normalization. This reviewer inspected those changes and reran the specific counterexamples independently. This section supersedes the original verdict only for the identified repairs; it is not a new broad audit or an official-protocol/readiness approval.

| Finding | Closure state | Independent evidence |
| --- | --- | --- |
| MCLI-001 | **Closed** | Temporary external fixture with only `dev` permission and `{"dev":1}` now exits 0 and writes a dev record. Requesting `{"confirmation":1}` against the same registry exits 2 and creates no output. |
| MCLI-002 | **Closed** | Both direct decoding and CLI JSON/JSONL reads reject `1e999`, including a nested field and a negative overflow number. CLI exits 2 with an actionable error. A split ratio containing `1e999` is rejected before output creation. |
| MCLI-003 | **Grade/weight cases closed; confidence edge case remains P3** | Huge invalid grade and huge weight now raise `ValueError`. Weights `[1e308,1e308]` yield `T=0.5`, `C=1`, `S=0.30000000000000004`. Underflowing positive weights raise `ValueError` consistently in score and bootstrap. Passing `confidence=10**400` still raises `OverflowError`, because its finite check still precedes the range check. |

The remaining confidence case is the same low-priority library error-contract issue, not a failure to reject an invalid confidence level or an incorrect score. The CLI catches `OverflowError`. A minimal correction is to check `0 < confidence < 1` before calling `isfinite`, with the existing type checks first, and add the large integer to parameter-regression cases.

Independent closure runs on the repaired modules:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_metrics.py' -v
Ran 16 tests in 0.004s — OK, exit 0

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_cli.py' -v
Ran 8 tests in 0.448s — OK, exit 0
```

The root's `review-fixes-red.txt` was inspected and contains 105 tests with two failures (dev-only CLI and overflow JSON acceptance) and two errors (huge grade and large weight total). Its `review-fixes-green.txt` records 105 passing tests after repair. Those full-suite logs were produced by the implementing root agent; the independent scope runs and counterexample results above are the reviewer's own evidence.

Repaired snapshot receipts for this closure pass:

```text
8ead7d7960304d9704d3d827028fb36061d607ce5dd6a8223a780a91f64cb920  src/mmbu_prep/metrics.py
074a00acb99f1a37432a557b8eacc9879c1767bc5a67b8a1f56631d5ce3c3c09  src/mmbu_prep/__main__.py
72b70094d593a97d7943526d1706a1c6c5eeb08f952c3363395bdaf466f5a27f  tests/test_metrics.py
77a2d19643bc4909a4b31115337672d25ffcdf9d69bd3a12a2ae4c455a99534b  tests/test_cli.py
```

## Final focused closure of the confidence edge case

**Current scoped disposition: MCLI-001, MCLI-002 and MCLI-003 are closed.** This supersedes the residual P3 status in the preceding closure section; the earlier findings remain historical evidence.

The implementing root agent removed the float-converting `isfinite(confidence)` check at `metrics.py:138`. The existing type/Boolean guards and `0 < confidence < 1` condition reject invalid values directly, including nonfinite floats and arbitrarily large integers. The parameter regression now includes `{"confidence": 10 ** 400}`.

The reviewer inspected that exact change and independently reran the original two-valid-row call:

```python
paired_cluster_bootstrap(rows, confidence=10**400)
```

Observed: `ValueError: confidence must be between zero and one`; the verification script exited 0. This closes the remaining MCLI-003 reproduction. No additional implementation changes or broad audit were performed in this closure pass.

The root-authored `confidence-red.txt` was inspected and records the new regression raising the original `OverflowError` (16 tests, one error). The corresponding `confidence-green.txt` records 16 passing metrics tests after the fix. These are implementation evidence; the direct counterexample above was rerun independently by the reviewer.

Final metrics snapshot receipts for this focused closure:

```text
66a620a00606f806ba0c1b334b19c35e2f76807c7000d0079c015fa56742bfd6  src/mmbu_prep/metrics.py
ea45d99a952c2a2b2c74e3161aa6c46c1ab65cb260d4e33aa9d0a5a47ab668fb  tests/test_metrics.py
```

Closure is limited to this report's identified defects and repaired snapshots. It does not establish official-harness equivalence, biomedical data approval, semantic-judge calibration, GPU readiness, model quality or completion of all precompute work.
