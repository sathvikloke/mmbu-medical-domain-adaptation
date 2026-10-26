# Stage A protected structural opening evidence

**Executed:** 2026-10-26 UTC  
**Local work date:** 2026-10-25 America/Chicago  
**Result:** all three bounded structural inspections passed; every source remains quarantined and unauthorized for model use.

## Sealed execution identity

- Packet canonical digest: `36d37a4e78a3fc326a149db2320eabd8f47df0d78e935d37977e23cc5a9b85c6`
- Packet full-file SHA-256: `e959028e3e857935f73b730a28fa8b1e982ea38ffaa488b9b78e252d8cc5ce77`
- Repository commit: `0e049584c4769f78074274d0a5ea34ca256b604e`
- MOCS run root: `/storage/scr/npl015/mmbu-admission/20261026T025503Z-ac920240-2338-41d3-9369-6597af128743`
- Slurm array: `86056`, tasks `0-2`, `epyc-cpu`, one attempt, no requeue
- All three Slurm tasks completed with exit code `0:0`; all three stderr logs are empty.

## Per-source results

| Task | Source | Structural result | Inventory digest | Status receipt digest |
|---:|---|---|---|---|
| 0 | BUS-BRA | Passed: 3,757 ZIP member headers | `38444eac36493aa741912f2e387f462345ed985129883197e8e65659323497a7` | `5e04645fbab62cd34594bb89f7094960a15702cb5841abd43a9e5f5c2a8b21f6` |
| 1 | PathMNIST-224 | Passed: six NPZ members, four permitted train/validation array headers, and CSV schema | `6f3d6b93121efa8e0b85e921e1f726c17ff520d4d7b9a0a17b7553ce6fc7f505` | `83583c8f2781bca7532063885b775418a1b54b821ce7242d5bafa1ee586c934e` |
| 2 | BUSI-WHU v3 | Passed: 1,856 ZIP member headers and workbook structure | `9113ef658000488f9863c1340340930bd7c086dd53f34db4c9a4586a1cc4927a` | `a96055fddc7f9730bd1d563a3219d5b4a313c151991d22f2330378a6aa87ced8` |

Every result was independently reloaded from canonical JSON and revalidated through the complete acquisition, manifest, candidate-to-quarantine, purpose-authorization, prospective-lock, opening-receipt, and registry chains.

## Structural findings

### BUS-BRA

- The archive contains one `BUSBRA/` tree with 3,750 PNG members, three CSV members, one text member, and three directory entries.
- The visible structural metadata names `bus_data.csv`, `5-fold-cv.csv`, `10-fold-cv.csv`, `Images/`, and corresponding mask/image paths.
- No archive member payload was opened during this pass.

### PathMNIST-224

- The archive contains exactly the six expected members: train, validation, and test image/label arrays.
- Only the four train/validation NPY headers were opened.
- Observed shapes:
  - `train_images.npy`: `89996 × 224 × 224 × 3`, unsigned byte
  - `train_labels.npy`: `89996 × 1`, unsigned byte
  - `val_images.npy`: `10004 × 224 × 224 × 3`, unsigned byte
  - `val_labels.npy`: `10004 × 1`, unsigned byte
- The mapping CSV schema is exactly `split,index,image_id`.
- The two test members remained unopened.

### BUSI-WHU v3

- The image archive contains 928 `img/` members and 928 `gt/` members: 1,854 BMP files plus two directory entries.
- The workbook contains one sheet, `Sheet1`, with dimension `A1:M928` and 13 header cells.
- Header cell coordinates and storage types were recorded, but shared-string values were deliberately not resolved.

## Closed join-rule verification

After the protected run, the observed member-name evidence was passed through new pure, fail-closed join validators. The validators do not reopen source archives or decode payloads.

- BUS-BRA: all 1,875 visible image names form a one-to-one match with 1,875 mask names. Pairing receipt digest: `a6f3e70a8323e611bdfe8e8a4fbf9528439437f7809df81caf6ea03db7ef8476`.
- BUSI-WHU: all 927 visible image names form a one-to-one match with 927 annotation names. Pairing receipt digest: `262c1a511229e62eec9991392c152e7ea64e94683f470fdea351437acc9d4e4b`.
- PathMNIST: a closed synthetic validator now requires exactly `split,index,image_id`, train/validation only, contiguous zero-based indices matching the frozen array shapes, and globally unique nonempty image IDs. It rejects test rows, index gaps, duplicate indices, duplicate image IDs, altered schemas, and unknown fields. No real mapping row was opened in this step.

The source-admission test file passes 54 tests, including adversarial join fixtures. Repository link verification and the diff integrity check also pass.

## First schema-value opening outcome

The acknowledged schema-value packet `c5149e1b53c7463ff454e143c47164db012b5aa1f3c8e90826e7c812933012e1` ran once as CPU array job `86059`. The predecessor root and all logs remain preserved.

- BUSI-WHU passed. Exactly 13 header strings were resolved; no data row or label value was emitted. Inventory digest: `6af0ba2ba1959976a9b5aa47ace8e7bcedf6673bf30c78f8185bde22069e08af`; status digest: `49bf2233983d7475f4dc4a40e4b0459ea9a0a465feb7d3ec59d0f417eb625d17`.
- PathMNIST failed closed before emitting an inventory because the mapping has more than the 100,000 expected train/validation rows. This is consistent with additional test-split identity metadata, but the failed packet did not authorize widening the read. No retry occurred.
- The reader was repaired against synthetic fixtures to accept bounded test-split mapping metadata solely for filtering, emit no excluded values, and still emit only the frozen 89,996 train plus 10,004 validation mappings. All 54 focused source-admission tests pass at commit `59da6097d56a203f2f94f43f5b7d817fb4981581`.

## Enforced negative claims

All three status receipts and inventories record:

- `image_payload_decoding_used = false`
- `label_values_read = false`
- `model_use_authorized = false`
- `mmbu_public_content_used = false`

PathMNIST additionally records `test_member_payload_opened = false`. No GPU, model loading, training, upload, submission, or MMBU public-set access occurred.

## What this establishes—and what it does not

This pass establishes the physical archive/workbook/array structure required to implement exact source-specific inventory logic without guessing. It does **not** establish dataset rights, clinical correctness, patient grouping, annotation completeness, source admission, training fitness, model quality, novelty, or competition readiness.

## Corrected PathMNIST mapping outcome

The one-attempt corrected packet `646c08a7f2cba4320cb7f0d5611f68b95a185f1df955d7c24c5ef30dfe53396a` completed successfully as CPU job `86061` in 12 seconds.

- All 107,180 `split,index,image_id` rows were structurally validated.
- Exactly 89,996 train and 10,004 validation records were emitted with contiguous split-local indices and globally unique image IDs.
- Exactly 7,180 test-split mapping identities were counted and excluded; zero excluded rows or identities appear in the emitted records.
- Inventory digest: `69d5978b10b5d7586df2bbb24ab165bf770131f0c88c4b0dd02ee77c14c6e507`.
- Status digest: `1d35390e2cc7a7d2e95059452f2e4b97407fde4b18258853496231547c4a7730`.
- The status receipt records false for image decoding, label-value reading, NPZ test-member opening, model use, and MMBU public content use.

The next evidence-producing step is no longer schema discovery. It is source admission: independent rights, grouping, annotation/clinical-validity, and use-purpose decisions must be completed before any source can be granted model use or enter training.
