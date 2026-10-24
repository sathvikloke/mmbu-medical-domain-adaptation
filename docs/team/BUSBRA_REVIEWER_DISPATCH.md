# BUS-BRA reviewer dispatch brief

**Prepared:** October 23, 2026
**Status:** recruitment and review-operations guide only; it does not open the data, authenticate a reviewer, approve a source, or authorize model use

## What we need from people

The automated BUS-BRA checks are finished as far as they can go. The archive identity, patient grouping, image and
mask joins, structural exceptions, duplicate-risk screen, and 244-record review population are frozen. Four decisions
still need accountable human judgment:

1. a breast-imaging reviewer decides whether each selected image, mask, and source field can support the named task;
2. a different breast-imaging reviewer independently reviews every mandatory exception and any uncertain or
   non-eligible primary decision;
3. a BUS-BRA source author or data steward resolves whether cases 110 and 536 have distinct or linked provenance; and
4. the team's rights authority reviews the exact source version, attribution duties, challenge disclosure, and whether
   each proposed purpose is acceptable.

These decisions stay separate. A clinician doesn't have to make a license decision, and the team rights reviewer
can't substitute for a breast-ultrasound review.

## Who qualifies

### Primary medical reviewer

Use one of the following profiles:

- breast-imaging clinician;
- breast-ultrasound clinician; or
- breast-imaging researcher with documented clinical review qualification.

The person reviews all 244 frozen records. They are checking whether the source annotation supports the proposed
research task. They are not being asked to diagnose a patient from scratch, certify model safety, or endorse a clinical
product.

### Secondary medical reviewer

The secondary reviewer must be a different person with one of the same three qualification profiles. They review at
least the 50 records carrying mandatory reasons. They also review any record where the primary reviewer is uncertain,
finds an artifact, requests a correction, excludes the record, or raises a completeness concern.

If the two reviewers disagree on any answer, permitted task, or disposition, a third breast-imaging or
breast-ultrasound clinician must adjudicate that record. The adjudicator can't be either of the first two reviewers and
must record a complete decision vector plus rationale.

### Provenance reviewer

This role must be a BUS-BRA source author or source data steward. The specific question is whether cases 110 and 536
represent distinct lineage, linked lineage, records that must both be excluded, or records that must be assigned together. Image similarity by
itself can't answer this.

### Rights and release reviewer

This role is the team's named rights authority. The reviewer must read the exact BUS-BRA 1.0 terms and make separate
decisions for training, development, untouched confirmation, public weight release, and challenge submission. One
blanket statement that the dataset is open is not enough.

The reviewer may approve, narrow, decline, or leave a purpose unresolved. A narrowed decision remains blocked until
its exact scope is written into the later admission record.

## What the medical review covers

The frozen packet contains 244 image and mask pairs:

- 199 records from the patient-exclusive pathology by BI-RADS sample;
- every recorded box or dimension exception;
- cases 110 and 536 from the perceptual-provenance check; and
- five records that overlap the sampled and mandatory populations, leaving 244 unique records.

For every record, the primary reviewer answers:

- Is this an interpretable breast-ultrasound image for the proposed task?
- Is the lesion mask usable for the named localization or grounded-classification task?
- Is an additional lesion visible, or could the annotation be incomplete?
- Are the pathology and BI-RADS values clinically plausible for the displayed record and usable for the named task?
- Is there a crop, overlay, caliper, panel, or acquisition artifact that could create a shortcut?
- Which of the four proposed tasks are permitted for this record?
- Is the record eligible, correction required, excluded, or unresolved?

The four task names are fixed:

- `pathology classification`
- `BI-RADS classification`
- `mask-grounded pathology classification`
- `mask-derived object detection`

