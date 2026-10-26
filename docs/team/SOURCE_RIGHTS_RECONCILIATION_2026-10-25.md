# Source rights and public-metadata reconciliation

**Reviewed:** 2026-10-26 UTC
**Scope:** public record metadata only; no biomedical payload, label, image, or MMBU example was opened
**Decision:** all three sources remain quarantined and unauthorized for model use

## Result

The three Stage A candidates have now been reconciled against their official public records and the immutable artifacts already acquired in quarantine. The public records establish source identity, version, citation, and a plausible license basis. They do **not** establish patient grouping, clinical correctness, annotation completeness, competition fitness, trained-weight release compatibility, or permission to use any record for model training.

| Source | Official public evidence | Rights state after this review | Remaining blocker before admission |
|---|---|---|---|
| BUS-BRA 1.0 | [Zenodo record 8231412](https://zenodo.org/records/8231412) identifies version 1.0, DOI `10.5281/zenodo.8231412`, the 133,917,740-byte archive, MD5 `1f8b2be6476d58fc97bfb5e5a1ea9bab`, required paper citation, and UFRJ copyright/distributor status. The official Zenodo API metadata identifies license `cc-by-4.0`. Protected job `86062` subsequently read the exact embedded license and verified its frozen required phrases, plus complete metadata/fold agreement and patient-disjoint proposed splits. | **Candidate only.** Public and embedded-license evidence now agree at the mechanical-validation level, but a named rights authority has not issued purpose-specific competition-training or trained-weight-release decisions. | Purpose-by-purpose rights/release decision; source-author resolution of cases 110 and 536; qualified medical and annotation review; source-proximity review. |
| PathMNIST-224 / MedMNIST+ 3.0 | [Zenodo record 10519652](https://zenodo.org/records/10519652) identifies version 3.0, MD5 `2c51a510bcdc9cf8ddb2af93af1eadec`, and states that MedMNIST is CC BY 4.0 except DermaMNIST. It also requires citation of the relevant upstream source paper and says the data are not intended for clinical use. The opened mapping contains only unique class-like source-image IDs and no recoverable slide/patient parent. | **Candidate only.** The wrapper's license is explicit and the acquired archive identity matches, but wrapper permission does not resolve upstream attribution, grouping, or release obligations. The wrapper validation split cannot currently support independent patient-level evidence. | Obtain an authoritative slide/patient mapping or restrict the source to training-only use with selection elsewhere; review upstream NCT-CRC obligations; keep test identities and test arrays excluded; perform qualified label/clinical-validity review; issue separate training and release decisions. |
| BUSI-WHU v3 | [Mendeley record v3](https://data.mendeley.com/datasets/k6cpmwybk3/3) identifies DOI `10.17632/k6cpmwybk3.3`, 927 images, benign/malignant cases, ages 17–79, Renmin Hospital collection dates, ethics approval `WDRY2022-K217`, a segmentation purpose, and CC BY 4.0. Protected job `86066` subsequently proved an exact 927-row workbook/image/annotation join, 816 patient groups, and bounded benign/malignant label structure without decoding images or annotations. | **Candidate only.** The record-specific license is explicit, artifact identities are fixed, and mechanical patient grouping is now available. | Freeze patient-disjoint confirmation sampling; obtain qualified clinical and annotation review; validate decoded-image/annotation integrity under a separate authority; issue separate confirmation-purpose and release decisions. |

## Evidence boundaries

This review makes only the following positive claims:

1. the public record identity and version match the quarantined source identity;
2. the published archive checksum or acquired artifact identity is consistent with the frozen Stage A evidence;
3. PathMNIST/MedMNIST+ and BUSI-WHU publish explicit CC BY 4.0 terms; and
4. the BUS-BRA Zenodo API publishes `cc-by-4.0`, while its rendered page and unopened embedded license require reconciliation before reliance.

It does not convert a public license into a blanket training or release approval. Dataset-use permission, competition disclosure, attribution, model-weight release, source grouping, and biomedical validity remain separate decisions. The user's prior broad project authorization does not substitute for the missing source-specific evidence.

## Role reconciliation

- PathMNIST `train` is only a proposed training partition. It is not admitted.
- PathMNIST `val` remains a proposed development partition and must not be silently merged into training.
- PathMNIST `test` remains excluded from Stage A outputs and unopened.
- BUS-BRA has proposed train/development/confirmation roles from its frozen fold rule, but none is active before admission.
- BUSI-WHU is proposed only as an independent confirmation source. It must not influence candidate selection or training.

## Next bounded evidence step

The BUSI-WHU metadata opening has passed, so another metadata read would add no value. The smallest useful next step is to freeze a patient-grouped clinical/annotation review design and a separate purpose/release decision surface. Any later pixel or annotation decoding must be authorized in a new digest-bound packet and reviewed by appropriately qualified people. PathMNIST label-array opening remains deferred because it cannot repair the demonstrated parent-lineage blocker.

Until those independent clinical, annotation, rights, and purpose gates pass, the honest admitted-source count remains **zero**.
