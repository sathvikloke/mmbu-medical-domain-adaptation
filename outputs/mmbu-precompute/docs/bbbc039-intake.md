# BBBC039 quarantine intake

This intake adds real source-data engineering evidence without clearing any data for challenge training, validation, or model selection. Source eligibility and annotation review remain separate gates. The source registry still grants BBBC039 no allowed purposes. `pending-records.jsonl` deliberately fails the model-use manifest gate.

## Actual execution

The public [BBBC039 version 1 page](https://bbbc.broadinstitute.org/BBBC039) declares CC0 and supplies three archives. The acquisition receipt records URLs, byte sizes, SHA-256 digests and the successful download exit code. This is a bounded public-source inspection authorized by the user's request for non-GPU work, not an acceptance of new access terms. The original archives remain under `work/bbbc039-quarantine/archives` in the parent project, outside the portable code bundle.

Only the 100 names in the supplied **training.txt** were used to open images or masks. The 50 validation and 50 test image/mask contents remain unopened inside the received archives. Metadata names and plate IDs for all partitions were inspected. Filenames beginning `IXMtest` occur in all partitions and are not a split signal.

The command produced 100 byte-preserved native 16-bit TIFFs, 100 byte-preserved annotation PNGs, and one annotation sidecar per field. Sidecars contain component count, area, tight pixel-edge xywh boxes, border flags, source plate, raw hashes and conversion version. The 198 pending question records comprise 100 counts and 98 box sets; two empty masks have no detection record because the empty-box task contract is unresolved. This is a candidate conversion inventory, not an evaluation population or accepted training corpus. No rows may be silently omitted when later defining an evaluation cohort.

## Decoder and geometry

The [source-linked decoder](https://gist.github.com/jccaicedo/15e811722fca51e3ae90e8b43057f075/2dd780afdbde1d5410ed57030a011b2000cfc658) identifies equal nonzero red-channel regions with full two-dimensional connectivity. The local implementation explicitly uses eight neighbors. Disconnected regions of the same red value are separate instances; touching regions of different red values remain separate. It does not threshold all foreground into one class, count unique colors, smooth, or discard small objects.

The actual source masks include opaque RGBA PNGs. The first real run rejected these because the initial contract allowed only RGB; a failing opaque-RGBA regression was added, then support was added with an all-opaque alpha requirement. Transparency (including RGB tRNS metadata), non-8-bit annotation PNGs, and colored pixels with zero red are rejected. Independent adversarial review found and reproduced the tRNS and 16-bit mask gaps; regression tests cover both repairs. Bounds use original 696 by 520 image coordinates, with inclusive pixel extremes converted to xywh widths/heights using +1. No resizing or 16-bit intensity conversion occurs in the prepared records. The earlier RGB-only failure did not publish an output directory.

## Findings that change the plan

- There are **11,999 decoded components**, ranging from 0 to 194 per field. These are software counts of supplied masks, not independently validated biological counts.
- **Two empty masks** require explicit annotation review. Their TIFFs have low dynamic range in the structural previews; this observation does not certify a zero-nucleus target.
- **1,997 components touch the image border**. A nucleus inclusion/counting policy must be written before constructing final targets.
- **429 components occupy fewer than 25 pixels**, across 92 images. They were retained. The source repository's training-specific size filter must not silently become a ground-truth rule.
- The training partition covers **20 plates**, and all 20 have metadata entries in other source partitions. Preserving official splits supports source comparisons but does not establish independence by plate. A plate holdout design would need to be defined separately without moving or consuming the protected source test images.

`evidence/bbbc039-review-queue.csv` contains all 100 fields with mechanical flags and pending review status. Counts, source coverage and flags should guide manual review, not become automated medical label approval. The sample contact sheet is a structural check only: its eight selected views cover both empty masks, the lowest nonzero count, intermediate ranks and the two highest counts. It uses documented per-image native-min/max scaling for display and downsampling; those previews are not training input or a finalized model preprocessing policy.

## Reproduce offline after obtaining the official archives

With the optional Pillow dependency and from the package directory:

```sh
PYTHONPATH=src python3 -m mmbu_prep prepare-bbbc039 /path/to/archives --output /path/to/new-quarantine-directory
PYTHONPATH=src python3 -m mmbu_prep inspect-images /path/to/new-quarantine-directory/pending-records.jsonl --image-root /path/to/new-quarantine-directory
```

The second command is structural image inspection only. It cannot authorize these pending records. `prepare-bbbc039` refuses an existing output path, checks archive entry paths/duplicates/declared size limits, matches metadata populations, and publishes only after every selected field passes. It never executes archived code or the bundled CellProfiler pipeline. Downloading remains a separate explicit action; the CLI makes no network requests.

See `bbbc039-source-audit.md` for pinned primary-source semantics and overlap cautions. No MMBU public/hidden examples were used for this conversion, and no model or learned preprocessing was run. This does not establish absence of overlap with MMBU or pretraining corpora.
