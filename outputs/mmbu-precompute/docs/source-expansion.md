# Source expansion: bounded metadata audit

Checked October 4, 2026. **Recommend ROCOv2 manual modality labels for the next quarantine conversion.** This adds radiology and image-context classification beyond BBBC039 microscopy without requiring generated disease answers. The recommendation permits preparation and inspection only; it grants no source/model-use purpose, competition eligibility, or public-weight release clearance.

The machine-readable findings, URLs, timestamps, byte counts, hashes, source integrity checks and retrieval exit codes are in [source-expansion.json](../evidence/source-expansion.json). Analysis output is in [source-expansion-analysis.log](../evidence/source-expansion-analysis.log). Raw source material is deliberately outside the distributable package, at project-root `work/source-expansion/`. Recompute with `python3 work/source-expansion/analyze.py` from the project root. The recorded response bodies total **61,188,175 bytes**; no image bytes were acquired in this metadata audit. No source-heldout captions, concept tables, QA files, or images were downloaded. The all-split ROCO license table supplies article identities and attribution only. An initial public Hugging Face landing-page read exposed its automatic dataset preview; the selected source training files, not that preview, underpin these findings.

## Verified ROCOv2 release and exact inputs

Use the author's [Zenodo record 10821435](https://zenodo.org/records/10821435), DOI `10.5281/zenodo.10821435`. Its API declares **version 2.0.1**, open access, aggregate license **CC BY-NC 4.0**, and metadata modification `2024-10-09T11:10:21.280941+00:00`. This is a more precise release identity than the existing registry's name-only version `2`.

