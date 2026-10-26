# BUSI-WHU decision-integrity repair design

**Status:** prospective repair design; no real biomedical opening, reviewer authentication, admission, confirmation,
training, MMBU evaluation, upload, or submission is authorized by this document  
**Audit basis:** `docs/team/INDEPENDENT_PROJECT_AUDIT_2026-10-26.md`  
**Intent:** make the BUSI-WHU path incapable of opening protected pixels or producing decision-bearing confirmation
evidence unless every authority, identity, target, population, and duplicate boundary is transitively frozen.

## Why this repair exists

The October 26 independent audit found that the current branch has strong deterministic mechanics but three classes of
decision-integrity failure: real decoding can bypass the authority graph; confirmation targets and execution inputs are
not fully frozen; and human identities/qualifications are declared inside the document they are meant to authenticate.
Those defects block merge and any real BUSI-WHU opening.

The repair preserves the existing selection, review, and patient-resampled confirmation logic where it is sound. It
does not use the opportunity to add a new learner, tune a model, inspect MMBU, or improve a score.

## Goals

1. Require a distinct, registered, operation-specific protected-opening chain before the first BUSI-WHU pixel byte is
   read.
2. Parse, hash, and decode the exact authorized artifact bytes through stable single-open file descriptors.
3. Freeze authoritative source targets and record ownership through review, admission, randomization, lock, result
   validation, and analysis.
4. Make the authenticated confirmation bridge mandatory for real runs while keeping a visibly synthetic-only fixture
   constructor.
5. Require independently validated reviewer and rights-attestation records; self-declared booleans and names never
   authenticate a human.
6. Implement the frozen cross-source duplicate contract before confirmation opening.
7. Represent every clinical question and source-level kill condition named by the governing design.

## Non-goals

- No real image, mask, label, or workbook opening.
- No reviewer recruitment or credential decision.
- No source admission, model loading, training, GPU use, MMBU public-set access, upload, or submission.
- No change to confirmation prompts, candidate identity, seeds, margin, resampling count, or pass/fail statistic.
- No attempt to raise novelty or competition ratings from repair work.
- The older Stage A arbitrary-prose attestation and partial historical-packet findings are a separate custody-hardening
  project after this decision path is safe.

## 1. Operation-specific protected opening

Add a closed `mmbu.phase1.busi_whu_review_opening_authorization` record. It binds:

- the exact active quarantined BUSI-WHU source and source-artifact manifest;
- the exact acquired archive and workbook artifact digests, byte counts, logical paths, and roles;
- the exact metadata inventory, review selection, review schema, duplicate-contract, and tested repository revision;
- the pre-opening primary, secondary, adjudicator, and rights-authority credential-verification digests;
- the only allowed operations: strict image BMP decode, strict annotation BMP decode, and bounded workbook-geometry
  comparison for the 927 frozen records;
- explicit forbiddance of model use, training, MMBU access, network access, upload, and submission;
- one attempt, one exact output root, no overwrite, and a bounded time window.

The record must be an input to a prospective lock whose phase is `busi_whu_clinical_review`. A registered protected
opening receipt must be the active head for that lock. The opening receipt binds the source manifest and opening
authorization. Generic Stage A structural opening evidence cannot satisfy this gate because it did not permit image
decoding.

`validate_busi_whu_review_opening(records, authorization_digest, opening_receipt_digest, now)` returns a private
validated capability object. The packet builder accepts only that capability; no public function accepts raw paths plus
self-sealed inventory alone.

## 2. Stable single-open artifact access

The protected opener resolves each artifact by its full frozen logical path and role, never by basename. It opens the
file once with no-follow semantics, requires a regular file with one link, records pre-read `fstat`, streams SHA-256 and
parsing from the retained descriptor, records post-read `fstat`, and rejects any identity or size change. All ancestors
of the execution root must be non-symlink directories.

The archive parser reads through the retained descriptor. The workbook comparison reads through its retained
descriptor. Receipt hashes are produced from the same stream or immutable bytes that were parsed; the path is not
reopened after authorization.

## 3. Frozen target and geometry contract

The protected packet records, for every record:

- source label code and canonical target label (`benign` or `malignant`);
- patient identifier and workbook row;
- workbook-declared geometry metrics (`scale(pixel/cm)`, `scale_category`, `gt_area(pixel2)`,
  `Image_area(pixel2)`, `gt(cm2)`, `gt/all`, centroid coordinates, and maximum/minimum diameter);
- decoded image and annotation dimensions;
- derived foreground area, centroid, tight annotation box, and ratio evidence; and
- explicit metric-by-metric geometry-consistency disposition without automatic repair or a fabricated equivalence
  between workbook diameter fields and a mask bounding box.

The packet emits deterministic deltas and parse/consistency findings. Numeric disagreements are never silently
corrected. Until a separately frozen source-specific tolerance contract exists, every numeric disagreement is
`unresolved` and blocks the affected task; code must not invent tolerances from the observed data.

Every task-specific eligible manifest carries an exact sorted `record_targets` mapping and its digest. The confirmation
source manifest, population binding, randomization artifact, and confirmation lock carry the same mapping and digest.
Every result row's target must equal the locked target for that record. A target flip repeated consistently across all
conditions is still invalid.

## 4. Mandatory real-confirmation entry point

Rename the current untrusted constructor to a private implementation. Expose two deliberately distinct entry points:

- `build_authenticated_randomization_artifacts(...)` consumes the actual review report, confirmation source manifest,
  Phase 1 store, source-admission digest, confirmation-purpose digest, and creation time. It revalidates the entire
  chain internally and binds the exact target map.
