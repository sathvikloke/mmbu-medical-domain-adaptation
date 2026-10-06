# Independent data-contract review

Reviewed October 3, 2026 (America/Chicago), against Task 2 and the current CLI. Reviewer `/root/model_data_audit` did not author `data.py`, its tests, or its contract documentation. The reviewer previously authored the source registry; its present values were used only as integration inputs, not independently certified for substantive source approval.

Initial verdict: **one moderate accidental-use defect requires repair**. No actual training, held-out-data leak, source clearance or model evaluation occurred. This is a bounded software cross-review, not a 16-pass scientific audit. Production code was not modified by this reviewer.

## DATA-REVIEW-01 — Nonengineering purpose can disagree with the record split

**Status: unresolved at initial review. Severity: moderate (P2). Confidence: high, directly reproduced.**

Location in reviewed snapshot: `src/mmbu_prep/data.py:272` and `:274` independently check whether the source allows the requested purpose and the existing split. They do not require the operation to match the record's designated partition. The CLI passes its `--purpose` to this function.

Reproduction: create an invented approved external source permitting `train` and `confirmation`, with nonempty fixture approval evidence and reviewer/date. Supply a fully valid, approved nonsynthetic record with `split="confirmation"`. Then:

```python
result = validate_manifest([confirmation_record], fixture_registry, purpose="train")
assert result["ok"] is True  # observed before repair
```

The source and record in this probe are explicitly invented test inputs, not an authorization to use any real source. This demonstrates the gate condition without accessing held-out biomedical data. The same library path is used by `validate --purpose train`.

Consequence: a caller treating successful training-purpose validation as a training preflight can inadvertently consume held-out records. The documentation's independent-purpose/split description explains the behavior but does not remove that operational risk. No existing trainer or actual leakage is claimed.

Minimum repair: require nonengineering use to match the record's designated split. Keep cross-partition mechanical auditing and initial split assignment on a distinct internal validation path; do not expose a default public bypass of the operation gate. Add regressions for train/dev/confirmation/official-dev mismatches and ensure deterministic assignment remains usable for approved external inputs.

## Other inspected behavior

Read all of `data.py`, `tests/test_data.py`, `docs/data-contract.md`, and the relevant CLI branches. Reviewed required field/type checks, source-role/status/purpose restrictions, item review, target geometry, path/root handling, lineage unions, deterministic assignment and exclusive output creation. The root reported 50 data tests and 105 total tests passing; I did not substitute those reports for inspection or rerun the full suite.

Independent targeted Python probes ran from the package root with `PYTHONPATH=src`, all expected assertions passed, exit code 0:

- All five shipped synthetic engineering records validated against the actual registry and file root.
- Each of the six real candidate entries was rejected when referenced; none gained a purpose through public availability or registry presence.
- A five-record chain linked through an absent shared parent, family/group identity, cross-family parent/image identity and a final group link produced one transitive component. Moving its last member to confirmation triggered a leakage error naming all five.
- All **120 permutations** of that chain preserved one identical assignment and original output order.
- For **30 generated 18-record graphs**, an independently written graph-reachability oracle matched component counts; every expected component stayed in one assigned split.
- Five one/multiple-box geometry cases accepted valid bounds and rejected Boolean, mixed/empty and out-of-frame boxes.
- An invented approved official source with overbroad permissions still could not pass training validation.
- The confirmation/train mismatch above was observed separately and preserved as the finding, not counted as a successful safeguard.

Five subprocess CLI probes used disposable invented approvals and ordinary local test bytes (not biomedical files). Observed outcomes:

| Case | Exit code | Output effect |
|---|---:|---|
| Approved external fixture split, then validate assigned output | 0 | New assignment written; assigned manifest passes existing checks. |
| Repeat using the same output filename | 2 | Existing output remains byte-identical. |
| Change an input file after recording its SHA-256 | 2 | `image_hash_mismatch`; no assignment output created. |
| Duplicate JSON key in manifest | 2 | Loader rejects before validation. |
| Candidate source on CLI validate | 2 | Structured source-ineligibility errors. |

The temporary CLI fixtures were removed. No additional issue was retained from these checks.

## Scope and limitations

