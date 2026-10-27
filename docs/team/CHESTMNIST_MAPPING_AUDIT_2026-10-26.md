# ChestMNIST public-mapping audit

**Date:** October 26, 2026

**Decision:** the patient key is recoverable, but the published wrapper split is not patient-disjoint and must not be
used unchanged for decision-bearing development. The NIH-published patient-level train/test boundary must govern.

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

## NIH split reconciliation

The official NIH repository also publishes a 72,223-byte FAQ, an 86,524-image `train_val_list.txt`, and a
25,596-image `test_list.txt`. The FAQ says usage is unrestricted with attribution and citation, describes the NLP
labels as imperfect, warns that “No finding” is not “normal,” and says the two NIH lists are patient-level disjoint.
The exact lists contain 28,008 and 2,797 patients respectively, with zero patient overlap. Together they cover the
same 112,120 image IDs as the MedMNIST mapping.

The MedMNIST wrapper roles do not preserve that official boundary:

| MedMNIST role | NIH train/validation images | NIH test images |
| --- | ---: | ---: |
| train | 60,549 | 17,919 |
| validation | 8,754 | 2,465 |
| test | 17,221 | 5,212 |

This supersedes the narrower “three crossing patients” interpretation. Those three are crossings among wrapper roles;
the larger scientific problem is that the wrapper roles mix NIH's official development and held-out populations.

## Binding intake consequence

ChestMNIST is no longer blocked on whether patient grouping can be reconstructed. It remains unadmitted and blocked on
label semantics, qualified positive-label QA, image/resize audit, rights/purpose/release review, and cross-source
proximity checks.

Any later development population must start only from NIH's official 86,524-image train/validation population and be
constructed prospectively by patient. All 25,596 official NIH test images and their 2,797 patients remain excluded
from training and adaptive development. The exact patient allocation, seed, class policy, and
thresholds must be frozen before label vectors or pixels are opened. Because the 14 findings are text-mined, an absent
label remains unknown rather than a verified negative; this audit does not repair that limitation.

The repository now enforces this boundary with `tools/compile_chestmnist_development.py`. It accepts the exact mapping,
the two official NIH lists, and a separately frozen `patient_id,role` CSV. The compiler requires complete one-time
coverage of every official train/validation patient across only `train` and `adaptive_development`, rejects test
patients and population drift, and emits each retained image's exact MedMNIST array location. It never chooses a split
ratio, opens labels or pixels, admits the source, or grants model-use authority. This separation prevents an operator
from accidentally treating MedMNIST's wrapper role as the scientific role.

```bash
python3 tools/compile_chestmnist_development.py \
  --mapping /path/to/chestmnist_split_info.csv \
  --official-train-val /path/to/train_val_list.txt \
  --official-test /path/to/test_list.txt \
  --patient-roles /path/to/frozen-patient-roles.csv \
  --output /new/path/chestmnist-development-manifest.json
```

The three crossing patients are evidence against the unchanged split, not permission to inspect test labels or images.
The audit read test identity metadata only and recorded `test_labels_opened = false` and `test_images_opened = false`.

## Executed successor

The label-blind patient allocation described above was executed once on the exact audited metadata and is retained in
the [ChestMNIST development freeze](CHESTMNIST_DEVELOPMENT_FREEZE_2026-10-26.md). It assigns 25,207 patients / 77,786
images to training and 2,801 patients / 8,738 images to adaptive development while excluding all 2,797 NIH test
patients / 25,596 images. This closes split selection only; ChestMNIST remains unadmitted and no label or pixel was
opened.
