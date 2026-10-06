# Independent optional-image inspection review

Review date: 2026-10-04 UTC. Reviewer: the contracts/comparison worker, who did not author the image module, its tests or its documentation. Scope: `src/mmbu_prep/images.py`, `tests/test_images.py`, `docs/image-inspection.md`, the actual optional Pillow runtime and independent synthetic counterexamples. No image implementation changes were made by this reviewer. Temporary probe files were automatically removed; this report is the only persistent artifact written for the image review.

**Initial verdict: changes requested for one reproduced P2 precision-boundary defect.** The ordinary file/path/decoder safeguards and the deliberately narrow duplicate definition are supported by the examined code and tests. This is not a security audit of Pillow or approval of real biomedical images, source rights, labels, geometry intent or scientific grouping.

## IMG-001 — P2: allowed PPM variants can lose precision or rescale samples before hashing

Locations in the reviewed snapshot: `images.py:18`, `48–60`, `132–144`.

The Pillow format name `PPM` covers several portable-map formats. `_file_bits` does not inspect their sample-depth/range header, so the inspector emits `file_bit_depth_unavailable` and continues to load/hash. Pillow's decoder can then reduce RGB data from 16 bits to 8 or rescale grayscale values without changing the advertised decoded mode/dimensions. The existing post-load mode check does not detect either operation. This bypasses the otherwise explicit precision-reduction guard and conflicts with the no-rescaling contract.

Independent reproduction with real local files and Pillow 12.3.0:

```python
import struct

# Two different 16-bit RGB sample arrays; neither file is an 8-bit source.
first = b"P6\n1 1\n65535\n" + struct.pack(">3H", 256, 0, 65535)
second = b"P6\n1 1\n65535\n" + struct.pack(">3H", 257, 0, 65535)

# A noncanonical grayscale range whose values the decoder rescales.
gray = b"P5\n2 1\n1023\n" + struct.pack(">2H", 1, 1023)
```

Write these bytes as `.ppm`/`.pgm` files in a temporary directory, build records with real SHA-256 hashes and the required ID/source/split/path fields, and call `inspect_images(records, image_root=directory)`.

Observed:

- Both P6 sources decode to mode `RGB`, pixel `(1, 0, 255)`. Their raw red values 256 and 257 become indistinguishable. A single P6 record returns `ok: true`, no errors, `file_bits_per_sample: null`, `decoded_bits_per_sample: 8`, and a nonnull pixel digest.
- Both P6 records receive digest `d2c51f6e8884ab3de1cf42cd3869e80257aa0e5f7d1abf4a96ca703641098f7a`. Across `train`/`dev`, they generate `decoded_split_leakage`; the underlying source-sample difference has already been lost. This hash equality is true of Pillow's reduced outputs, but is not the intended preservation of original sample precision.
- The P5 source decodes to mode `I` with values `[64, 65535]`, although its stored values are `[1, 1023]`. Inspection returns `ok: true`, null source depth, 32-bit decoded storage, and a `high_bit_depth` warning stating that samples were retained. An increase in storage width does not establish that sample values were preserved.

The installed primary Pillow code was also inspected: `PpmImageFile._open`, `PpmDecoder.decode`, and `PpmPlainDecoder._decode_blocks` explicitly select scaling paths for these ranges. The format plugin accepts P1–P6 and additional `Pf`, `P0CMYK`, `PyP`, `PyRGBA`, and `PyCMYK` variants; the format name alone is not an adequate preservation contract. `Pf` also selects a bottom-up raw layout and carries scale metadata. These observations use the actual installed library implementation, not a recalled API assumption.

Suggested correction: define a reviewed portable-map subset, parse the relevant magic/header/depth/range before loading pixels, and reject precision-reducing or sample-rescaling cases before issuing a pixel digest. Fail closed for unreviewed variants. At minimum, add regressions for adjacent 16-bit P6 samples, noncanonical P5/P2 ranges, and continued acceptance of the package's ordinary byte-range engineering fixtures. Supporting additional variants is optional; no automatic conversion is needed.

The finding was sent to the implementing image worker and root with the exact byte reproductions. Repair and independent closure, if completed, should be appended below rather than erasing this historical finding.

## Independently supported behavior

