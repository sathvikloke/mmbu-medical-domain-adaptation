# Independent experiment receipt and CLI review

Review date: 2026-10-04. Reviewer: `/root/processor_probe`, separate from the experiment-record and CLI authors. No production or test code was changed by this review. Executions used Python 3.12.14 in the processor probe's isolated environment, temporary synthetic files and local subprocesses. No model, source dataset, network acquisition or genuine confirmation run was performed.

Verdict: **PASS within the declared local provenance scope; no actionable defect found.** This is a focused code/behavior review, not a full SENTINEL audit or evidence that a declaration corresponds to an actual executed scientific experiment.

## Exact reviewed versions

| Package-relative file | SHA256 |
| --- | --- |
| `src/mmbu_prep/experiments.py` | `4592ac4f9451257d5c87b067cba6d46f07dc4046f037f1b163e31c2996b069ec` |
| `src/mmbu_prep/_cli_experiments.py` | `38b3bb63c09c75fe1180a45559db889e7e27999030b8fd363ecae930fd1534cf` |
| `src/mmbu_prep/__main__.py` | `bf88ba4b49554e0ddc3e202bbd18e2fd112e550351fe6d7bff6b0cf9c1e1617e` |
| `tests/test_experiments.py` | `a575f92973699ccf119143d90a5196fe20e3454bcbb684828cdd2bed0674a424` |
| `tests/test_cli_batch3.py` | `3ab56ce7706409e99ea8862db18bac87014ee6b8a39fb1b4ca2b175a41ebb72a` |

## Retained anchors and state order

Source inspection confirmed that receipt verification checks both the recomputed canonical JSON digest and the independently supplied expected digest. The receipt cannot authenticate itself by merely replacing its own digest. The canonical recipe is sorted keys, compact separators, UTF-8, unescaped Unicode and finite JSON. The returned receipt digest is deliberately distinct from the raw pretty-printed file hash.

The reviewer independently recomputed the canonical digest for a CLI-created receipt over thirteen synthetic files and matched it exactly. The wrong retained digest returned a structured error with exit 2; the correct digest returned `ok:true`, exit 0.

Frozen records bind the full declaration and exact selected local file receipts. Later event hashes bind their predecessor; each mutation and read-only confirmation verification also require the independently retained freeze and latest hashes. Thus a rehashed intermediate event cannot be accepted while retaining the old final hash, and truncation cannot be accepted while retaining the newer latest anchor. Supplied tests execute rewritten/truncated tails and confirm rejection without adding the next event.

The only mutation sequence is `frozen_unopened → opened → result_recorded → retired_to_development`. Tests exercise skipped, repeated, backdated and terminal-state transitions. The review's independent CLI exercise attempted result recording before opening, and again after opening with the stale freeze hash as latest: both exited 2 and left `02-result.json` absent. With the correct opened-event anchor, result recording succeeded and preserved the exact bytes of a negative synthetic result. No score was parsed or used to select which result to retain.

## Declared scope and byte drift

Declaration-only validation is explicitly identified as `declaration_only_files_not_checked`. Validation with an artifact root compares exact selected file paths/hashes and rejects undeclared additions inside directory scopes. Explicit file selections cover only their named files. Recursive directory selections cover relevant file additions; empty directory metadata, permissions and extended attributes are deliberately outside the receipt's claim.

The implementation rejects parent traversal, noncanonical relative paths, selected symlinks, overlapping selections and receipt/ledger outputs inside frozen scope. Existing receipt and event outputs use exclusive creation. Local artifact hashes are streamed and include ordinary concurrent-change checks; no atomic multi-file snapshot or resistance to adversarial filesystem races is claimed.

Independent CLI checks added a file inside the selected directory and observed exit 2, with the correct relative filename in `extra`. After a successful result record, changing its bytes returned exit 2 with `result.changed == ['result.txt']`; deleting it returned exit 2 with `result.missing == ['result.txt']`. Input and result bytes are checked independently. Retirement records that results informed changes; it does not certify that the scientific result or source use was valid.

## CLI behavior and strict loading

The dispatcher preserves the distinction between structured drift (`ok:false` on stdout, exit 2) and runtime/validation errors (JSON error on stderr, exit 2). Successful mutations and checks return 0. Duplicate JSON keys, NaN, Infinity and an overflowing `1e999` input each produced exit 2 in separate subprocesses. No permissive decode silently discarded a duplicate or converted an overflow to infinity.

The batch3 diagnostics/calibration paths retain the earlier module boundaries: partial task coverage remains explicit and random versus targeted calibration summaries remain separate. These results are diagnostic arithmetic, not winner selection. The acquisition module is not added as a network command to the offline prep CLI.

## Executed evidence

Command from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=outputs/mmbu-precompute/src:outputs/mmbu-precompute/tests \
work/processor-probe/.venv/bin/python -m unittest test_experiments test_cli_batch3 -v
```

Observed: **28 tests passed in 0.890 seconds, exit 0**: 23 experiment tests and 5 batch3 CLI tests. In addition, 18 independent CLI invocations asserted exact expected exit codes, JSON result/error placement, digest arithmetic, file-set closure and lack of events after failed transitions. That driver completed with exit 0:

| Independent operation | Expected and observed exit |
| --- | ---: |
| Declaration-only experiment validation | 0 |
| Local experiment verification with extra scoped file | 2 |
| Local experiment verification after removing extra file | 0 |
| Receipt creation | 0 |
| Receipt verification with wrong retained anchor | 2 |
| Receipt verification with correct retained anchor | 0 |
| Receipt verification with added selected-scope file | 2 |
| Duplicate-key declaration input | 2 |
| NaN declaration input | 2 |
| Infinity declaration input | 2 |
| Overflowing `1e999` declaration input | 2 |
| Confirmation freeze | 0 |
| Result before opening | 2 |
| First opening with correct anchors | 0 |
| Result with stale latest anchor | 2 |
| Result with correct opened-event anchor | 0 |
| Read-only verification after changing result bytes | 2 |
| Read-only verification after deleting result file | 2 |

The implementation and documentation consistently limit their claim to declared local bytes and retained hashes. Opaque configuration contents are not scientifically validated; revision strings are not resolved against upstream providers; author-declared source permissions are not granted; the ledger cannot stop an external tool from reading a confirmation set or a caller from deleting history and replacing independently retained anchors. Those disclosed limits were not misreported as defects in this bounded helper.