Exact hashing does not decode images or detect perceptual duplicates; declared dimensions do not establish the actual displayed coordinate frame. Approval evidence is a human-maintained record, not a rights authority. BBBC family grouping is the documented conservative namespace assumption, not an actual eligibility or independence claim. Initial assignment uses hash probabilities rather than exact quotas or stratification. It cannot enforce a future experiment's confirmation freeze by itself.

No task labels, masks, overlays, source licenses, biomedical correctness, official contract equivalence or omitted-dataset overlap were independently validated. All synthetic fixtures remain engineering-only. The positive split tests used explicitly invented external approvals to exercise mechanics, not the real candidate registry.

## Initial reviewed snapshot hashes

```text
f103db0f0d7ab1583afb6e42b1e9acdcb87b37631cc5c3a4cf5444bfa92e05fc  src/mmbu_prep/data.py
dd5c26b290d4469b2547dbef95e8e0a29ec1547e091b03ddf82fa4d50642bc58  tests/test_data.py
337059ee17f16888b4193d00fc52c32dc75c5ca056b18723a4be38a349a907c2  docs/data-contract.md
074a00acb99f1a37432a557b8eacc9879c1767bc5a67b8a1f56631d5ce3c3c09  src/mmbu_prep/__main__.py
11346c256800fff2d998fa325265c6b005617bbf2fdb62ad12a328e45b8bcc30  configs/source-registry.json
```

Repair review will be appended below; the initial evidence above must remain intact.

## Independent repair closure

**Final status: DATA-REVIEW-01 resolved with reproduced evidence. No remaining actionable blocker found in this bounded review.** The initial finding and hashes above are retained unchanged.

Inspected the completed repair in `data.py`, updated regressions/documentation, and the root's CLI integration. The public validator now fixes `require_purpose_split=True`; the bypass parameter is not part of the public signature. Nonengineering purposes require exact record-split equality. Initial assignment uses the private mechanical path, which retains whole-manifest leakage and permission checks. Existing dev/confirmation records cannot be moved to any different positive-ratio target. The CLI validates each resulting partition under its own operational purpose before exclusive output creation.

Ran a fresh targeted standard-library Python heredoc with the repaired code (`PYTHONPATH=src python3`, exit **0**). Observed:

- All **12 combinations** of three external operational purposes and four existing splits passed only when purpose equaled split. The original confirmation/train counterexample now returns `ok=false` with `purpose_split_mismatch`.
- A public `require_purpose_split=False` keyword raises `TypeError`; no bypass was added to the public API.
- Official-dev validation accepts its matching official-dev split and rejects an engineering split.
- Engineering auditing still accepts independent mixed partitions when permissions allow, and still rejects a cross-partition group link.
- For both dev and confirmation, assignment rejects a pure training target and a mixture with a small positive training share. An unchanged single-target assignment succeeds.
- CLI assignment of **30 invented approved external engineering records** produced train, dev and confirmation partitions, with each reported partition validation `ok=true`. A whole-manifest engineering audit of the assigned output also passed.
- CLI `validate --purpose train` on a confirmation record returned **2** with `purpose_split_mismatch`.
- Repeating assignment to the same output returned **2** and preserved its bytes. Changing an input file returned **2** with `image_hash_mismatch` and did not create a new output.

All disposable probe files were removed. The expanded full-suite result is owned by the integrator; this closure did not unnecessarily rerun that suite. Its independently executed checks directly exercise the defect and the adjacent successful assignment/file-validation path.

No inference is made that users cannot manually falsify provenance or that a marker change erases prior evaluation exposure. Those limits do not excuse the previous accidental-use path; that public operational path is now checked.

Repaired snapshot hashes:

```text
15bf5e2d6feeb84e84b34e74ca83170cc1ad782285c19ecfb2b9144c696a286d  src/mmbu_prep/data.py
88ab6debc8fbce1683e81afcf8a192df5cb46124c4d32e160fed54e1874d38e9  tests/test_data.py
167bd1a26166248ad656f80cbc6d9e9c77d2a5199d19108d08b1fc3f5a50e316  docs/data-contract.md
37863468abe08984a0c62c5b6fdc1dbc12076e7acf944c56dcc85140ca98a3a5  src/mmbu_prep/__main__.py
a180b91afb9c5651d1616b27e9e68989c68bd4bdbc878a8cd9206babbff66ebe  tests/test_cli.py
```
