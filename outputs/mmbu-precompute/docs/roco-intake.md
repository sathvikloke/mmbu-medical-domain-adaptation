# ROCOv2 training metadata quarantine

`mmbu_prep.roco.build_roco_inventory` prepares a source-native metadata inventory and a deterministic inspection shortlist. It does not acquire images, create a canonical image manifest, assign development/confirmation splits, or approve model use. All records remain pending with empty `allowed_purposes`.

The implementation uses the [verified source-expansion findings](source-expansion.md): Zenodo DOI `10.5281/zenodo.10821435`, version `2.0.1`, aggregate CC BY-NC 4.0. Upstream attribution strings are preserved, with exact license versions and original figure/patient identity left unknown.

```python
from pathlib import Path
from mmbu_prep.roco import build_roco_inventory

inventory, audit = build_roco_inventory(
    Path("work/source-expansion"), per_modality=4, seed=1729,
)
assert audit["release_integrity_verified"]
by_id = {row["source_image_id"]: row for row in inventory}
shortlist = [by_id[key] for key in audit["shortlist_source_image_ids"]]
```

Run from the project root with the package installed, or set `PYTHONPATH=outputs/mmbu-precompute/src`. The function returns `(list[dict], dict)` and writes nothing. It accepts the exact native filenames or their `roco-` prefixed local acquisition aliases, requiring exactly one of each. Required inputs are `train_concepts_manual.csv`, `train_captions.csv`, `license_information.csv`, and `cui_mapping.csv`. The all-partition license table contains article identity and rights assertions; no heldout image or label files are required.

Each CSV must have the expected ordered header, unique keys and complete rows. Training concepts, captions and training license IDs must join exactly. Training captions and labels cannot contain a source-valid or source-test ID. PMCIDs and article URLs must agree, and the six modality CUIs must retain their source canonical names. Structural errors fail the whole intake before anything is published. SHA-256 and MD5 receipts cover every input; `release_integrity_verified` is true only when all four MD5s match the recorded publisher release. Synthetic unit-test tables can exercise behavior but correctly return false for that release check.

Individual questionable labels are retained with flags instead of being silently repaired: missing/ambiguous modality, unknown/repeated CUIs, X-ray context without an X-ray label, and training articles that cross a source heldout partition. All 18 observed manual CUIs preserve their source text. Captions are review-only provenance; they never generate disease answers.

The shortlist accepts exactly one recognized manual modality and an attribution beginning with literal `CC BY ` followed by a nonblank attribution. NC, public-domain assertions and malformed prefixes remain outside this particular shortlist. This is a provenance filter, not a legal clearance decision; even selected records retain the aggregate NC declaration and unverified upstream versions. Empty labels are missing supervision rather than negatives.

For each modality in lexical CUI order, candidates sort by `SHA256(seed + NUL + CUI + NUL + source_image_id)`, with source ID as the tie-breaker. The function takes up to the requested count while allowing each PMCID only once across the whole shortlist. Insufficient eligible articles produce a disclosed shortfall, without sampling with replacement or substituting another license class. This is an engineering inspection sample, not a representative evaluation cohort. Changing the seed is a new recorded inspection draw, not a way to discard failures.

The October 4 run is recorded in [roco-inventory-audit.json](../evidence/roco-inventory-audit.json) and [roco-shortlist.json](../evidence/roco-shortlist.json):

| Intake result | Count |
| --- | ---: |
| Source training metadata records | 59,958 |
| Eligible inspection pool | 46,241 |
| Unique records excluded from inspection pool | 13,717 |
| Missing manual modality | 493 |
| Attribution outside the exact CC BY prefix | 13,331 |
| Selected source images / distinct articles | 24 / 24 |
| Selected per modality | 4 |

The reason counts overlap, so they should not be added to obtain unique exclusions. All four source file hashes matched. No source-training article crossed either heldout partition. The 24 metadata records have no image hash, image dimensions, image path or asserted original figure identity. A later image acquisition step must record and verify source archive membership, byte hashes and decode properties separately, and then perform image-supported conversion review. No image-backed acceptance can be inferred from metadata completeness.

Verification: [ten focused unit tests](../tests/test_roco.py) cover exact joins, duplicate IDs, malformed PMCIDs/link mismatches, semicolon labels, source-training isolation, exclusion flags, deterministic ordering, global article uniqueness, filename alias ambiguity and changed modality semantics. [The first run failed before implementation](../evidence/roco-tests-red.txt); [the implementation passes](../evidence/roco-tests-green.txt). The real metadata audit independently exercised the full 59,958-record join. No model was run.
