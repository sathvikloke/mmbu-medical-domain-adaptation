# BBBC039 source audit

Checked 2026-10-04. This bounded audit covers public documentation, source code, and filename/plate metadata. It is not a scientific performance audit or approval to train. Machine-readable retrieval hashes, metadata checks, and five original synthetic decoder probes are in [the evidence ledger](../evidence/bbbc039-source-research.json).

Quarantined intake is defensible while MMBU eligibility is unresolved, provided it remains a separate, unapproved inventory. The source card supplies CC0 rights evidence; competition eligibility and overlap are separate questions. Keep the registry's real-source purposes empty until reviewed. A real dataset must not be relabeled as the synthetic `engineering_only` category. Do not publish training-ready manifests or open source validation/test labels during this intake. This conclusion is a conditional workflow judgment, not an organizer ruling.

## Canonical decoding: resolved

**BBBC039-01 — high confidence, mandatory conversion control.** The [officially linked decoder gist, revision `2dd780afdbde1d5410ed57030a011b2000cfc658`](https://gist.github.com/jccaicedo/15e811722fca51e3ae90e8b43057f075/2dd780afdbde1d5410ed57030a011b2000cfc658), takes channel zero and labels its equal-valued connected regions. The [UNet4Nuclei preprocessing](https://github.com/carpenterlab/unet4nuclei/blob/5575e611f06abe2af97ccb50ba7b777f2c6b0cad/unet4nuclei/01-preprocessing.ipynb) and [evaluation](https://github.com/carpenterlab/unet4nuclei/blob/5575e611f06abe2af97ccb50ba7b777f2c6b0cad/unet4nuclei/04-evaluation.ipynb) use the same operation.

The historic [scikit-image v0.13.1 label implementation](https://github.com/scikit-image/scikit-image/blob/03f4997359e9d439db9709fb359d7b9c0ea38556/skimage/measure/_label.py) specifies zero background and full dimensional connectivity; [morphology imports that function](https://github.com/scikit-image/scikit-image/blob/03f4997359e9d439db9709fb359d7b9c0ea38556/skimage/morphology/__init__.py). Thus the explicit 2D contract is channel zero, integer-value equality, background zero, and **8-connectivity**. A modern explicit expression is `measure.label(red, background=0, connectivity=2)`. The original author's package version is unpinned; this historic release and [current documentation](https://scikit-image.org/docs/stable/api/skimage.measure.html#skimage.measure.label) agree on these defaults.

| First-channel example | Correct instance count | Mistake exposed |
| --- | ---: | --- |
| `[7, 0, 7]` | 2 | Counting distinct colors merges disconnected reuse. |
| `[7, 8]` | 2 | Thresholding to binary joins touching unequal labels. |
| `[[7, 0], [0, 7]]` | 1 | Four-neighbor connectivity splits a diagonal component. |
| All zero | 0 decoded components | This alone does not prove an annotated negative. |

Do not infer background from full-RGB black/white appearance, apply a grayscale luminance transform, or assume globally unique RGB colors. Unexpected mask modes, transparency, or channel inconsistencies need explicit handling and review. These are defensive controls, not defects observed in source labels; no source pixels were inspected in this research pass.

## Preserve metadata and original targets

**BBBC039-02 — high confidence.** Direct checks of the [official metadata archive](https://data.broadinstitute.org/bbbc/BBBC039/metadata.zip) found 100 training, 50 validation, and 50 test filenames, internally unique and pairwise disjoint. Their union has 200 names. All begin `IXMtest`; the prefix does not identify the split. Lists use `.png`, so match raw TIFF and mask names by a verified one-to-one stem rule.

`filenames_and_plates.csv` has **no header**: 200 filename/plate rows map exactly to the partition union and cover 20 BBBC022 plates. Use `csv.reader` with `newline=''`; do not consume its first image as a header. Training/validation/test cover 20/20/18 plates, respectively, so these are not plate-disjoint splits. Preserve source partition, original basename, plate mapping, archive/member hashes, and transformation version. Keep well/site tokens as provenance if parsed; do not invent patient or independent-study identities from them.

**BBBC039-03 — high confidence.** The pinned [UNet configuration](https://github.com/carpenterlab/unet4nuclei/blob/5575e611f06abe2af97ccb50ba7b777f2c6b0cad/examples/bbbc039_seg_config.py) sets minimum nucleus area to 25 pixels. Its preprocessing removes smaller regions and produces three-channel background/interior/boundary targets. Those derived targets are not the unfiltered instance annotation used by the evaluation notebook. Intake counts and boxes should originate from canonical unfiltered instances. Preserve small and border-touching regions, record their flags, and quarantine empty masks for annotation review instead of silently treating them as verified zero-nucleus examples.

For an instance occupying pixel coordinates, retain the tight integer half-open box `[min_x, min_y, max_x + 1, max_y + 1]`. Source arrays are row/column; model boxes are x/y. Preserve the original image frame and any later affine mapping. Do not interpolate instance labels or substitute boundary masks for original masks.

**BBBC039-04 — high confidence.** UNet preprocessing clips image intensities to per-image 0.1/99.9 percentiles and writes 8-bit PNG. This is a lossy training recipe. Retain original 16-bit TIFF bytes; any preview should document its display transform, constant-image handling, dimensions, and source hash. Display RGB replication must not be represented as three acquired channels.

## Provenance, rights, and limits

**BBBC039-05/06 — high confidence for source facts; MMBU eligibility unresolved.** [BBBC039v1](https://bbbc.broadinstitute.org/BBBC039) consists of 200 U2OS fluorescence fields, 520×696 pixels, sampled from BBBC022, with manually annotated nucleus masks and a CC0 waiver. Some images overlap BBBC038. This is nucleus-instance supervision, not clinical lesion or cell-subtype ground truth. The [BBBC022 card](https://bbbc.broadinstitute.org/BBBC022) independently identifies its 200-image annotated subset. Preserve plate lineage and screen BBBC022/BBBC038 derivatives together before eventual cross-source partitioning. [BBBC038](https://bbbc.broadinstitute.org/BBBC038) also has multiple public annotation variants; a renamed/reannotated image remains related.

No LICENSE/COPYING file was visible in the pinned UNet repository tree; the gist exposes only its example file. The dataset waiver should not be generalized to repository code. This is an unresolved code-license observation, not a rights-violation finding. Document the decoder behavior and implement independently or establish reuse rights before copying substantive upstream code.

The strongest counterargument to quarantine is that unknown benchmark overlap can still bias future decisions if images influence tuning. Constrain this stage to deterministic conversion and engineering QA of source-training material; keep source-heldout labels unopened and retain a review gate before model use. Filename disjointness does not establish perceptual independence, source correctness, or absence from MMBU. No model, image/mask archive, gated material, or heldout labels were downloaded by this auditor; only public code/docs and the 17,816-byte metadata archive were read. The linked bioRxiv page returned 403 and was not used as evidence.

The three highest-value controls are: pin and test the equal-value 8-connected decoder; preserve explicit partitions and headerless plate lineage; and keep unfiltered targets plus original 16-bit imagery quarantined until eligibility and annotation review are complete.
