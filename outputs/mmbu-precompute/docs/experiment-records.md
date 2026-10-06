# Experiment declarations and local freeze receipts

`mmbu_prep.experiments` makes a pre-run provenance declaration mechanically checkable and records a small confirmation lifecycle. It is offline, uses Python's standard library, and never runs a model or reads a result's score to decide what to preserve. No source is approved, no manifest permission is granted, and no official protocol is established by a passing check. Use the separate [manifest and source authorization contract](data-contract.md) for those checks.

The historical `configs/experiment-record.template.json` and `configs/confirmation-freeze.template.json` remain unchanged. Their nulls, unresolved fields and template statuses deliberately fail the new executable declaration schema. They are planning aids, not completed experiment records.

## Declaration schema

`validate_experiment_record(record)` returns a deep copy after checking all required fields, finite JSON values, artifact references, relative paths and hashes. It inserts no defaults, repairs no values, and rejects unknown fields. This function checks a declaration's structure; `verify_experiment_record(record, root)` additionally checks all selected local files against its declared fingerprints.

Every row in this table is required, including `confirmation: null` for a non-confirmation record. Every object listed has exactly the indicated keys.

| Field | Required contents |
| --- | --- |
| `schema_version`, `record_kind` | Integer `1`; string `pre_run_experiment` |
| `experiment_id`, `owner`, `hypothesis` | Explicit nonblank strings |
| `created_at_utc` | ISO-8601 datetime with UTC offset, such as `2026-10-04T10:00:00Z` |
| `purpose` | `engineering`, `development`, or `confirmation` |
| `baseline`, `candidate` | Each: `model_id`, `revision`, `checkpoint_artifact` |
| `seeds` | Explicit integer `training`, `inference`, `bootstrap`; booleans rejected |
| `artifact_scope` | Nonempty list of relative files/directories whose full file membership is frozen |
| `artifacts` | Nonempty mapping from artifact name to `{path, sha256}`; unique local paths, lowercase SHA-256 |
| `protocol` | `revision`, `profile`, `artifact` |
| `processor` | `revision`, `artifact` |
| `grading` | `judge_model_id`, `judge_revision`, `policy_artifact` |
| `source` | `revision`, `registry_artifact` |
| `weights` | `mode` (`explicit_uniform` or `record_id`), `artifact` |
| `comparison` | `estimand`, `multiplicity_policy`, `practical_gain_threshold`, `max_task_regression`, `artifact` |
| `execution` | `configuration_artifact`, `code_artifact`, `environment_artifact`, `python_version` |
| `evaluation_manifest_artifact` | Artifact name for the exact evaluation population |
| `confirmation` | For other purposes: explicit `null`. For confirmation: `set_id`, `selected_on`, `selection_decision_artifact`, `mechanical_failure_rule` |

All `*_artifact` fields and each section's `artifact` name an entry in `artifacts`, not an unverified remote URL. Checkpoint references can point to a local archive or explicitly enumerated bundle index; include all bundle members in the selected scope and declared artifacts. The tool does not parse checkpoint formats or verify that an index correctly describes its members. Revisions must be supplied rather than inferred from model names. Common moving aliases/placeholders such as `main`, `HEAD`, `latest`, `pending` and `TBD` are rejected; the validator cannot prove that another supplied revision string is pinned at its upstream provider.

The comparison thresholds must be finite numbers in `[0, 1]`; no threshold or multiplicity method is recommended by this validator. Uniform weights still require an explicit artifact describing the chosen population/weight policy. The comparison artifact should state the exact candidate pair, estimand, population, exclusions/failure handling, resampling and multiplicity/selection rule. The grading artifact should bind judge prompt, parsing/failure policy and calibration evidence. The protocol/execution artifacts should include task and context prompts, template versions, processor settings, token budgets, trainable modules, optimizer, learning rate, normalization, precision and all other run settings relevant to the declared experiment. Include source-data/manifests and environment locks in the artifact map as appropriate.

These artifact contents are deliberately opaque to this module. It checks their exact bytes and mandatory provenance references, not scientific adequacy or completeness of an arbitrary run configuration. It does not connect the declaration to an inference/training runner, prove the named files were consumed, check grade-to-baseline correctness, or establish data independence. Those reviews remain necessary even when every required field is present.

