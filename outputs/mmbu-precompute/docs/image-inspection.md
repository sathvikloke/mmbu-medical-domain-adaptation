# Optional image inspection

`mmbu_prep.images` inspects actual local image files and reports exact decoded-representation duplicates. It reads files without modifying them. A successful inspection is not source approval, training eligibility, label review, biomedical annotation QA, or a perceptual-duplicate clearance. Run the manifest/provenance validator separately.

## API and dependency

```python
inspect_images(
    records,
    *,
    image_root,
    max_pixels=40_000_000,
    max_file_bytes=67_108_864,
) -> dict
```

The module imports only the standard library until this function runs. It lazily imports Pillow and returns a structured `dependency_unavailable` error if Pillow is absent. It never installs packages. This implementation was tested with Python 3.12.14 and Pillow 12.3.0 in the bundled runtime; the standard-library-only Python environment can still import the module and run the dependency-boundary tests.

`records` must be a nonempty list of objects. Each record requires nonblank `record_id`, `source_id`, `split`, and `image_path`, plus a 64-character lowercase hexadecimal `image_sha256`. Record IDs must be unique. Splits are `engineering`, `train`, `dev`, `confirmation`, or `official_dev`; their names identify collision boundaries but do not grant permission. The inspector does not consult or alter source review status.

`image_width` and `image_height` are optional. If supplied, both must be positive integers excluding Boolean and must match the decoded dimensions. If neither is supplied, `dimensions_unrecorded` warns that there is no manifest dimension claim to compare. Measured dimensions appear only in the report; no manifest field is invented or repaired.

## File and resource boundary

`image_root` must resolve to an existing directory and defines the source-file boundary for the invocation. Paths must use relative POSIX syntax with no absolute path, Windows drive prefix, backslash, NUL, or `..` component. Resolved paths, including symlinks, must remain under the resolved root. Missing, unreadable, nonregular, or escaping paths fail individually, so the report preserves other records' findings.

Files larger than `max_file_bytes` fail before parsing. A bounded read creates an immutable in-memory byte snapshot; both the raw hash and decoder operate on that same snapshot. The read repeats the byte-limit check to cover growth after the initial file-size check. The tree must remain stable while files are opened: this path check is not an OS-level sandbox against a concurrent adversary replacing directories or symlinks.

The format allowlist is PNG, JPEG, TIFF, BMP, GIF, WEBP, and a restricted PNM subset reported by Pillow as PPM: only binary P5 grayscale or P6 RGB with maxval exactly 255. A bounded 64 KiB header parser checks the PNM magic, dimensions, and maxval before Pillow is invoked. ASCII PNM, bitmap variants, high-depth PNM, nonstandard maxval, floating PFM, and Pillow's extended PNM variants are rejected. Other formats are rejected without invoking external delegates. DICOM, microscopy container stacks, EPS, PDFs, and other formats require a separately reviewed conversion path. No such conversion is implemented here.

The inspector checks declared dimensions before loading pixels, rejects counts above `max_pixels`, preserves Pillow's own global bomb threshold, and treats Pillow's decompression-bomb warnings as errors. It rejects an environment with `ImageFile.LOAD_TRUNCATED_IMAGES` enabled. Both configured limits must be positive integers excluding Boolean. Limits bound ordinary compressed input and pixel allocation; they do not guarantee a process memory budget, CPU timeout, or immunity to decoder defects. Encoded bytes, decoded storage, and digest serialization can coexist in memory.

