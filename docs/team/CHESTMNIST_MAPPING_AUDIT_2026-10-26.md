# ChestMNIST public-mapping audit

**Date:** October 26, 2026

**Decision:** the patient key is recoverable, but the published wrapper split is not patient-disjoint and must not be
used unchanged for decision-bearing development.

**Authority boundary:** public mapping metadata only; no image, label vector, model output, or MMBU public content was
opened. This audit does not admit ChestMNIST or authorize model use.

## Reproducible finding

The official MedMNIST [mapping-file index](https://github.com/MedMNIST/MedMNIST/issues/49) identifies
`chestmnist_split_info.csv`. The exact file audited here is 2,836,941 bytes with SHA-256
`3cfe66207037f1f99b1bf457f1f009b0cfc2346ea7a710505a23e02c8ff492e9`. The repository's strict CPU-only validator
requires the exact `split,index,image_id` schema, canonical contiguous indices, the frozen split counts, globally
unique NIH image IDs, and the expected 30,805 patient prefixes.

The mapping contains 112,120 image identities:

| Wrapper split | Images | Unique patients |
| --- | ---: | ---: |
| train | 78,468 | 21,528 |
| validation | 11,219 | 3,093 |
| test | 22,433 | 6,188 |

Every image ID matches the NIH `########_###` identity form and all 112,120 image IDs are unique. The first eight
digits recover 30,805 patient IDs. Three patients cross the official wrapper roles:

| Patient | Wrapper memberships |
| --- | --- |
| `00005681` | validation, test |
| `00027864` | train, validation, test |
| `00028591` | train, validation |

The machine-readable result is retained in
[`outputs/chestmnist-metadata-audit-2026-10-26/receipt.json`](../../outputs/chestmnist-metadata-audit-2026-10-26/receipt.json).
It is independently replayable with:

```bash
python3 tools/audit_chestmnist_mapping.py \
  --mapping /path/to/chestmnist_split_info.csv \
  --train-count 78468 --val-count 11219 --test-count 22433 --patient-count 30805
```

## Binding intake consequence

ChestMNIST is no longer blocked on whether patient grouping can be reconstructed. It remains unadmitted and blocked on
label semantics, qualified positive-label QA, image/resize audit, rights/purpose/release review, and cross-source
proximity checks.

Any later development population must be constructed prospectively by patient, not by reusing the wrapper split.
At minimum, every patient touching the wrapper test population must remain excluded from training and adaptive
development, and no patient may cross the newly frozen roles. The exact patient allocation, seed, class policy, and
thresholds must be frozen before label vectors or pixels are opened. Because the 14 findings are text-mined, an absent
label remains unknown rather than a verified negative; this audit does not repair that limitation.

The three crossing patients are evidence against the unchanged split, not permission to inspect test labels or images.
The audit read test identity metadata only and recorded `test_labels_opened = false` and `test_images_opened = false`.
