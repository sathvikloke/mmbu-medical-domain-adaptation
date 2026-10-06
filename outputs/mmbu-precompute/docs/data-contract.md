# Manifest and split contract

This is an offline engineering validator. Recorded source approval is an input, not a permission decision made by this package. The supplied real sources remain candidates. A passing result does not establish label correctness, biomedical validity, or compliance with an official challenge protocol.

## Python API

```python
validate_manifest(records, registry, *, image_root=None, purpose="engineering") -> dict
assign_splits(records, *, registry, seed, ratios) -> list[dict]
```

`records` must be a nonempty list of dictionaries. `registry` is mandatory for assignment so callers cannot accidentally bypass source authorization. Both functions leave caller data unchanged; assignment returns deep copies in the original input order. Empty record lists fail with `empty_manifest`.

Validation returns `ok`, `errors`, `warnings`, and `counts`. Errors and warnings contain a stable `code` and explanatory `message`, plus applicable `record_index`, `record_id`, `source_index`, `source_id`, `field`, or leakage details. Indices are zero-based. Missing IDs remain missing: no replacement IDs or grouping values are invented. Consumers should branch on `code`, not message text.

Counts contain `records` (including malformed submitted rows), `sources` (distinct nonempty submitted source IDs, including unknown ones), `components` (connected components among dictionary rows), `files_checked` (distinct resolved files actually hashed), `by_split`, and `by_task`. Invalid split/task values are excluded from those two distributions. Inspect `ok` before treating counts as usable-data counts.

## Registry schema, version 1

The top-level object requires integer `schema_version: 1` and a `sources` list. Each source requires:

| Field | Required value |
|---|---|
| `source_id` | Unique, nonempty string |
| `source_version` | Nonempty version or pinned revision string |
| `source_family` | Nonempty lineage/group namespace; related collections should share it |
| `source_role` | `external`, `official`, or `synthetic` |
| `status` | `candidate`, `quarantined`, `approved`, or `engineering_only` |
| `allowed_purposes` | List of unique values from `engineering`, `train`, `dev`, `confirmation`, `official_dev` |
| `evidence` | For `approved`: nonempty list of nonempty strings or nonempty finite-JSON objects |
| `reviewed_by` | For `approved`: nonempty string |
| `reviewed_at` | For `approved`: nonempty string identifying the review date/time |

Evidence objects can hold URLs, excerpts, review receipts, or structured decisions; the validator checks their presence and representation, not their truth, sufficiency, or date syntax. Source-specific access, rights, permitted release, overlap, annotation and review fields may be included and preserved. Changing a source's approval requires the separate review process documented in the source screening checklist.

Registry structure is checked even for unused sources. Unused `candidate` or `quarantined` sources do not by themselves cause failure, but any record referencing them fails eligibility. A source marked `approved` still needs explicit permission for both the requested `purpose` and the record's current `split`.

For operational purposes `train`, `dev`, `confirmation`, and `official_dev`, every record must also have exactly that existing split. For example, a confirmation record fails `purpose="train"` with `purpose_split_mismatch` even if its source permits both uses. The public API and CLI provide no bypass flag. `purpose="engineering"` remains a mechanical audit that can inspect a manifest containing several existing splits, subject to engineering permission, existing-split permission, and the full leakage check; an engineering result does not authorize training on held-out records.

`engineering_only` is valid only for a `synthetic` source with exactly `allowed_purposes: ["engineering"]`. Conversely, every `synthetic` source must have that status and permission list. No synthetic fixture can enter training, dev, confirmation, or official dev. Public accessibility or the spelling of a split never supplies approval.

Official/challenge sources are forbidden from `train`, `dev`, and `confirmation`, even if their registry permissions claim otherwise. `official_dev`, whether used as a split or a requested purpose, requires role `official` and explicit permission. This makes official examples distinct from external selection and confirmation data. An engineering-only validation of official examples also needs explicit engineering permission; it is not automatically authorized.