| Exact public file | Bytes | Exact CSV header | Source MD5, matched locally |
| --- | ---: | --- | --- |
| [train_concepts_manual.csv](https://zenodo.org/records/10821435/files/train_concepts_manual.csv?download=1) | 2,352,220 | `ID,CUIs` | `29c00284c410665b6fe6ddc7f0b72f0a` |
| [train_captions.csv](https://zenodo.org/records/10821435/files/train_captions.csv?download=1) | 10,100,161 | `ID,Caption` | `fac7fc6bd570408f451e7558b994518a` |
| [license_information.csv](https://zenodo.org/records/10821435/files/license_information.csv?download=1) | 9,446,130 | `ID,PMCID,Attribution,Link` | `65f21bc4620778259b530a2c033cd4e7` |
| [cui_mapping.csv](https://zenodo.org/records/10821435/files/cui_mapping.csv?download=1) | 62,591 | `CUI,Canonical name` | `b12e7e3627b599b18c68dd3091294ef6` |

The [image archive endpoint](https://zenodo.org/api/records/10821435/files/train_images.zip/content) is publisher-listed as **4,611,440,786 bytes**, MD5 `cd5f5fdb73f24cf6a7473319116a84cc`. A HEAD request returned HTTP 200 and the same Content-Length, without Accept-Ranges or ETag. Its Last-Modified header was `Wed, 19 Aug 2026 06:09:27 GMT`; this transport timestamp is not a new semantic release claim. Range support and selective archive extraction were not tested in this audit. A partial archive retrieval cannot verify the whole-archive MD5.

Actual training IDs follow `ROCOv2_2023_train_000001`, including the split in the identifier. Preserve these exact IDs; the paper's abbreviated filename pattern is insufficient for constructing names. The manual-concept and caption tables each have **59,958 rows and unique IDs**. Their ID sets exactly equal the training IDs in the 79,789-row license table. No training attribution fields or captions are blank. Preserve quoted CSV semantics and semicolon-separated CUIs; do not split captions on commas.

## Rights and grouping findings

The item table gives attribution assertions and article URLs, **not exact per-image license versions or original figure IDs**. It does not override the dataset's aggregate NC declaration. Training attribution prefixes are:

| Literal assertion category | Training images |
| --- | ---: |
| `CC BY ` | 46,627 |
| `CC BY-NC ` | 13,315 |
| `PUBLIC DOMAIN ` | 14 |
| Other malformed/nonstandard strings | 2 |

The two nonstandard entries are `ROCOv2_2023_train_017310` / `PMC6360002` (`CC  Sabetian et al. (2019)`) and `ROCOv2_2023_train_044353` / `PMC6533034` (`CC CC-BY Zanini et al. (2019)`). Keep all 16 unusual assertions review-required; do not rewrite them into cleared license identifiers. A CC BY-only sampling stratum is possible for inspection, but does not itself settle aggregate-license applicability, exact upstream versions, attribution obligations or model-release use.

The license table identifies **33,814 training articles**, 7,759 validation articles and 7,819 test articles. Training article intersections with either heldout partition are **zero**. Validation and test share **4,417 articles**. These statements use article metadata only, without reading heldout labels. Up to 28 training images share one article. Article grouping is a useful minimum, not a patient-independence guarantee; reports can include multiple patients, repeated cases or reused figures. Original figure and patient identifiers remain unknown and must stay null.

## Manual labels and safe conversion boundary

The [source methods](https://www.nature.com/articles/s41597-024-03496-6) describe curated modalities and additional X-ray anatomy/directionality. Automated caption-derived concepts are separate and can conflict with manual concepts. Use `train_concepts_manual.csv` for this first conversion. Caption facts must not silently become visually verified answers.

| Modality CUI | Source canonical name | Training images |
| --- | --- | ---: |
| C0040405 | X-Ray Computed Tomography | 20,459 |
| C1306645 | Plain x-ray | 16,603 |
| C0024485 | Magnetic Resonance Imaging | 9,790 |
| C0041618 | Ultrasonography | 8,305 |
| C0002978 | angiogram | 3,958 |
| C0032743 | Positron-Emission Tomography | 350 |

Exactly **59,465** rows contain one of these modality CUIs; **493 rows have no manual CUIs**. No row has multiple modality labels, repeated CUIs, unmapped CUIs or CUIs outside the 18 observed manual categories. Empty annotation is missing supervision, not a negative label or proof of a combined modality.

There are **16,224** rows with one anatomy label: abdomen 1,747; breast 56; lower extremity 2,293; pelvis 1,257; cranium 3,216; vertebral column 1,073; chest 5,463; upper extremity 1,119. **12,401** rows have one directionality label: transverse anatomical location 29; sagittal 1,868; postero-anterior 3,393; anterior-posterior 7,111. All anatomy/directionality rows contain the plain-X-ray modality label. These are source label counts, not expert validation results. Preserve CUI and canonical text; do not silently reinterpret sagittal as a new view class or anatomy as a lesion region.

The minimal quarantine record should retain:

- Source `rocov2`, family `pmc-literature`, release `2.0.1`, DOI, exact source partition and source ID.
- Article group `PMCID`, article link, raw attribution, aggregate license declaration, per-item exact license URI/version unknown, and review-required status.
- Original figure ID and patient ID null; future byte hash, archive member identity and transform history separate from metadata identity.
- Original manual CUIs, canonical mapping, annotation origin `source-manual-concepts`, exact caption in review-only provenance, and input-file hashes.
- Proposed task `global_classification` / subtype `modality`, a versioned fixed question, source-derived answer, and pending conversion review. No coordinates or pathology labels.

Keep the caption, PMCID, source ID, attribution and source label vocabulary out of eventual model inference inputs. A first image QA sample should cover all six modalities, use one image per article, record deterministic selection and source member hashes, and retain ambiguous/failed examples. Review at least 20 examples per proposed source/conversion under the existing plan. Anatomy and directionality should be distinct later conversions with their own review rather than adding every available label to the initial pilot.

## PMC-VQA: useful next-stage text inventory, not the first importer

The [author-linked repository](https://huggingface.co/datasets/RadGenome/PMC-VQA) is pinned at `b56ae594f794867893143b337b4118a835794647`. Its README and [paper v6, section 7](https://arxiv.org/html/2305.10415v6) assert upstream CC0/CC BY and aggregate CC BY-SA, without specifying the aggregate version. The repository's original and updated CSVs require different parsers; the README abbreviates filenames differently from the actual tree.

| Exact resource at pinned revision | Bytes | Observed schema/use |
| --- | ---: | --- |
| [train.csv](https://huggingface.co/datasets/RadGenome/PMC-VQA/resolve/b56ae594f794867893143b337b4118a835794647/train.csv) | 38,081,707 | Full training file: `Figure_path,Question,Answer,Choice A,Choice B,Choice C,Choice D,Answer_label`; Answer is free text. |
| [train_2.csv](https://huggingface.co/datasets/RadGenome/PMC-VQA/resolve/b56ae594f794867893143b337b4118a835794647/train_2.csv) | 56,703,454 | Only first 131,072 bytes inspected: `index,Figure_path,Caption,Question,Choice A,Choice B,Choice C,Choice D,Answer,split`; Answer is a choice letter in all 357 complete prefix rows. |
| [oa_comm_use_file_list.csv](https://huggingface.co/datasets/RadGenome/PMC-VQA/resolve/b56ae594f794867893143b337b4118a835794647/oa_comm_use_file_list.csv) | 496,021,536 | Only first 262,144 bytes inspected: `File,Article Citation,Accession ID,Last Updated (YYYY-MM-DD HH:MM:SS),PMID,License`. Full rights join remains undone. |

The full original train file SHA-256 `24b4e287546bbfc96ce47aadda59f43fe948b15b82820ac533363e51c1adc029` matches the pinned Hub LFS object. It has **176,948 QA rows**, **115,821 figure filenames**, and **85,778 PMCIDs**, all parseable with `^(PMC[0-9]+)_(.+)\.jpg$`. Preserve the complete figure filename as the figure group. The suffix is not a verified patient identifier, and new subfigure suffixes must not be stripped speculatively.

Deterministic text screening found 14 invalid choice labels (3 double quotes, 11 apostrophes), one fully duplicated row, and eight image/question groups with multiple distinct answers after trimming and case-folding. A deliberately limited regex flags 2,409 answers containing option dependencies such as “none of the above”; that is a triage count, not a prevalence estimate or complete rejection set. Train-2's different Answer semantics can create wrong labels if loaded through a train-1 adapter. Full per-article license joining, original figure-to-panel lineage, caption independence and image-supported answer review remain prerequisites to useful conversion.

The source license prefix contains 2,325 complete rows, with 2,311 `CC BY` and 14 `CC0` assertions; only 83 of the training articles join within that prefix. **Do not extrapolate prefix coverage or licenses to the full dataset.** No image archives were requested; the repository lists original `images.zip` at 18,945,102,275 bytes and `images_2.zip` at 2,206,255,503 bytes.

## Dependence and finite remaining work

PMC-VQA training and ROCO training share **12,078 article IDs**, containing **23,548 ROCO training images**. PMC-VQA training also intersects nine ROCO validation and twelve ROCO test articles. These are exact article intersections, not exact image-duplicate counts. Consequently, combining these sources under independent source-family weights or using one as clean confirmation of the other would be unsupported. Keep the common `pmc-literature` family and eventual cross-source article groups; future image hashes/near-duplicate checks may reveal additional relationships. The source paper also documents ROCO/ImageCLEF ancestry. No comparison with hidden MMBU examples was attempted.

The next useful CPU work is bounded: implement strict metadata-only ROCO intake and rejection accounting; verify a small source-training image sample's decode, member identity and label visibility; record conversion review; then resolve rights/eligibility before any model-use promotion. PMC-VQA can follow only if its full license join and choice/caption-dependent conversion review are worth the additional data and reviewer effort. There is no need to open more datasets merely to increase inventory size. MedMNIST fallback was not pursued because ROCO public training metadata proved available. Compute-dependent model ranking, learned visual diagnostics and end-to-end submission validation remain unmeasured until the relevant model runtime and authoritative harness are available.
