# Independent ROCOv2 metadata review

Review date: 2026-10-04. Reviewer: `/root/processor_probe`, separate from the source-inventory author. This review changed no ROCO implementation, tests, source files, audit or shortlist. It used Python 3.12.14, read local source-training metadata and the all-partition article/license table, and consulted the current primary [Zenodo record 10821435](https://zenodo.org/records/10821435). No image archive, heldout image, heldout caption or heldout concept file was downloaded or opened by this review.

Verdict: **PASS within the metadata-only scope; no actionable defect found.** The reviewed code and evidence support a deterministic quarantine inspection shortlist. They do not establish image-label correctness, source/model-use eligibility, cleared rights, patient independence or model performance. This is a focused independent review, not a full SENTINEL audit.

## Exact reviewed artifacts

| Package-relative path | Bytes | SHA256 |
| --- | ---: | --- |
| `src/mmbu_prep/roco.py` | 13,360 | `392caca85d1b31e7f249944f0f5783dce187bd1ff8133410c02a6421c328e536` |
| `tests/test_roco.py` | 8,590 | `36ed0b12621e9cf142518fd6c37263dd8efc1ae6d7a812c8a3189e82ecd956bb` |
| `docs/roco-intake.md` | 5,175 | `1f4fcd97ac9037b3cb3362cae6fabbd2bb8969e1f0b8d94077f1b61ab0d2b75b` |
| `evidence/roco-inventory-audit.json` | 5,120 | `a8b37f636d5ba1a5819bfa8d0c34232ba3adde063ee983433c2040e7f672cae8` |
| `evidence/roco-shortlist.json` | 57,515 | `d815b2238224f8e92cf5f321aba387e9a4ca3686bfd4dab13bf1c3b4377b9014` |

The published record independently confirms version 2.0.1 and the four MD5 values below. The saved primary API metadata also identifies record 10821435 and `cc-by-nc-4.0`; no interpretation of that declaration as model-use permission was made. Local sizes and digests were recomputed from raw bytes, rather than accepted from the authored audit.

| Raw file in `work/source-expansion/` | Bytes | Recomputed MD5, matching publisher |
| --- | ---: | --- |
| `roco-train_concepts_manual.csv` | 2,352,220 | `29c00284c410665b6fe6ddc7f0b72f0a` |
| `roco-train_captions.csv` | 10,100,161 | `fac7fc6bd570408f451e7558b994518a` |
| `roco-license_information.csv` | 9,446,130 | `65f21bc4620778259b530a2c033cd4e7` |
| `roco-cui_mapping.csv` | 62,591 | `b12e7e3627b599b18c68dd3091294ef6` |

Their recomputed SHA256 values, in the same order, were:

```text
1da272c7fbb2fd08b2a932e6bbff811bd5dfc5b50c5bef60df16b7bd0d1badbd
2b219f3579b24750e3e170a1b1eb1edfb50361c45acba2bba34560a0fe867b81
f56f9c6959b2d4152743c001cda7c126052961b9e10c03b7486cf8d7f50559e3
63cf714611563e3bc3e564cc0b47ef32f267cb13cb90f7465a1ed293976ab502
```

Every value exactly matched the saved inventory audit's receipt and the sizes/checksums in the saved publisher API. The current publisher page was read without following heldout file links.

## Independent recomputation

The reviewer parsed the four raw files with standard-library `csv.DictReader(newline='')`, independently constructed ID dictionaries and asserted uniqueness. The manual labels and captions each contain 59,958 records. The 79,789-row article/license table's training ID set exactly equals both training tables; the concept mapping has 1,934 unique rows. Quoted captions were preserved as CSV values, not split by punctuation.

Independent article sets gave 33,814 training, 7,759 validation and 7,819 test articles. Training intersects neither heldout set. Validation/test article overlap is 4,417. Those observations use identifiers in the all-partition attribution table and no heldout labels; they do not prove patient independence.

Manual-CUI parsing independently found 18 distinct CUIs, no repeated CUIs within a record, no unmapped CUI and at most one recognized modality per record. Counts reproduced exactly:

| CUI | Source training rows |
| --- | ---: |
| C0002978 | 3,958 |
| C0024485 | 9,790 |
| C0032743 | 350 |
| C0040405 | 20,459 |
| C0041618 | 8,305 |
| C1306645 | 16,603 |
| Missing modality | 493 |

The independent literal `CC BY ` prefix check excluded 13,331 attribution strings; combined with missing modality, 46,241 records remained eligible and 13,717 unique records were excluded. Exclusion counts overlap. This check reproduces a deliberately narrow provenance filter, not a legal conclusion.

The reviewer independently sorted eligible tuples by `SHA256('1729' + NUL + CUI + NUL + ID)`, with ID as tie-breaker, processed the six CUIs in lexical order, and selected four per modality while enforcing global PMCID uniqueness. The resulting 24 IDs exactly matched `shortlist_source_image_ids` in the authored audit, with 24 distinct articles. This was a separate standard-library calculation, not an invocation of the author's selector to check itself.

After the independent calculation, `build_roco_inventory(work/source-expansion, per_modality=4, seed=1729)` was executed to check implementation correspondence. The complete returned audit exactly equaled the saved JSON. Indexing its inventory by the independently selected IDs produced a list exactly equal to the saved 24-record shortlist. Assertions over all 59,958 returned records verified:

- `metadata_only=True`, `training_ready=False`, source partition `train`, and empty `allowed_purposes`.
- Exact caption and attribution values from the raw joined source tables.
- Proposed modality answers equal the source mapping for the selected CUI; missing modality retains no answer.
- Null original figure/patient identities; no image path, byte hash or dimensions asserted.

The original source-derived names were preserved. The review did not medically interpret captions or decide whether a future image visibly supports a label.

## Executed tests and reproduction

Command, from the project root:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=outputs/mmbu-precompute/src:outputs/mmbu-precompute/tests \
work/processor-probe/.venv/bin/python -m unittest test_roco -v
```

Observed result: **10 tests passed in 0.019 seconds, exit 0**. Tests cover joins, duplicate IDs, malformed PMCIDs/links, semicolon labels, source-training isolation, exclusion accounting, deterministic row-order invariance, unique article selection, ambiguous filename aliases and changed modality mappings. The separate full raw-source recomputation described above also exited 0.

The key real-data implementation/evidence comparison can be repeated with:

```python
import json
from pathlib import Path
from mmbu_prep.roco import build_roco_inventory

package = Path('outputs/mmbu-precompute')
inventory, audit = build_roco_inventory(Path('work/source-expansion'),
                                       per_modality=4, seed=1729)
assert audit['release_integrity_verified']
assert audit == json.loads((package / 'evidence/roco-inventory-audit.json').read_text())
by_id = {row['source_image_id']: row for row in inventory}
assert [by_id[key] for key in audit['shortlist_source_image_ids']] == json.loads(
    (package / 'evidence/roco-shortlist.json').read_text())
```

The function intentionally allows synthetic or changed tables for diagnostic tests while reporting `release_integrity_verified=False`. The documented real-data workflow checks that flag. Consumers must retain that explicit release-integrity check before treating any future acquisition as belonging to the pinned release. No image-backed acceptance or model-use approval follows from this metadata review.
