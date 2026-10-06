# ROCO image-backed quarantine sample

Twenty-four images from the pinned ROCOv2 release 2.0.1 source-training partition are now available locally for engineering and expert review: four images for each of six manually supplied modality classes, from 24distinct PMC articles. The selection is deterministic from seed 1729, exact published metadata, and a CC BY attribution-prefix filter. That filter is not model-use clearance. The aggregate dataset declares CC-BY-NC-4.0; article-level licenses and image-specific exceptions remain separate evidence.

The first range acquisition timed out and published no output. A bounded retry received 15,007,890 HTTP body bytes, including repeated/archive-index ranges, to recover 1,395,076 bytes of selected JPEG payload. Every selected member passed ZIP CRC and has an individual SHA-256. The whole 4,611,440,786-byte archive was not downloaded and its publisher MD5 was not verified. Both the failure and final acquisition receipt are retained.

`tools/prepare_roco_sample.py` recreates the image-backed sample from local pinned metadata, the acquired JPEGs and their receipt. It checks the exact 24-ID selection, source hashes and sizes, preserves original JPEGs, and writes a new directory atomically. It makes thirteen RGB8 identity presentations and eleven grayscale8 channel-replicated RGB PNGs. Dimensions remain unchanged, ranging from 195–800 pixels wide and 263–845 pixels high. Decoding and exact duplicate checks pass. No crop, resize, intensity window, OCR, model or biomedical judgment is applied.

From the project root:

```sh
/your/pillow/python outputs/mmbu-precompute/tools/prepare_roco_sample.py \
  --metadata work/source-expansion \
  --acquired work/roco-quarantine/acquired \
  --receipt outputs/mmbu-precompute/evidence/roco-image-acquisition.json \
  --output work/roco-quarantine/reproduction
```

Current local files are in `work/roco-quarantine/prepared`; the contact sheet is `work/roco-quarantine/qa/contact-sheet.png`. Raw images are deliberately outside the portable code bundle. `source-metadata.json` preserves the earlier metadata-only inventory snapshot unchanged, including its then-current unresolved flags; `presentations.json`, `image-inspection.json`, the pending manifest, and the separate article-rights report supply subsequent evidence. Original figure IDs from caption matching remain in that separate report; the pending manifest conservatively leaves them null.

The root assistant visually inspected the 24-thumbnail contact sheet for structural presentation. All tiles visibly contain images, but several include arrows, labels, acquisition text, colored overlays or photograph/tint artifacts. In particular, train_036451 contains dense acquisition text, train_055358 contains a printed finding label, and train_046920 contains a visible bottom annotation bar. These are review observations, not a privacy clearance, medical-label validation, or instruction to remove pixels. Potential shortcuts and any embedded identifiers need a deliberate source/use decision before optimization. The supplied images and proposed modality labels were not altered in response.

`evidence/roco-review-queue.csv` provides 24 unanswered review rows. A suitable reviewer must decide whether each proposed modality is supported, whether the panel/label semantics are appropriate, and whether source presentation and rights are acceptable. `context={}` explicitly means no image-supported context labels were approved; it is not a scored zero-context example. The stored `split=train` preserves the source partition and does not grant training permission. Every record stays pending, every real source has zero allowed purposes, and the model-use validator must reject these records until those separate gates are satisfied.

Source crossovers are handled at article level: the metadata audit found 12,078 ROCO-training PMCIDs also present in PMC-VQA training. Keep the shared `pmc-literature:PMCID` grouping across both sources. Neither this sample nor its hashes establish absence of hidden benchmark overlap.
