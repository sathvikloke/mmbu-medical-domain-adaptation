# BUS-BRA train-only evidence sprint

**Status:** real immutable reviewer packet built and independently validated; human review remains incomplete, so no real source is admitted and no training or model use is authorized
**Purpose:** reduce the next genuine evidence gate without weakening the clinical/confirmation gate

**Execution evidence:** [`BUSBRA_REAL_REVIEW_PACKET_2026-10-26.md`](BUSBRA_REAL_REVIEW_PACKET_2026-10-26.md)

## What changed

The existing BUS-BRA packet asks qualified breast-imaging reviewers to answer clinical, localization, provenance, and
release questions across a frozen 244-record population. That packet remains the correct path for adaptive-development
or confirmation claims. The train-only sprint projects the same immutable assets into a narrower visual/annotation-QA
surface for the repository's `train` purpose tier.

The narrow packet asks whether the exact publisher-bound assets are mechanically usable for source-annotation
training. It does **not** ask a reviewer to certify pathology, BI-RADS, diagnostic correctness, or clinical validity.
It always excludes unresolved provenance cases 110 and 536, includes every frozen visual/geometry exception and
`bus_0845-s`, and adds up to 60 patient-exclusive routine records by deterministic SHA-256 rank.

## Build

Start from an immutable v2 BUS-BRA human-review packet. The command reads only that packet; it does not reopen the
source archive.

```sh
PYTHONPATH=src python3 tools/busbra_train_qa.py build \
  <immutable-busbra-human-review-packet> \
  --output <new-train-qa-packet-directory>
```

The output operation is atomic and refuses to overwrite. Preserve the printed `receipt_digest` before any reviewer
opens an asset. Do not edit files inside the emitted packet. Copy `visual-review-template.csv` and
`rights-purpose-template.json` to separate writable locations.

MOCS home and scratch are GPFS and reject Linux `RENAME_NOREPLACE`. The executed production packet was therefore
built and atomically finalized on node-local storage, archived, and then published to a new scratch root as a single
no-overwrite hard-linked tar artifact. Do not point the directory builder directly at GPFS or replace this procedure
with a check-then-rename fallback, which would weaken the no-overwrite guarantee.

## Opening record

Before review, create a closed JSON record with exactly these fields:

```json
{
  "schema": "mmbu.busbra.train_qa_opening.v1",
  "source_id": "busbra",
  "source_version": "1.0",
  "packet_receipt_digest": "<printed receipt_digest>",
  "opened_at": "<UTC timestamp>",
  "opened_by": "<accountable coordinator ID>",
  "authorization_evidence_locator": "<durable evidence locator>",
  "human_attested": true,
  "review_opening_authorized": true,
  "training_ready": false,
  "model_use_authorized": false
}
```

Review timestamps must be strictly after `opened_at`. The visual reviewer must complete every row using only the
closed vocabularies already present in the header. Targets are sorted and pipe-delimited from
`birads_classification`, `mask_context`, and `pathology_classification`. An excluded row has no targets. Every adverse,
uncertain, excluded, or escalated decision needs a nonblank note.

| Field | Allowed values |
| --- | --- |
| `asset_match`, `image_interpretable` | `yes`, `no` |
| `modality_body_part_supported`, `mask_alignment`, `annotation_completeness_concern` | `yes`, `no`, `uncertain` |
| `shortcut_artifact` | `none`, `overlay`, `caliper`, `crop`, `text`, `panel`, `other` |
| `permitted_training_targets` | sorted unique pipe-delimited subset of `birads_classification`, `mask_context`, `pathology_classification` |
| `final_disposition` | `eligible`, `exclude`, `escalate` |

The rights reviewer completes only the exact BUS-BRA 1.0 `train` decision. Public-weight release, adaptive development,
confirmation, upload, and submission remain false. A `narrow` decision must name its exact scope.

## Validate

```sh
PYTHONPATH=src python3 tools/busbra_train_qa.py validate \
  <immutable-train-qa-packet-directory> \
  --completed-visual <completed-visual.csv> \
  --completed-rights <completed-rights.json> \
  --opening <opening.json> \
  --expected-receipt-digest <printed receipt_digest>
```

The validator re-hashes every packet member and binds the raw and canonical completed evidence. It reports record- and
target-specific eligibility, exclusions, escalations, shortcut counts, routine critical failures, and the routine
rule-of-three bound. `admission_input_ready=true` means only that the evidence is mechanically ready to enter the
generic Phase 1 admission chain. The report always leaves `source_admission_authorized`, `training_ready`, and
`model_use_authorized` false.

## What must happen next

1. A real accountable visual/annotation reviewer completes the frozen worksheet.
2. A real accountable rights/purpose reviewer completes the BUS-BRA 1.0 train-only decision.
3. Their identities, roles, conflicts, declarations, and evidence are authenticated through the existing external
   trust-root and Phase 1 admission chain.
4. Only an admitted `train` source and active train-purpose authorization may enter a separately frozen GPU job.
5. The first run is a bounded Qwen3.5-9B base/task-only/dual engineering pilot. It cannot select a winner or support
   clinical/confirmation claims.

Decision-bearing evidence still requires BUS-BRA plus two other independently admitted semantic families, distinct
clinical QA for adaptive-development/confirmation use, three seeds, and a prospectively held-out family. This sprint
shortens the path to real execution; it does not lower that bar.