## Record schema, version 1

All fields below are required. Extra fields are preserved and checked only for finite JSON serialization; they are not interpreted as permissions or silently passed to model inputs.

| Field | Contract |
|---|---|
| `schema_version` | Integer `1`, excluding Boolean |
| `record_id` | Globally unique nonempty string |
| `source_id` | Registered source identifier |
| `source_version` | Exact match to that source's version |
| `source_family` | Exact match to that source's family |
| `split` | `engineering`, `train`, `dev`, `confirmation`, or `official_dev` |
| `image_path` | Nonempty relative POSIX path; no absolute path, backslash, Windows drive prefix, NUL or `..` component |
| `image_sha256` | Exactly 64 lowercase hexadecimal characters |
| `parent_image_sha256` | Same hash representation or explicit JSON `null`; key cannot be omitted |
| `group_id` | Explicit nonempty grouping identifier within `source_family` |
| `task` | `global_classification`, `counting`, `box_classification`, `mask_classification`, or `detection` |
| `question` | Nonblank string |
| `answer` | Present, finite JSON value satisfying the task-specific rules below |
| `context` | Object mapping canonical fields to nonblank strings; may be empty |
| `annotation_origin` | Nonempty string recording target provenance |
| `conversion_version` | Nonempty conversion recipe/version string |
| `review_status` | Nonempty string satisfying the review rules below |
| `synthetic` | Boolean matching whether the registered role is `synthetic` |

`review_status: "approved"` is required whenever either the requested purpose or existing split is nonengineering. If both are engineering, `engineering_reviewed` or `approved` is accepted. Other statuses such as `pending` or `quarantined` fail the use gate. Source approval does not substitute for record review.

Internal target forms are deliberately explicit while official output serialization remains unresolved:

| Task | Internal answer form |
|---|---|
| Global or box classification | Nonblank string |
| Mask classification | Nonblank string, or nonempty list of nonblank strings |
| Counting | Nonnegative Python/JSON integer (Boolean excluded), or canonical ASCII decimal string matching `0` or `[1-9][0-9]*`; no leading zeros, sign, whitespace, or decimal point |
| Detection | One `[x,y,width,height]` array or a nonempty list of such arrays; additionally requires positive finite `image_width` and `image_height` |

Detection targets are checked with the shared `contracts.validate_xywh` helper: finite numeric coordinates, Boolean excluded, nonnegative x/y, strictly positive extent, and no excursion outside the declared dimensions. Fractional pixel coordinates are allowed and no value is clamped, rounded, rescaled, or repaired. Empty detection lists are not silently interpreted as negative examples; a supported encoding for that case remains unresolved. Correct coordinate units, actual decoded image dimensions, lesion identity, task-dependent box matching, and visual support are not established by these arithmetic checks.

Context keys are limited to `modality`, `submodality`, `specimen`, `body_part`, `stain`, and `medical_domain`; every included value must be a nonblank string. An empty context object is allowed in an annotation manifest, but does not define a zero-field scoring rule. The validator does not grade the values or convert targets. Box/mask classification labels are checked syntactically; rendered region overlays and mask semantics still need their separate review.

## Paths and file identity

Without `image_root`, validation checks path syntax and emits `files_unchecked`. With `image_root`, the root must resolve to an existing directory. Each image path is resolved with `Path.resolve`, including symlinks; resolved paths outside the root fail. Existing regular files are streamed into SHA-256 and compared with the manifest. Files, hashes, and paths are never repaired. An invalid root, unreadable/missing file, symlink escape, or hash mismatch is an error.

The hash can be computed for any bytes: it does not prove the file decodes as an image. Byte hashes do not discover differently encoded copies, resized images, near duplicates, incorrect inherited lineage, or hidden patient/study overlap. File checks assume a stable local tree during validation; this is not a security sandbox against concurrent filesystem mutation. Parent hashes need not have a corresponding file or record in the supplied manifest.

