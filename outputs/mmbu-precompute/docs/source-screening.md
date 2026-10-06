# Source screening record

Reviewed on October 3, 2026 in America/Chicago (retrieval crossed into October 4 UTC). This is a public-document review, not data ingestion or approval. The machine-readable decisions are in `configs/source-registry.json`; URLs, locators and retrieval evidence are in `evidence/source-research.json`.

All six real-source entries are `candidate`, with empty `allowed_purposes`. They cannot supply even an engineering manifest until their intended purpose is explicitly cleared. Only the original local `synthetic-fixtures` source has engineering permission; those shapes are not biomedical training data.

| Candidate | Primary documentation | Evidence to resolve before use |
|---|---|---|
| ROCOv2, named release 2 | [Dataset paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11208523/), Methods and Data Records | Actual acquisition revision, item-level rights evidence, concept visibility, article/figure grouping. |
| PMC-VQA, repository SHA recorded | [Paper v6](https://arxiv.org/html/2305.10415v6), sections 4.1 and 7; [current repository](https://huggingface.co/datasets/RadGenome/PMC-VQA) | Exact selected files and schema, license version/application, independent grouping, answer validity without hidden context. |
| BBBC039 version 1 | [Accession documentation](https://bbbc.broadinstitute.org/BBBC039), Images, Ground truth and Copyright | Conversion review, parent-collection overlap and experiment grouping. |
| BBBC041 version 1 | [Accession documentation](https://bbbc.broadinstitute.org/BBBC041), Images, Ground truth and Copyright | Intended-use/release terms, difficult labels, class imbalance and collection/group independence. |
| Chest ImaGenome 1.0.0 | [PhysioNet documentation](https://physionet.org/content/chest-imagenome/1.0.0/), Methods, Usage Notes and Access | Credential/access requirements and release compatibility; no restricted files were accessed. |
| MMBU public, repository SHA recorded | [Public card](https://huggingface.co/datasets/mmbu/mmbu-public) and public API metadata | Authorized access, permitted public-dev operations and unresolved protocol register. |

The registry distinguishes a visible release number from a byte-level data pin. PMC-VQA's paper v6 is not a dataset version. A repository SHA identifies the inspected metadata state; no archive integrity or contents have been checked. The public PMC-VQA viewer reports incompatible CSV columns. Select and inspect the intended schema before writing an importer rather than relying on automatic whole-repository loading.

Use the current primary rights statement: PMC-VQA v6 documents upstream license filtering. Do not carry forward older secondary claims that this filtering is absent. A code repository's license is also not the dataset's license. These statements remain evidence for review, not automatic authorization for every downstream use.

Source families express dependence: ROCOv2 and PMC-VQA share `pmc-literature`; both BBBC candidates share `bbbc`; Chest ImaGenome uses `mimic-cxr`. A shared family is a conservative grouping signal, not proof of duplicate items. Different family labels do not prove independence either. Preserve article/figure/field/patient lineage and check the actual intersection when files are legitimately available. No hidden-test search is part of that work.

For the first ingestion decision, fill a compact source-by-conversion table: intended purpose, accepted image/group counts, annotation origin, task/subtype, conversion version, reviewed sample IDs, exclusions/error counts, release conditions, and reviewer/date. Keep missing values explicit. Begin with a smaller usable pilot if the planned task mix cannot be supported.

An `approved` real source requires a documented decision, nonempty structured `evidence`, `reviewed_by`, `reviewed_at`, and only the specifically authorized `allowed_purposes`. Passing a validator does not make that decision. Failed critical conversion review quarantines that conversion; quarantine the source entry if no safe approved conversion remains. Preserve the history when changing a source version or approval.

The protocol register preserves hashes of prior local brief/card snapshots. Those paths identify workspace evidence; an offline copy of the package need not contain the snapshots. The hashes are receipts, not claims that the public documents can never change.


## Version 0.2 quarantine update

BBBC039 official public archives were acquired for separately recorded CPU engineering inspection. Only the source training image/mask contents were decoded. This does not grant model-use purposes or supersede the overlap/annotation gates above. See `bbbc039-intake.md`, the pinned `bbbc039-source-audit.md`, and the acquisition/conversion receipts. Other source candidate access statements retain their original scope.

## Version 0.3 quarantine update

ROCO release 2.0.1 metadata and a deterministic 24-image source-training sample have now been inspected; PMC-VQA training metadata has been audited for article overlap and QA defects. Source-registry access/version fields now describe these actual artifacts. See `source-expansion.md`, `roco-intake.md`, `roco-sample.md` and `roco-upstream-rights.md`. No model-use approval has been granted. Earlier source-screening observations remain historical, not the current acquisition status.
