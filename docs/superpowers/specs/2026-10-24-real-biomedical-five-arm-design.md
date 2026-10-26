# Real biomedical five-arm execution design

**Date:** 2026-10-24  
**Status:** accepted for implementation under the user's 2026-10-24 authorization

## Objective

Turn the already-tested synthetic five-arm contract into an evidence-producing biomedical experiment without using any
MMBU public example, label, derivative, embedding, or outcome. The first decision-bearing comparison is:

1. unchanged Qwen2.5-VL-7B base;
2. language-LoRA, answer-only;
3. language-LoRA, answer plus source-provided visual context;
4. language-LoRA plus visual merger, answer-only; and
5. language-LoRA plus visual merger, answer plus source-provided visual context.

Every adapted arm starts from the identical pinned base, sees the same independent units in the same order, and receives
the same total unit mass. The experiment is useful only if a replicated adapted arm improves answer performance over the
unchanged base without a material loss on its paired context endpoint.

## Minimal source portfolio

The first portfolio contains two independent, openly licensed source families:

- **BUS-BRA 1.0** for breast-ultrasound pathology classification and source-provided lesion context. The exact local
  archive must match Zenodo record 8231412 (`133917740` bytes; MD5
  `1f8b2be6476d58fc97bfb5e5a1ea9bab`). The archive license permits use, modification, and distribution subject to
  retaining its notice and citing the dataset paper. Zenodo reports CC BY 4.0. We comply with both. Patient `Case` is
  the independent unit. Five-fold values 1--3 train, 4 develops, and 5 is never opened during selection. Cases 110 and
  536 are excluded everywhere pending resolution of the recorded cross-case near-duplicate candidate.
- **PathMNIST-224 v3** for independent histopathology breadth. The exact official Zenodo artifact must match MD5
  `2c51a510bcdc9cf8ddb2af93af1eadec`; MedMNIST declares CC BY 4.0. Its official train and validation partitions may be
  used for fitting and selection. The CRC-VAL-HE-7K test partition, originating at a different clinical center, remains
  sealed until confirmation. No attempt is made to infer unavailable patient identities inside the development source.

This is a research-training admission, not a clinical-validity claim. Only source-provided labels and annotations are
used. BUS-BRA's classification target is `Pathology`; its context target is a canonical JSON object containing the
source-provided `BIRADS`, side, and normalized source bounding box. PathMNIST's answer target is the published tissue
class; because it has no localization annotation, it contributes only to the answer endpoint and its unit mass is not
silently reassigned to fabricated context.

## Leakage and selection boundary

- MMBU public data is prohibited throughout this lane.
- BUS-BRA splitting is by patient case, never by image.
- The two unresolved BUS-BRA near-duplicate cases are excluded before splitting.
- PathMNIST's external-center test split is confirmation-only.
- Selection uses only development partitions. Each final contender is rerun with three fixed seeds; the confirmation
  partitions are opened once for the frozen base and winning contender.
- Results are source-stratified and macro-averaged so the larger source cannot dominate.

## Training and scoring

The answer endpoint uses exact normalized label matching and macro accuracy by source. BUS-BRA context scoring separately
reports BI-RADS exact match, side exact match, and normalized-box IoU; an invalid or incomplete JSON prediction receives
zero for the affected endpoint. The primary score is the repository's frozen Track 2 proxy applied to macro answer and
context scores relative to the unchanged base. Raw per-source metrics remain visible.

Answer-only and dual-objective arms use singleton microbatch accumulation. Each independent unit has total mass one.
For dual rows with applicable context, answer and context receive 3/4 and 1/4 mass. For PathMNIST rows with no context,
the full mass stays on the answer endpoint. This is the behavior already proven by the native dual-objective preflight.

The first GPU run is a bounded shakedown: 64 training units and 32 development units per source where available, one
epoch, one seed, all five arms. It may establish wiring only. A decision-bearing result requires the full frozen training
set, three seeds, both source families, and the untouched confirmation partitions.

## Runtime and artifacts

The MOCS job uses the already verified Qwen snapshot and Python environment, one A100 per arm, offline model loading, and
one Slurm job per arm. Data acquisition is a separate checksum-verifying step. Every run writes its frozen manifest,
source checksums, ordered-unit digest, package versions, GPU receipt, checkpoints, predictions, metrics, and a terminal
status. Offline reload must reproduce the saved predictions before a result is eligible for comparison.

The packaging rehearsal creates the official-shaped local tree and validates it without upload. It must not contain
source images, source labels, MMBU content, secrets, caches, optimizer state, or absolute HPC paths.

## Stop rules

- Stop on checksum, license, split-overlap, excluded-case, model-revision, trainable-scope, non-finite-loss, reload, or
  provenance mismatch.
- Do not call a shakedown a performance result.
- Do not promote an arm unless the base-relative answer gain is positive in every seed and its mean clears the frozen
  effect floor; report a failed experiment honestly.
- Do not evaluate MMBU, upload, or submit under this authorization.

