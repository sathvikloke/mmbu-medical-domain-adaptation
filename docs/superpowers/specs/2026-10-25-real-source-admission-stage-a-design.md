# Real-source admission Stage A design

**Date:** October 25, 2026  
**Status:** authorized design direction; exact acquisition packet still requires one digest-bound acknowledgment  
**Purpose:** create truthful, immutable source-custody evidence without weakening any scientific, clinical, or legal gate

## Intent

The Qwen3.5-9B confirmation protocol is implemented and the replicated development response justifies one real confirmation path. The next blocker is source admission, not another model screen. BUS-BRA and PathMNIST lack complete training-purpose admission, and BUSI-WHU v3 has not entered the protected confirmation custody chain.

Stage A performs source identity resolution, fresh acquisition, quarantine custody, protected inventory, deterministic joins, and readiness reporting. It may end with every source still blocked. A blocked result is valid evidence and must never be repaired by inventing parents, changing source identity, or treating software checks as human review.

## Authorized boundary

The user's October 25 instruction authorizes real biomedical-source acquisition and opening, MOCS scratch use, and admission work for the MMBU project. That statement authorizes scope, but does not make the user a clinical, grouping, rights, or candidate-admission reviewer. One final acknowledgment must bind the exact sealed acquisition packet after its digests exist; no repeated acknowledgments are required unless that packet changes.

Stage A may:

- use CPU nodes and a new root under `/storage/scr/npl015/mmbu-admission/`;
- resolve official public metadata without opening biomedical payloads;
- freshly acquire the exact official source artifacts once under an active acquisition authorization;
- after the complete protected-opening chain validates, inventory and decode only the permitted source populations;
- emit immutable receipts and repository-safe aggregate reports.

Stage A may not:

- inspect any biomedical payload before its protected-opening receipt is active;
- open PathMNIST test arrays or use them for development, confirmation, or selection;
- use or inspect any MMBU public example, label, derivative, embedding, or outcome;
- load model weights, use a GPU, train, infer, select a checkpoint, or evaluate a model;
- fabricate reviewer identity, clinical truth, parent identity, rights authority, or release permission;
- upload, submit, publish biomedical content, overwrite evidence, or auto-retry a failed acquisition.

## Frozen official identities

### BUS-BRA 1.0

- Source ID/version/family: `bus-bra` / `1.0` / `bus-bra`
- Official record: Zenodo `8231412`, DOI `10.5281/zenodo.8231412`
- Exact artifact: `BUSBRA.zip`
- Expected bytes: `133917740`
- Expected MD5: `1f8b2be6476d58fc97bfb5e5a1ea9bab`
- Proposed purposes: `train`, `release`
- Population: the outer-fold training population only; any adaptive-development role requires a separate successor authorization

The existing structural audit remains evidence, not acquisition authority. Cases 110 and 536 remain linked or excluded until provenance review resolves them. The `bus_0845-s` geometry exception remains a clinical/visual review gate.

### PathMNIST-224

- Source ID/version/family: `pathmnist-224` / `3.0` / `nct-crc`
- Official wrapper record: Zenodo `10519652`
- Exact artifact: `pathmnist_224.npz`
- Expected bytes: `12629854322`
- Expected MD5: `2c51a510bcdc9cf8ddb2af93af1eadec`
- Upstream record: NCT-CRC-HE-100K and CRC-VAL-HE-7K, Zenodo `1214456`
- Proposed purposes: `train`, `release`
- Population: wrapper `train` and `val` arrays only; every `test_*` member remains unopened

The official MedMNIST source-image mapping is a separate, exactly pinned acquisition artifact. Its repository commit, exact filename, byte count, SHA-256, join key, join algorithm, and parent namespace must be frozen before acquisition. If it cannot recover a defensible patient/slide parent for every retained row, PathMNIST stays blocked. The existing compiler is forbidden for Stage A because it reads `test_labels.npy` and treats patches as independent.

### BUSI-WHU v3