- **Read-only byte snapshot:** actual file hashes before and after inspection of integer/float fixtures were identical. The code reads a bounded immutable byte snapshot, and both manifest hash comparison and decoding use that snapshot. It does not rewrite files or annotations.
- **Lossless duplicate detection:** two RGB PNG files with identical samples but compression levels 0 and 9 had different raw SHA-256 values and the same decoded digest. A train/confirmation pair produced `decoded_split_leakage`, as intended. Different encodings do not evade this exact-sample check.
- **Floating sample identity:** two mode-F TIFF fixtures differing only in NaN payload bits (`0x7fc00000` versus `0x7fc00001`, alongside the same 1.0 sample) produced different digests, remained mode F with 32-bit file/decoded depth, and reported no duplicate group. The digest's integer-byte serialization preserved the distinction without numerically normalizing NaNs.
- **Path confinement:** lexical traversal/absolute/Windows/NUL checks precede reads, and resolved paths must remain below the resolved root. Existing symlink-escape tests pass. The docs accurately state that this is not protection against a concurrent adversary changing the tree after resolution.
- **Decoder and size boundary:** encoded-byte and declared-pixel ceilings, Pillow bomb-warning promotion, multi-frame rejection, format allowlisting and rejection of permissive truncated-image configuration are present. No external conversion command is invoked. The docs do not promise a process memory budget, CPU timeout, or immunity to decoder defects.
- **Supported depth/orientation checks:** existing 16-bit TIFF sample preservation, 16-bit RGB PNG reduction rejection, and TIFF nonidentity-orientation rejection tests pass. The code rejects known loss before a digest is emitted. PNG orientation is reported without changing the stored pixel coordinates. This supported behavior is why the portable-map bypass is consequential.
- **Duplicate semantics:** mode/bands/dimensions, pixel bytes, palette and transparency representations contribute to identity. Cross-source matches are considered. Orientation, ICC/gamma and rendered appearance are explicitly outside the digest contract, with separate orientation/ICC evidence. The absence of a digest match is not claimed to establish perceptual uniqueness or patient independence.
- **Failure accounting:** per-record errors are preserved; a decoded image with a stale manifest hash still participates in duplicate detection while the overall report remains failed. Cross-split group failures can coexist with individually successful decoding; the docs describe this distinction.
- **Dependency boundary:** Pillow remains a lazy optional import. Missing-dependency behavior is tested without site packages. No package installation, network access, downloaded biomedical sample or model execution was used in this review.

## Executed tests and probes

Runtime: bundled Python 3.12.14, Pillow 12.3.0. Working directory: package root.

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /Users/sathvikloke/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m unittest discover -s tests -p test_images.py -v

Ran 22 tests in 0.101s
OK
process exit_code: 0
```

The independent counterexample/probe scripts also exited 0 after recording the outcomes above. The first probe used Pillow's deprecated `getdata()` only to print observed pixels; its deprecation warnings were unrelated to production inspection. No output or exception was suppressed to turn a failure into a pass. Passing existing tests did not cover IMG-001.

## Reviewed snapshot SHA-256

```text
35c3c6952f756800668a4825771d5ea33f3511f16d67df15dec8c72668c3bc73  src/mmbu_prep/images.py
eee6dff026673aefb897c193dd67c6c003cda3e60d92492200e9ed9335bae8f0  tests/test_images.py
61b27b751540404d9349f2a453f257b88d3516e94c5209c54e474d55e6573ada  docs/image-inspection.md
```

## Scoped repair closure

**Current disposition: IMG-001 is closed; no identified defect remains open in this scoped image review.** The original reproduction and snapshot above remain historical evidence. The implementing image worker made the repair; this reviewer inspected it and independently reran the counterexamples and affected behavior.

The image module now parses a bounded portable-map header before opening a P-prefixed payload with Pillow. Only binary P5/P6 with `maxval == 255` are admitted. Noncanonical/high ranges fail with `pnm_requires_conversion`; unreviewed magic variants fail with `unsupported_pnm_encoding`. The header has a 64 KiB bound, validated positive dimensions, bounded ASCII numeric tokens, and a decoded-dimension consistency check. The report includes `pnm_maxval` and established byte sample depth. The original payload is not modified.

Independent closure results:

```text
16-bit P6, red 256: pnm_requires_conversion
16-bit P6, red 257: pnm_requires_conversion
P5 maxval 1023 with values [1,1023]: pnm_requires_conversion
Pf float variant: unsupported_pnm_encoding

All four pixel_sha256 values: null
Decoded count: 0
Duplicate groups: []
Verification script exit_code: 0
```

The same bundled-runtime image-test command was rerun independently:

```text
Ran 26 tests in 0.108s
OK
process exit_code: 0
```

The shipped synthetic fixtures were also exercised through the actual CLI:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  /Users/sathvikloke/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m mmbu_prep inspect-images examples/engineering-manifest.jsonl --image-root examples

exit_code: 0
ok: true
records: 5; files_read: 5; decoded: 5; duplicate_groups: 0
decoded modes: [L, L, L, L, L]
pnm_maxval: [255, 255, 255, 255, 255]
raw fixture SHA-256 values unchanged: true
```

The implementer's `images-pnm-red.txt` was inspected and records six failing regression cases before repair; `images-pnm-green.txt` records 26 passing tests after repair. Those are implementation receipts; the 26-test rerun, direct byte counterexamples and CLI fixture checks above are this reviewer's independent evidence.

Repaired snapshot SHA-256:

```text
2b6fd50003d659204806b354f5da2a1502bc85a7a8dde9f5b6475bde65b58b51  src/mmbu_prep/images.py
1bc8525d1ded178709d732925af47acb973b94630850618defb970594600da38  tests/test_images.py
a0baaa21c24055d429d929e1558605cd168f407a6d942b5d1fc12454d855b4a1  docs/image-inspection.md
```

The restricted PNM subset is an intentional limitation, not a conversion service. The earlier limits remain: no perceptual-duplicate guarantee, hostile-concurrency sandbox, decoder vulnerability audit, source approval, biomedical label/geometry review, or inference readiness claim.