## Leakage components

A connected component joins records whenever:

1. Any `image_sha256` or non-null `parent_image_sha256` matches any such hash on another record. Hash keys are global, so a crop and its parent remain linked across source IDs **and across declared families**. Sibling crops with an absent shared parent also remain linked.
2. Both `source_family` and `group_id` match. Related source versions/datasets should use the same family; identical group strings in unrelated families do not merge by themselves.
3. Those relationships connect transitively. For example, A shares a parent with B, and B shares a group with C: A, B and C form one component.

Any component containing more than one existing split fails with `split_leakage`, including engineering/official/external boundaries. Missing or invalid groups and hashes fail validation before assignment. The intended group is the patient, study, slide, acquisition batch, or other defensible dependence unit, not a row ID chosen merely to make the check pass.

Only submitted records and declared lineage are visible to this check. Include the relevant existing partitions and overlap inventory when auditing leakage. Passing a small subset alone cannot establish disjointness from an omitted challenge or upstream dataset.

## Deterministic assignment

`seed` must be an integer, excluding Boolean. `ratios` must be a nonempty dictionary with keys drawn only from `train`, `dev`, and `confirmation`; values are finite numbers in `[0,1]`, excluding Boolean, and must sum to one within absolute tolerance `1e-12`. Zero-probability targets are never assigned. Every positive target needs source permission for every input record.

Assignment first validates the entire supplied manifest using a private mechanical validator and the first positive target in fixed order `train`, `dev`, `confirmation` for source permission. This internal preassignment audit omits only the purpose-equals-existing-split check; it still checks the complete manifest for leakage, provenance, item approval, source eligibility, and both purpose and existing-split permissions. Official/challenge sources and synthetic fixtures are never assigned. Records may begin in `engineering` or `train` if their approved external source explicitly permits the current split and every positive target. Permission is checked again for every positive target. Validation and configuration failures raise `ValueError`; omitting the mandatory registry raises Python `TypeError`.

Existing `dev` and `confirmation` records are protected. If any positive target differs from a protected record's existing split, the whole assignment raises `ValueError` before changing anything. Thus dev-only records can pass an unchanged `{"dev": 1}` assignment, and confirmation-only records can pass `{"confirmation": 1}`; a mixture with even a small positive training share fails regardless of the eventual hash bucket. A zero-probability other target does not request movement. The tool cannot retire a held-out set. Any intentional retirement needs a separately reviewed provenance decision outside this assignment API; changing a marker alone cannot undo prior evaluation exposure.

Each connected component is mapped as a whole using SHA-256 of a versioned payload containing the seed and sorted `(source_id, source_version, record_id)` tuples. Fixed target order makes the mapping independent of both input record order and ratio-dictionary insertion order. Reordering inputs preserves assignments while the output preserves caller order. Adding or removing members of a component can change its assignment; freeze the reviewed manifest before an experiment.

Ratios are hash-bucket probabilities, **not exact row quotas**. A large component may dominate a partition, and a small manifest can leave a target empty. There is no stratification, automatic source holdout, exact balance guarantee, immutable manifest store, or historical exposure tracking. Protection applies to declared dev/confirmation markers; the validator cannot discover that a caller manually erased one. Inspect the resulting counts and source coverage, then record and freeze the approved assignment explicitly. The algorithm does not change data to fill a target.

## Test evidence

`tests/test_data.py` uses invented approvals and tiny local byte files solely to test gates. It contains no approved real training corpus. `evidence/data-test-log.txt` records the initial failures, additional regression failures, and final result with exact commands and exit codes. The tests cover missing/duplicate IDs, source/record consistency, approval and purpose restrictions, transitive leakage, ordering stability, hash mismatch, traversal and symlink escape, malformed input, invalid ratios, task-specific target forms, declared detection bounds, canonical context fields, and nonmutation.