- `build_synthetic_randomization_artifacts(...)` accepts only a closed synthetic-fixture record with
  `origin_class="synthetic_engineering"`, `real_execution_eligible=false`, and no biomedical source identity.

No execution-facing path may accept an opaque source-manifest digest or arbitrary patient map. Analysis and lock
validation resolve the same authenticated source manifest transitively.

## 5. Human identity and qualification authentication

The review opening no longer contains authoritative names, qualifications, or `human_attested` booleans. Human
authority has two non-circular layers:

1. Four **pre-opening credential-verification records** are created and independently verified before the opening
   authorization. They bind identity, role, qualification class, verification evidence, permitted purpose, and
   independence. The opening authorization binds their digests.
2. Four **post-opening review attestations** are created only after immutable packet/report outputs exist. They bind
   the completed evidence digests and the corresponding pre-opening credential-verification digest. They can never
   authorize the opening that produced their own subject.

Each layer is validated through a versioned closed schema and must bind:

- the exact packet/opening subject digest;
- one exact role: primary breast-ultrasound reviewer, independent secondary reviewer, clinical adjudicator, or rights
  authority;
- an allowed qualification class and a non-self-authored verification artifact;
- the exact permitted purpose set;
- distinct reviewer identity where independence is required; and
- chronology appropriate to its layer: credential verification before authorization/opening, review attestation
  after immutable review output.

The completed report sets `reviewer_identity_authenticated=true` only after all pre-opening credential records and all
post-opening output attestations validate. The confirmation bridge requires true and re-resolves both layers. A report
that merely contains names, locators, or true booleans remains blocked. The qualification verifier must be distinct
from the reviewed person, and primary, secondary, adjudicator, and rights roles must satisfy the frozen independence
matrix.

## 6. Cross-source duplicate contract

Implement one versioned 64-bit dHash routine with the prospectively frozen comparison rule:

- exact decoded-image SHA-256 always creates a candidate;
- dHash Hamming distance at most four creates a perceptual candidate;
- aspect-ratio relative delta must be at most 0.05 for perceptual comparison;
- BUSI-WHU fingerprints are compared against every source declared eligible for training or confirmation in the
  active source registry; the authorization carries the exact complete list of source identity and fingerprint
  inventory digests, and a declared source without a fingerprint inventory blocks opening; and
- all source-inventory digests and comparison parameters are bound into the review opening and packet receipt.

Candidate generation is deterministic, emits every cross-source and within-source pair/group, and never silently
chooses a disposition. Any unresolved cross-patient or cross-role collision blocks confirmation. Tests cover Hamming
distances 0, 1, 4, and 5 plus both sides of the aspect-ratio boundary.

## 7. Complete clinical and source-level decisions

Replace the single `annotation_usable` answer with separate closed answers for:

- intended-lesion annotation;
- lesion-grounded classification completeness;
- localization completeness; and
- additional-visible-lesion or incomplete-instance risk.

The task rules are explicit: global classification does not require a usable mask; grounded classification and
localization each require their named completeness gate; any additional/incomplete-instance risk narrows or excludes
the affected single-target tasks.

Add independently signed source-level assessments by the clinical adjudicator and data custodian for systematic label
inversion, label leakage/shortcut, patient-identity defect, and systematic annotation defect. Each is `absent`,
`present`, or `unresolved` with evidence and rationale. Every `present` or `unresolved` finding blocks confirmation;
there is no free-form materiality escape hatch. Disagreement between the two assessors is unresolved. Aggregate record
pass rates cannot override it.

Adjudication record IDs and duplicate-group keys are unique and exact. Duplicate rows reject before any last-entry-wins
map is built.

## 8. Status and verification

Preserve the current canonical status as immutable predecessor evidence. After the repair is implemented and verified,
build a versioned successor status record, validate its transition through the authority module, and atomically replace
`config/phase1/current-status.json` only through that transition path. The successor preserves the predecessor digest
and records:

- the real external-biomedical response screen as exploratory evidence;
- the independent-audit blockers;
- the repaired code/test revision; and
- continued `blocked_external` status for real confirmation until authenticated humans and real admission exist.

Verification must include focused red/green tests, the full Phase 1 suite, maintained-link verification, Python compile
checks, `git diff --check` on the working tree, and `git diff --check <merge-base>..HEAD` on the whole branch. No score
or readiness rating rises from these repairs alone.

## Frozen implementation choices

- Canonical source identity is `source_id="busi-whu"`, `source_version="3"`; the composite string
  `busi-whu-v3` is not a second source identifier and must be migrated out of confirmation manifests.
- The exact record-to-target mapping and digest are carried by both the general prospective lock and the
  confirmation-specific lock; equality is mandatory.
- Task-specific eligible manifests are separately sealed records referenced by the report, not mutable nested blobs.
- A one-attempt opening is consumed only when the protected descriptor is successfully opened. Validation failures
  before descriptor acquisition do not consume it; any read/parse/decode failure after acquisition does.
- Duplicate/adjudication record identifiers and pair/group keys are unique by schema; duplicates reject before map
  construction.

## Success condition

Synthetic fixtures can demonstrate the complete chain, but a real BUSI-WHU run remains impossible until a separately
authorized operation-specific opening and independently verified human attestations exist. Once those records exist,
the same execution path reads only the exact authorized bytes once, emits immutable review evidence, freezes exact
targets and patients, and makes it impossible to bypass the authenticated bridge or mutate labels after lock.
