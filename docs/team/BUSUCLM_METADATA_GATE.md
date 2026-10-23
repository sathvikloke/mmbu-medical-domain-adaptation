# BUS-UCLM v3 metadata gate

**Observed:** October 23, 2026
**Evidence:** [`outputs/BUSUCLM-metadata-gate-2026-10-23.json`](../../outputs/BUSUCLM-metadata-gate-2026-10-23.json)
**Decision:** inventory and patient grouping close; schema and license clearance fail; model use remains unapproved

## Authority and bounded access

The authoritative [Mendeley Data v3 record](https://data.mendeley.com/datasets/7fvgj4jsp7/3) identifies DOI
`10.17632/7fvgj4jsp7.3`, publication date January 27, 2025, and CC BY 4.0. Its current public download endpoint resolves
to a `336713241`-byte ZIP with ETag `"66fea5503ae433b324be1cbf54ca8866"`, last modified January 27, 2025, and S3
version ID `OtNyHu6R84RS3_v.5.KA6bykStLQaxxw`. ETag is recorded as an HTTP validator, not asserted to be an official
dataset checksum.

The gate used bounded HTTP ranges to read the ZIP central directory and the single 26,469-byte `INFO.csv` member.
It received 2,217,497 bytes for the selected-member extraction and verified the member CRC. No image or mask body was
opened, extracted, or decoded. The archive inventory contains exactly 1,367 ordinary files with 337,879,300 total
uncompressed bytes: one metadata table, 683 images, and 683 same-named masks.

## Structural result

The semicolon-delimited UTF-8-with-BOM metadata has exactly these columns:

`Image;Resolution;Label;Doppler;Marks;Combined`

All 683 image names are unique canonical `{PATIENT}_{INDEX}.png` names. Their four-letter prefixes yield exactly 38
patient groups, matching the dataset paper and repository description. Metadata, image names, and mask names close
exactly with no missing, extra, or duplicate member. Every row declares `856x606`.

The image-level label totals match the publication:

- 419 normal;
- 174 benign; and
- 90 malignant.

Patient grouping must precede any future split. Thirty-three of 38 patients contain more than one image-level label:
18 have benign and normal images, 10 have malignant and normal images, and 5 contain benign, malignant, and normal
images. A patient's records may never be separated or assigned by label.

## Recorded defects and restrictions

Schema clearance fails because one Doppler-positive row uses `Y` while 36 use `Yes`; all 646 negative rows use `No`.
The gate preserves this as a source anomaly rather than silently normalizing it. The table also identifies 154 images
with visual marks and 6 combined images. These fields require prospective, patient-grouped handling; they cannot be
filtered after observing model performance.

License clearance also fails. The Mendeley v3 record and the authors'
[repository README](https://github.com/noeliavallez/BUS-UCLM-Dataset/blob/main/README.md) say CC BY 4.0, but the same
repository's [LICENSE.md](https://github.com/noeliavallez/BUS-UCLM-Dataset/blob/main/LICENSE.md) says CC BY-NC 4.0.
The repository README points readers to that contradictory file. Only the authors or repository authority can resolve
which terms govern the dataset and trained-weight use; this project will not infer the more permissive answer.

## Honest readiness effect

This gate closes the exact v3 archive inventory, metadata schema, patient grouping, label totals, and image/mask name
joins. It does not establish decoder behavior, mask colors, annotation completeness, pixel privacy, duplicates,
cross-source/MMBU proximity, medical correctness, allowed derived tasks, or trained-weight release compatibility.

Receipt digest: `2b3bf668bb89c379633cf2e6db54e5f9a61325300c45da7318091bd9f85a5538`.
The receipt remains `schema_clearance=false`, `training_ready=false`, and `model_use_authorized=false`.