- Source ID/version/family: `busi-whu` / `3` / `busi-whu`
- Official record: Mendeley Data `k6cpmwybk3`, DOI `10.17632/k6cpmwybk3.3`
- Proposed purposes: `confirmation`, `release`
- Population: all structurally eligible, patient-joined v3 records; no target-derived filtering

Exact official files:

| File | Bytes | SHA-256 | Official file ID |
| --- | ---: | --- | --- |
| `BUSI-WHU.zip` | 128106790 | `5d10c0bb931666e9cff48db9161febc0ec0c74e4b611c2edcbb9726f6d9d74cc` | `5aa18322-e19e-4779-8392-e621ec660f79` |
| `Patient_infos_BUSI-WHU.xlsx` | 92017 | `14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44` | `6f13c484-94e1-4378-bc73-293a68671948` |

The official API metadata response, file listing, license record, and redirect chain are identity evidence. The image archive and patient workbook are acquired together. Masks are inventoried for integrity but cannot define the frozen classification target.

## Identity resolution before authorization

A metadata-only identity resolver records, for every source:

- canonical record and file URLs;
- source ID, version, family, DOI, exact artifact basenames, sizes, and published checksums;
- terms/license artifact digests and official provenance locators;
- every redirect host required for transport;
- a normalized identity-evidence digest.

No biomedical payload is downloaded during this step. Identity ambiguity blocks packet creation.

## Scratch and preservation policy

Every launch uses an independent, non-circular ID:

```text
/storage/scr/npl015/mmbu-admission/<UTC timestamp>-<random UUID>/
```

The path is then bound into the sealed authorization. The root contains `repo/`, `staging/`, `records/`, `inventory/`, `receipts/`, and `logs/`. It is create-once. The old home archives are historical evidence only and are not reused as acquired artifacts.

Each artifact gets one acquisition attempt with no resume, retry, or replacement. Partial bytes, logs, and failure receipts remain preserved. A failure needs a new root and a successor authorization. Before launch, available scratch bytes must exceed the sealed sum of `maximum_bytes` plus a 20 GiB working margin.

## Mandatory custody graph

For each source, the following records must exist and validate in order:

1. metadata-only identity evidence;
2. acquisition-reviewer attestation;
3. allowed `acquisition_authorization` with `intended_purpose=quarantine_inspection`, exact command/method, exact host allowlist, exact artifact basenames, numeric byte cap, sealed staging destination, and `inspection_prohibited=true`;
4. authorization-registry head naming that authorization;
5. one-shot acquisition execution receipt;
6. exact `source_artifact_manifest` binding observed bytes, SHA-256 values, receipt, and retrieval log;
7. candidate then quarantined source record with immutable proposed purposes;
8. container-level quarantine split built from names, sizes, and archive headers only;
9. quarantine-inspection purpose authorization and new authorization-registry head;
10. prospective `custody_inventory` lock;
11. protected-access inventory opening receipt and opening-receipt-registry head;
12. only then, deterministic inventory/decoding and eligible-population construction.

Any missing, stale, mismatched, late, or superseded member blocks opening.

## Protected inventory rules

### BUS-BRA

Inventory the admitted outer-fold training population, preserve the existing parent/linkage rules, and emit explicit exclusions for ambiguous provenance or geometry. No prior derived inventory is silently imported.

### PathMNIST

Use a new header/member-scoped reader. It may inspect NPZ central-directory metadata first and may open only `train_images`, `train_labels`, `val_images`, and `val_labels` after the protected opening. It must reject any access request for a `test_*` member. The official mapping join must be complete at the frozen parent namespace or the source is structurally ineligible.

### BUSI-WHU

Join archive images, masks, filename labels, and the exact patient workbook using one pre-frozen normalized-key algorithm. Ambiguous, duplicated, missing, or conflicting joins are excluded and reported. Fewer than 60 eligible patients yields `underpowered`.

## Duplicate and grouping contract