`verify_experiment_record` reads the exact declared scope, rejects missing/extra files and hash mismatches, and returns `ok`, `experiment_id`, `purpose`, `record_sha256`, `artifact_count` and a receipt. It creates no files or confirmation state. The record digest is SHA-256 over UTF-8 JSON using sorted keys, compact separators, unescaped Unicode and finite values. Use a strict JSON loader that rejects duplicate keys; the package CLI does so. A Python dictionary cannot preserve duplicate keys that were already discarded by a permissive loader.

## Artifact receipts

```python
receipt = create_artifact_receipt(
    root,
    ["inputs", "source/code.zip", "locks/environment.txt"],
    receipt_output,
)
check = verify_artifact_receipt(
    root,
    receipt,
    expected_receipt_sha256=independently_retained_receipt_hash,
)
```

Selections must be canonical relative POSIX paths, without `..`, absolute paths, symlinks, duplicate selections or overlapping selections. Directories cover all regular files recursively, including additions made after receipt creation. An explicit file covers only that file: neighboring files are outside the receipt's claim. Directory metadata, empty directories, permissions, ownership and extended attributes are not recorded. At least one regular file is required. Archives are fingerprinted as bytes; their contents are not extracted or validated.

Each artifact has `path`, `size_bytes` and the SHA-256 of its exact bytes. The receipt has `schema_version`, `kind`, typed `selections`, sorted `artifacts`, and `receipt_sha256`. That digest covers the canonical JSON payload excluding `receipt_sha256`; it is **not** the raw byte hash of the pretty-printed receipt file. Equivalent selections and unchanged bytes produce the same receipt. Large artifacts are streamed in 1 MiB chunks.

The output must be outside the selected scope. Creation uses exclusive file creation and refuses an existing output, even an empty file or symlink. Verification requires an independently retained expected digest rather than trusting the receipt's digest field. It returns `{ok, missing, extra, changed}` with sorted relative file paths. Malformed/tampered receipt structure, unsafe paths or a file/directory type change raise `ValueError`; ordinary missing files or byte changes return `ok: false`. Read/access errors propagate as `OSError`.

Use a quiet local directory while collecting or checking hashes. The implementation checks file size, inode and modification time before and after hashing to catch ordinary concurrent writes. It provides no atomic multi-file snapshot and does not defend against adversarial filesystem races. Keep receipts and their independently retained digests somewhere whose change controls are appropriate to the experiment.

## Confirmation lifecycle

The supported sequence is:

```text
frozen_unopened -> opened -> result_recorded -> retired_to_development
```

Freeze is only accepted for `purpose: confirmation`. `selected_on` must explicitly be `external_development_only`. The stable `set_id` identifies the confirmation set across candidate changes; do not rename it to reuse a set. A selection decision artifact and mechanical failure rule are required before freeze. The module records these declarations without establishing their truth.

```python
frozen = freeze_confirmation(record, root, store, frozen_at_utc="2026-10-04T10:01:00Z")
ledger = frozen["ledger_path"]
freeze_hash = frozen["event_sha256"]  # Retain independently before accessing the set.

opened = open_confirmation(
    ledger, root,
    expected_freeze_sha256=freeze_hash,
    expected_latest_sha256=freeze_hash,
    opened_at_utc="2026-10-04T10:02:00Z",
)
# After one execution, preserve its result file outside the frozen input scope.
result = record_confirmation_result(
    ledger, root, "run-results/confirmation.json",
    expected_freeze_sha256=freeze_hash,
    expected_latest_sha256=opened["event_sha256"],
    recorded_at_utc="2026-10-04T11:00:00Z",
)
check = verify_confirmation(
    ledger, root,
    expected_freeze_sha256=freeze_hash,
    expected_latest_sha256=result["event_sha256"],
)
```

`freeze_confirmation` validates all declared fingerprints before creating any ledger. It creates a new directory under `store`, named by the SHA-256 of `set_id`, and exclusively writes `00-frozen.json`. The frozen event contains the entire declaration, receipt, timestamp and event digest. An existing directory is never reused, even if empty or its original candidate differs. Failed/partial creation is deliberately left visible for inspection instead of silently erased and retried. Store/ledger outputs must be outside the frozen artifact scope.