Eligibility is task-specific. Every task requires an interpretable breast-ultrasound image and explicit support for
`modality=ultrasound` and `body_part=breast`. Pathology and BI-RADS classification do not require a usable mask.
Mask-grounded pathology classification and mask-derived object detection require a usable mask and no additional or incompletely
annotated lesion. The packet builder separately binds each frozen source row, image member, and mask member. A clinician
records clinical plausibility and flags suspected mismatches; they do not certify a database join from pixels alone.
Excluded and unresolved records can't retain a permitted task.

## What gets sent to reviewers

Do not send the raw archive or an editable packet assembled by hand. Use only packet manifest and receipt schema v2;
discard and rebuild any unopened v1 packet. After a separately authorized review opening, the project builds one
immutable local packet and freezes its `packet-receipt.json` digest before anyone opens an image.

Send the reviewer:

- this brief;
- the immutable packet or a read-only copy through the agreed secure channel;
- a writable copy of `record-review-template.csv`;
- a writable copy of `source-review-template.json` only for the role-specific source decisions;
- the exact controlled values listed below; and
- a location where review notes and qualification evidence can be retained.

Never edit files inside the immutable packet. Completed forms live outside it and are validated against the frozen
receipt digest.

The review coordinator records the authorized opening in a closed `mmbu.busbra.review_opening_record.v1` containing the
packet receipt digest, UTC opening time, coordinator identity, authorization-evidence locator, `human_attested=true`,
`review_opening_authorized=true`, `training_ready=false`, and `model_use_authorized=false`. The validator rejects any
human review timestamp that is not later than that opening.

The writable source copy starts with schema `mmbu.busbra.source_review_template.v2`. When all required fields are
complete, change only `schema` to `mmbu.busbra.source_review_completed.v2`, `decision_status` to
`completed_human_review`, and `review_complete` to `true`. Leave both authority flags false.

## Controlled values reviewers must use

Record questions use these exact values:

- yes/no questions: `yes`, `no`, or `uncertain`
- shortcut artifact: `none`, `present`, or `uncertain`
- record disposition: `eligible`, `correction_required`, `excluded`, or `unresolved`
- multiple permitted tasks: join the exact task names with `|`
- no permitted task: leave the field empty
- timestamps: UTC in `YYYY-MM-DDTHH:MM:SSZ` form

Source-level decisions use:

- rights decisions: `approve`, `narrow`, `decline`, or `unresolved`
- provenance decision: `distinct_lineage`, `linked_lineage`, `exclude_both`, `coassign`, or `unresolved`

Reviewer profiles use these exact role and qualification tokens:

| Role token | Allowed qualification token |
|---|---|
| `medical_primary` | `breast_imaging_clinician`, `breast_ultrasound_clinician`, or `breast_imaging_researcher_with_clinical_review_qualification` |
| `medical_secondary` | `breast_imaging_clinician`, `breast_ultrasound_clinician`, or `breast_imaging_researcher_with_clinical_review_qualification` |
| `adjudicator` | `breast_imaging_clinician` or `breast_ultrasound_clinician` |
| `provenance` | `source_data_steward` or `source_author` |
| `rights_release` | `team_rights_authority` |

Conflict status is also controlled: `none_declared`, `declared_managed`, or `unresolved`. Every profile needs a
nonblank conflict-evidence locator. An unresolved conflict blocks advancement.

Every reviewer profile needs a stable reviewer ID, controlled role, controlled qualification, qualification-evidence
location, review-evidence location, completion time, and `human_attested=true`. A public institutional profile, CV, or
credential record can support qualification evidence. The review-evidence location must point to the retained review
record, not merely repeat the reviewer's name.

## Review order