Pillow opens image files lazily, so merely reading a header is insufficient. Inspection verifies supported format integrity, reopens the snapshot, and calls `load()` to decode pixels. PNG EXIF access can itself consume the stream, so verification runs before that access. See the official [file lifecycle documentation](https://pillow.readthedocs.io/en/stable/reference/open_files.html) and [image API](https://pillow.readthedocs.io/en/stable/reference/Image.html). Pillow's [security guidance](https://pillow.readthedocs.io/en/stable/handbook/security.html) describes the remaining decoder/resource boundary.

## Report contract

The return value contains:

| Field | Meaning |
|---|---|
| `ok` | True only when no errors occurred |
| `errors`, `warnings` | Structured `code`, `message`, and applicable zero-based record index/ID or group details |
| `counts.records` | Submitted records, including malformed rows |
| `counts.files_read` | Successfully obtained byte snapshots, counted per record |
| `counts.decoded` | Records completing verification, decoding, and pixel hashing, even if the manifest hash or dimensions disagree |
| `counts.duplicate_groups` | Number of exact decoded-representation groups with at least two records |
| `images` | One ordered entry per input record when configuration/dependency validation succeeds |
| `duplicate_groups` | Stable groups sorted by pixel digest, with sorted member IDs, source IDs, splits, and raw hashes |
| `pixel_digest_version` | `pillow-decoded-representation-v1` |
| `pillow_version` | Decoder version used, or null if unavailable |

Each image entry contains its source/record/split/path identity, per-file `ok`, `raw_sha256`, `pixel_sha256`, `width`, `height`, `format`, `mode`, `frames`, `decoded_bits_per_sample`, `file_bits_per_sample`, `pnm_maxval`, `exif_orientation`, `orientation_requires_transform`, and `icc_profile_sha256`. `pnm_maxval` is null outside a parsed P5/P6 header. Properties unavailable after a failure remain null. Full EXIF, patient metadata, or ICC contents are not copied into the report. Per-file `ok` concerns that file's checks; a later cross-split duplicate error can make the overall report fail while individual files decoded correctly.

Actual raw hashes are retained even after decode, manifest-hash, or dimension failure, provided the bounded file read succeeded. A successfully decoded image with a manifest mismatch still participates in duplicate detection; the overall report remains failed. This avoids hiding leakage just because a manifest hash was stale.

## Precision, orientation, and frames

`decoded_bits_per_sample` describes Pillow's mode storage, not the effective scientific dynamic range. PNG's IHDR, TIFF's BitsPerSample tag, and JPEG's declared bit depth supply file sample-depth evidence where available. GIF/WEBP use their 8-bit decoded sample representation. Unsupported source-depth introspection is reported as null with `file_bit_depth_unavailable`; it is not inferred from a filename.

Known file depth greater than decoded storage depth fails with `decoder_precision_reduction`. For example, Pillow can decode a 16-bit-per-channel RGB PNG into 8-bit RGB; this module refuses to issue an exact pixel digest for that reduction. PNM needs a stronger gate: Pillow can reduce 16-bit RGB P6 samples to 8 bits or rescale P5 samples when maxval is not 255. Those inputs fail with `pnm_requires_conversion` before decoding, even when decoded storage has enough bits. The reviewed byte-valued P5/P6 subset has declared depth 8 and preserves the shipped engineering PGM fixtures. Native 16-bit grayscale TIFF is retained and flagged `high_bit_depth`. Signed integer and floating modes remain in their decoded modes; no range scaling, windowing, quantization, clipping, RGB conversion, or 8-bit normalization is performed.

Nonidentity EXIF orientation is reported without applying rotation or mirroring. Pillow 12.3.0 automatically applies TIFF orientation during loading; therefore TIFF orientation 2–8 fails before that load, with `decoder_orientation_transform`, and receives no pixel digest. PNG/JPEG orientation flags can remain untransformed. Invalid orientation values fail rather than being guessed. A separate, reviewed conversion would be needed to change pixels and update geometry.

Any multi-frame image fails with `multiple_frames`. The inspector reports the frame count and does not treat the first frame as the image. It does not validate every rejected frame or infer a clinically meaningful frame selection.

## Exact decoded-representation identity

The pixel digest is SHA-256 over three length-prefixed parts: a canonical JSON header, complete palette bytes if present, and complete decoded pixel bytes. The header includes a version, dimensions, Pillow mode and bands, serialization byte order, palette mode/raw mode, and typed transparency metadata. Native 32-bit integer/float sample bytes are serialized in big-endian order without changing sample values or float bit patterns; native 16-bit mode uses the same byte-order rule. Explicit-endian modes retain their mode-defined storage. Different Pillow modes remain distinct even when rendering might look identical.

Thus a match means equal declared decoded dimensions/mode/bands, equal decoded sample bytes under this serialization, and equal complete palette and transparency representation. It does not mean equal encoded files: PNG and BMP containers can produce the same digest. It also does not mean equal rendered appearance. EXIF orientation, ICC profiles, gamma/display metadata, captions, filenames, and compressed container details are excluded. Orientation and ICC evidence are reported separately, and differing orientation among matching samples generates an additional warning. Palette differences, even in unused entries, can prevent a match; this conservative identity test is narrower than visual equivalence.

Same-split duplicates produce a warning; exact decoded matches across any split names produce `decoded_split_leakage`, including matches across source IDs. Images rejected for multiple frames, precision reduction, or required TIFF orientation receive no pixel digest and cannot silently join a successful group. Groups are stable under record reordering.

No resizing, crop matching, near-duplicate search, perceptual hashing, registration, color normalization, or semantic comparison is implemented. Re-encoded lossy images can have different decoded samples and escape this check. Shared patient/slide/study lineage remains a separate manifest grouping requirement. Absence of a matching digest is not evidence of independent images or patients.

## Verification

`tests/test_images.py` creates tiny synthetic local fixtures for real decoding, raw/dimension mismatches, path escape, corruption and truncation, oversized headers, decompression warnings, palettes/transparency, 16-bit values, precision loss, orientation, multi-frame rejection, cross-encoding equality, and different pixels with the same shape. Tests for optional dependency behavior run without site packages. No downloaded image or biomedical label is used as a unit-test oracle.

The initial red and green receipts are `evidence/images-red.txt` and `evidence/images-green.txt`; the system-runtime result is recorded separately. Independent review found the PNM precision gap; `evidence/images-pnm-red.txt` reproduces it and `evidence/images-pnm-green.txt` records the 26-test suite after the restricted P5/P6 fix. These receipts preserve the exact interpreter, command, output, and exit code. Historical batch-1 receipts are unchanged.
