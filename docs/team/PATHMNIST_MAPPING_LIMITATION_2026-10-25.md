# PathMNIST mapping limitation and status correction

**Reviewed:** 2026-10-26 UTC
**Evidence:** corrected mapping inventory from CPU job `86061`
**Decision:** PathMNIST remains ineligible for decision-bearing development or confirmation use
**Author evidence:** authenticated replies received from the MedMNIST lead and original source lead on October 26, 2026

## Material finding

The official 100,000-row train/validation mapping does not contain a slide or patient key. Every emitted `image_id` has exactly the form `PREFIX-XXXXXXXX`: one of nine uppercase prefixes followed by a globally unique eight-letter token. There are 100,000 unique IDs and 100,000 unique suffixes. No identifier repeats across patches in a way that can reconstruct the 86 upstream source slides or their patients.

The mapping therefore proves wrapper-to-source-image identity only. It cannot prove independent-unit grouping, cannot detect train/validation patches originating from the same slide or patient, and cannot support a patient-disjoint development claim. The [official MedMNIST repository](https://github.com/MedMNIST/MedMNIST) describes the CSV as a mapping to source image names, while the published PathMNIST description says the 100,000-patch NCT-CRC source was divided 9:1 into train and validation. Neither statement supplies the missing parent key.

The October 26 author reply confirms this interpretation rather than repairing it: the published CSV links each
PathMNIST sample to its original patch ID, while slide/patient identifiers must be sought from the original
NCT-CRC-HE-100K authors. The response supplies no slide key, patient key, or complete parent mapping. The retained
communication record is
[`pathmnist-medmnist-2026-10-26.json`](../../outputs/source-clarification-replies/pathmnist-medmnist-2026-10-26.json).

The original source lead then answered the exact public patch-to-slide/patient mapping question negatively. The terse
reply supplied no parent map, filename encoding, or confirmation that the 86 slides represent 86 distinct patients.
It is retained with passing Gmail DKIM, DMARC, and SPF observations in
[`nct-crc-author-2026-10-26.json`](../../outputs/source-clarification-replies/nct-crc-author-2026-10-26.json).
This closes the current public-lineage route negatively; it does not prove that no private source record exists or
grant any authority for training-only use.

## Boundary correction

The historical job `86061` status truthfully records that no NPZ label-array member was opened. Its broader `label_values_read = false` wording is nevertheless incomplete: the permitted `image_id` strings themselves expose nine class-like prefixes. The mapping opening therefore revealed semantic label proxies even though it did not open `train_labels.npy`, `val_labels.npy`, or either test member.

The historical receipt is preserved unchanged. Going forward, claims must distinguish:

- `npz_label_array_values_read = false`; from
- `semantic_label_proxy_exposed_by_mapping = true`.

No class target is inferred or granted authority from this finding. It is a custody-surface correction, not a label-validation result.

## Consequences

1. Do not use PathMNIST validation results as independent patient-level evidence.
2. Do not open the train/validation label arrays merely to continue the current plan; labels cannot repair missing parent lineage.
3. PathMNIST may remain a quarantined training-only candidate only if development and selection are performed on an independently admitted source and the team accepts that its 100,000-patch family contributes no independent validation unit.
4. Any claim of patient- or slide-disjoint PathMNIST train/validation performance requires a source-author-provided mapping or another authoritative parent record.
5. The unopened PathMNIST test arrays remain excluded. Their independent-center status does not authorize opening or use.

## Portfolio effect

This finding lowers PathMNIST's near-term value relative to BUS-BRA, BUS-UCLM, and ChestMNIST. It does not invalidate
PathMNIST as a possible source of histology training examples, but it prevents the wrapper split from serving as clean
decision evidence. The public mapping and original-author routes are closed negatively; only genuinely new
authoritative parent records could reopen PathMNIST for decision-bearing use.