`open_confirmation` checks the retained freeze digest, event sequence and all frozen artifact bytes, then exclusively creates `01-opened.json`. It records the caller's intended first access; it neither opens a dataset nor prevents other software or people from reading it. It cannot prove that the set was previously untouched.

`record_confirmation_result` requires the opened state, verifies frozen inputs again, fingerprints a relative regular result file outside their scope and exclusively creates `02-result.json`. The tool does not parse a score or filter disappointing outcomes. It records the result's hash/size/path, **not a backup copy**: preserve the result file. If input artifacts drifted, recording fails; preserve the raw run result and investigate the failed provenance check rather than rewriting the frozen inputs or silently declaring a valid confirmation.

If a result informs any change, retire the set before further development:

```python
retired = retire_confirmation(
    ledger,
    expected_freeze_sha256=freeze_hash,
    reason="Confirmation result informed a prompt revision.",
    expected_latest_sha256=result["event_sha256"],
    retired_at_utc="2026-10-04T12:00:00Z",
)
```

Retirement requires a recorded result and creates `03-retired.json` with `result_informed_changes: true`. The terminal state permits no reopening, replacement result or reselection in that ledger/store/set identity. A new independent confirmation set is needed for another confirmation claim. Mechanical failure does not provide an automatic retry or fallback exception; document the failure in the result artifact and follow the prospectively reviewed policy outside this helper.

Each event links its predecessor's digest; event timestamps must be nondecreasing and cannot precede the declaration. Each returned event has `event_sha256`; retain every transition hash independently. `verify_confirmation` requires both first and latest retained hashes, checks the contiguous recognized event sequence, and checks current frozen artifact and result bytes. It returns `ok`, current `status`, `event_count`, `latest_event_sha256`, `artifacts` and `result` (`null` before result recording). Altered or truncated history fails against the latest retained anchor. An ordinary result-file change or deletion produces `ok: false` in its result check.

Every mutation requires both `expected_freeze_sha256` and `expected_latest_sha256` and verifies them inside the transition before creating any event. For the initial opening, both anchors equal the freeze hash. For result recording, supply the independently retained opened-event hash as latest; for retirement, supply the result-event hash. A stale latest anchor rejects history that has been rewritten, truncated or advanced since that hash was retained. There is no signing service, trusted clock, remote registry, cross-store global uniqueness, or filesystem access control. A caller can bypass the local rules by deleting history and substituting an older anchor, changing set identity, using another store, or editing files and replacing retained hashes. The code does not claim to stop those actions or make a receipt physically immutable.

## Synthetic verification

`tests/test_experiments.py:fixture` constructs a fully specified declaration over files containing obvious `synthetic ...` text. Its checkpoint, protocol and grading files are placeholders **only for software tests**. They are not a real model, approved source, executed experiment or completed scientific confirmation. To inspect the API using those fixtures without persistent outputs:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:tests python3 - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory
from test_experiments import fixture
from mmbu_prep.experiments import verify_experiment_record

with TemporaryDirectory() as directory:
    root = Path(directory)
    record = fixture(root, purpose="engineering")
    verified = verify_experiment_record(record, root)
    print({"synthetic_only": True, "ok": verified["ok"], "files": verified["artifact_count"]})
PY
```

Run the focused tests with:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p test_experiments.py -v
```

The tests exercise missing protocol/identity, absent artifact references, wrong hashes, explicit weights/seeds, complete file-set matching, symlinks, tampered receipts, byte drift, new relevant files, missing artifacts, exclusive receipt/ledger creation, reopening, duplicated results, terminal retirement, backdated transitions, duplicate JSON keys, event rewriting/truncation and result-byte changes. [experiments-red.txt](../evidence/experiments-red.txt) preserves the initial 19 expected failures; [experiments-verification-red.txt](../evidence/experiments-verification-red.txt) records three additional expected failures before read-only verification was implemented. [experiments-mutation-anchor-behavior-red.txt](../evidence/experiments-mutation-anchor-behavior-red.txt) demonstrates that a rehashed later event could previously be advanced without checking the retained latest anchor inside the mutation. [experiments-green.txt](../evidence/experiments-green.txt) records the focused passing run, interpreter and exit code after that safeguard was added. These are engineering checks with synthetic data, not GPU/model/protocol readiness evidence.