1. Confirm each reviewer's role, qualification, conflict status, availability, and evidence location before opening the packet.
2. Obtain the explicit review-opening authorization and freeze the packet receipt digest.
3. The primary reviewer completes all 244 rows in order.
4. The secondary reviewer receives every mandatory or escalated row after its primary decision is recorded.
5. A distinct adjudicator resolves any actual answer, task-scope, or disposition disagreement.
6. The source author or data steward records the evidence-backed cases 110 and 536 provenance decision.
7. The team rights authority records five separate purpose decisions plus exact attribution and redistribution terms.
8. Run the existing validator against the untouched packet and the two completed copies.
9. Authenticate the named reviewers through separate Phase 1 attestations.
10. Build a separate source-admission and purpose-authorization chain. A valid worksheet alone never grants model use.

## Stop conditions

Stop the review and preserve the evidence if:

- a reviewer can't document one of the allowed qualifications;
- the packet digest or any immutable member changes;
- a record is missing or reordered;
- a reviewer wants to replace a difficult mandatory case;
- source fields or geometry appear joined to the wrong case;
- the two medical reviewers disagree and no distinct qualified adjudicator is available;
- cases 110 and 536 can't be resolved from source evidence;
- any intended purpose is declined, narrowed without a written scope, or unresolved; or
- a reviewer is asked to infer permission, medical truth, or provenance from the model's behavior.

## Outreach draft for a medical reviewer

**Subject:** Short breast-ultrasound dataset review for an MMBU research project

Hello Dr. [Last name],

I'm working on a medical vision-language research project for the MMBU Medical Domain Adaptation challenge. Before we
train anything on the BUS-BRA breast-ultrasound dataset, we need a qualified human review of a frozen sample of 244
image and mask pairs.

The review is narrower than a diagnostic study. We would ask you to check whether each image is interpretable, whether
the lesion mask is usable for the proposed task, whether the pathology and BI-RADS values are clinically plausible for
the displayed record, and whether any overlays, incomplete annotations, or additional lesions make the record unsuitable. The form uses fixed
answers, keeps exclusions and uncertainty, and does not ask you to certify the model or make a patient-care decision.

We also need a second qualified reviewer for the 50 mandatory exception records and any cases the primary reviewer
flags. The images come from the public, anonymized BUS-BRA 1.0 release described by the
[primary Zenodo record](https://zenodo.org/records/8231412), but we would share the frozen review packet only
after confirming the review arrangement and data-handling method.

Would you be open to discussing whether you or someone in your department could help with this review?

Thank you,
Aditya Raut

## Outreach draft for a BUS-BRA source author or data steward

**Subject:** BUS-BRA provenance question about cases 110 and 536

Hello Dr. [Last name],

I'm using BUS-BRA 1.0 in a medical vision-language research project, subject to a review process before any training.
Our structural and duplicate-risk checks found that cases 110 and 536 need a source-level provenance decision. Visual
similarity isn't enough for us to decide whether they represent distinct acquisitions, linked lineage, or records that
should be assigned together or excluded.

Could you confirm the relationship between those two cases, or point me to the source record that resolves it? We will
retain the answer as provenance evidence and disclose BUS-BRA in the project and challenge materials.

Thank you,
Aditya Raut

## Internal rights review assignment

The team rights authority should record decisions only after checking:

- BUS-BRA 1.0, Zenodo record 8231412, DOI `10.5281/zenodo.8231412`;
- archive size 133,917,740 bytes and MD5 `1f8b2be6476d58fc97bfb5e5a1ea9bab`;
- the recorded Zenodo API license identifier `cc-by-4.0`;
- the official MMBU requirement to disclose training datasets;
- the planned public Hugging Face checkpoint and method/data disclosure; and
- whether source labels, masks, derived boxes, review records, or other source material would be redistributed.

The completed form must contain exact attribution wording and exact redistribution conditions. This review is a team
decision about the planned uses. It isn't legal advice.

## Current blocker

The packet builder and validator are ready. The packet itself hasn't been opened in this workstream. Progress now
depends on naming the primary medical reviewer, secondary medical reviewer, source-author or data-steward contact, and
team rights authority. Until those people and their evidence locations are known, BUS-BRA remains a candidate source
with no model-use purpose.