The method is frozen before protected opening:

- exact artifact identity: SHA-256 of each acquired artifact and each logical image member;
- exact decoded-image identity: SHA-256 of canonical RGB pixel bytes plus width and height;
- perceptual candidate: 64-bit dHash with Hamming distance at most 4 and aspect-ratio difference at most 0.05;
- comparison population: every structurally eligible record within the source and across all Stage A sources;
- collision handling: exact or perceptual cross-parent/cross-source candidates remain blocked pending a qualified grouping reviewer; software never chooses the surviving label;
- missing parent policy: reject the record for decision-bearing populations.

The grouping algorithm can generate evidence, but cannot issue its own grouping-reviewer attestation.

## QA contract

Stage A freezes the sampler implementation, error taxonomy, adjudication schema, and target/annotation-completeness checks before opening. The actual QA sampling plan is created only after the eligible population exists. Sample sizes, clinical thresholds, stratum definitions, and medical dispositions remain blocked until a qualified reviewer approves exact values. Software cannot turn a draft QA plan into an admission receipt.

## Stage A execution sequence

1. Resolve and freeze official metadata identities and redirect hosts.
2. Build one closed acquisition packet containing the repository commit, launch root, identities, exact commands, byte caps, proposed purposes, and all forbidden operations.
3. Obtain one digest-bound project-owner acknowledgment and independent acquisition-reviewer attestation for that exact packet.
4. Validate the packet and both registry heads locally against synthetic and negative fixtures.
5. Verify scratch capacity and create the new run root.
6. Freshly acquire all exact official artifacts once, streaming only byte counts and hashes.
7. Emit and validate execution receipts and artifact manifests. Stop on any mismatch.
8. Emit quarantined source/split/purpose records, inventory locks, opening receipts, and registry heads. Validate the complete graph before payload access.
9. Run the protected inventories, joins, and duplicate-candidate generation.
10. Emit eligible-population manifests plus blocked/draft human-review packets.
11. Write a combined status receipt and stop. Stage A never launches a model job.

## Required outputs

Each source receipt binds exact identity, official locators, acquisition records, archive identities, container inventory, grouping namespace, mapping/join completeness, decode counts, duplicate candidates, exclusions, unresolved fields, and first blocking gate. Every output fixes `mmbu_public_content_used=false`, `model_weights_loaded=false`, `gpu_used=false`, and `model_use_authorized=false` unless a later independently valid human admission chain changes the last field.

The combined receipt may say only what its source receipts prove. It cannot promote a source or authorize training, confirmation, release, or model selection.

## Human gates

Software cannot close:

- BUS-BRA medical semantics, the `bus_0845-s` exception, and cases 110/536 provenance;
- rights for challenge training, disclosure, and adapter release;
- PathMNIST parent validity if the primary mapping is incomplete;
- BUSI-WHU patient/label semantics and clinical validity;
- qualified clinical/visual QA and collision adjudication;
- candidate admission and final purpose authorization.

No repeat outreach is sent before the existing October 30 follow-up date unless a reply or bounce arrives.

## Stop rules

- Any size, checksum, version, origin, redirect-host, command, or byte-cap mismatch stops before opening.
- Any attempted `test_*` PathMNIST access fails closed and is recorded.
- Missing complete PathMNIST parent mapping blocks PathMNIST.
- Missing complete BUSI-WHU patient/label joins blocks confirmation.
- A license label alone never grants a purpose.
- Failed decoding, ambiguous joins, and duplicate candidates remain exclusions or blockers.
- No training begins until the necessary source records hold real `train` authority and the later Qwen3.5-9B successor runtime gate passes.

## Success condition

Stage A succeeds when every permitted acquisition and inventory action is reproducible, every disallowed action fails closed, and every unresolved human gate is explicit. Each source must end as mechanically ready for human admission review, blocked by a named external decision, or structurally ineligible for its frozen role. Only a later Stage B plan may authorize model loading, training, confirmation, or release.
