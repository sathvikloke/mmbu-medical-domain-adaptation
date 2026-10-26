# BUSI-WHU clinical, annotation, and confirmation-admission design

**Status:** prospective design only; no biomedical payload opening, source admission, model use, training, or confirmation execution is authorized  
**Source:** BUSI-WHU v3, DOI `10.17632/k6cpmwybk3.3`  
**Mechanical predecessor:** job `86066`, inventory digest `8df0b10e95b2cee3dcb3bd55754c42633a56b6f63fe2cf21b7105f5f3532f6f5`  
**Role:** independent confirmation only

## Intent

Turn the mechanically complete BUSI-WHU workbook/image/annotation join into defensible confirmation evidence without allowing the confirmation source to influence training, candidate selection, prompting, hyperparameters, or rescue decisions. The review must distinguish five questions that cannot substitute for one another: file integrity, image interpretability, pathology-label plausibility, annotation usability, and rights/purpose authorization.

The project seeks competition-grade evidence, not a decorative checklist. Review failures therefore exclude records, narrow tasks, or reject the source; they are never repaired by AI inference or silently averaged away.

## Known population

The protected metadata inventory contains exactly:

- 927 joined workbook/image/annotation records;
- 816 patient groups;
- 560 benign records from 560 patients;
- 367 malignant records from 256 patients;
- 778 single-record patients and 38 multi-record patients;
- 149 records belonging to the 38 multi-record patients; and
- one to nine records per patient.

These counts are metadata and custody evidence only. They do not assert that any image, label, or mask is clinically correct.

## Non-negotiable role isolation

BUSI-WHU remains confirmation-only. No image, annotation, label distribution beyond the already opened bounded metadata, reviewer decision, error pattern, or confirmation result may change:

- the training-source mixture;
- model or adapter selection;
- prompt text or parser;
- optimizer, exposure, or seed settings;
- candidate ranking; or
- the decision margin.

The candidate, three adapted checkpoints, prompts, eligible population, exclusions, duplicate dispositions, and exact confirmation rule must be locked before model outputs are produced on BUSI-WHU. Any post-opening change retires the confirmation and requires a new untouched source.

## Review population and reviewer assignment

### Primary review

One qualified breast-ultrasound reviewer examines all 927 records. This prevents an unreviewed tail from entering confirmation merely because a sample looked clean.

### Independent second review

The second reviewer examines a frozen enriched subset consisting of:

1. every record from all 38 multi-record patients, totaling 149 records;
2. 50 benign single-record patients selected by ascending SHA-256 of `busi-whu-review-v1\0<parent_id>`; and
3. 50 malignant single-record patients selected by the same rule.

The resulting second-review population is exactly 249 records from 138 patients. The selection uses only sealed patient identifiers and labels, never pixels or reviewer outcomes. The second reviewer also examines every record flagged by the primary reviewer, even when it falls outside the 249-record set. Added flagged records expand review coverage but do not replace any frozen record.

### Adjudication

A distinct qualified adjudicator resolves every disagreement in interpretability, label plausibility, annotation usability, task eligibility, or final disposition. Majority vote is forbidden. The adjudicator records a complete decision vector and rationale after seeing the two independent decisions.

Reviewer identity, breast-ultrasound qualification, conflict disclosure, review timestamp, and evidence locator are mandatory. AI systems cannot fill a reviewer or adjudicator role.

## Protected opening and automated checks

Any real decode requires a new digest-bound authority packet. The one-shot CPU opening must bind the exact two acquired artifacts, job `86066` evidence, tested code commit, reviewer assignment, frozen 249-record subset, and output schema. Before human review, software must check all 927 pairs for:

- strict BMP decode and matching image/annotation dimensions;
- nonempty, finite dimensions within a frozen ceiling;
- binary or explicitly enumerated annotation values;
- nonempty annotation extent;
- deterministic tight half-open annotation box;
- workbook geometry consistency as QA evidence, never an automatic correction;
- exact and perceptual duplicate candidates at both record and patient level; and
- absence of cross-patient duplicate groups from any later confirmation split.

The opening may create immutable review assets and worksheets. It may not train, load a model, access MMBU public content, select a candidate, or grant admission.

## Per-record clinical review

Each assigned reviewer answers every field independently:

1. Is the image an interpretable breast-ultrasound view?
2. Is the benign/malignant source label clinically plausible for the displayed record, without asking the reviewer to recreate histopathology?
3. Does the annotation mark the intended lesion?
4. Is the annotation sufficiently complete for lesion-grounded classification?
5. Is it sufficiently complete for mask-derived localization?
6. Is there another visible lesion or incomplete-instance annotation that invalidates a single-target claim?
7. Does the image contain text, calipers, overlays, panels, crops, or acquisition artifacts that could create a shortcut?
8. Are `modality=ultrasound`, `body_part=breast`, and `medical_domain=breast imaging` supported?
9. Which exact tasks are permitted: global benign/malignant classification, lesion-grounded classification, localization, and context prediction?
10. Final disposition: eligible for named tasks, narrow to named tasks, exclude, or unresolved.

Review never changes the source label or redraws a mask. A suspected wrong label or annotation is excluded or escalated; it is not repaired by guessing.

## Source-level kill and narrowing rules

The source is rejected for confirmation if any of these occurs:

- the patient/image/annotation bijection fails;
- a systematic label inversion, label leakage, or patient-identity defect is found;
- an unresolved cross-patient duplicate can cross the locked confirmation boundary;
- any reviewer qualification or chronology requirement is unmet;
- the rights decision does not explicitly approve confirmation use and challenge reporting; or
- the eligible population falls below the frozen minimum of 60 independent patients.

Task-specific annotation failures narrow the task instead of being hidden. Global classification may remain eligible when a mask is unusable, but grounded classification and localization require a usable intended-lesion annotation. Every unresolved reviewed record is excluded. No aggregate pass rate can override a systemic defect or an unresolved material disagreement.

## Purpose and release decisions

A separate accountable team authority reviews the exact v3 record, CC BY 4.0 terms, required citation and attribution, source-derived label/mask handling, competition disclosure, result reporting, retention, and any public checkpoint implications. Decisions for confirmation evaluation, challenge submission, publication, source-derived artifact redistribution, and trained-weight release are recorded separately as `approve`, `narrow`, `decline`, or `unresolved`.

This review is governance evidence, not legal advice. An unresolved purpose remains forbidden.

## Outputs

The protected workflow produces immutable, digest-bound artifacts:

- full-corpus decode and annotation-integrity inventory;
- duplicate-candidate inventory and independent dispositions;
- frozen 249-record second-review manifest;
- primary, secondary, and adjudication worksheets;
- completed source-level rights/purpose decision;
- exact eligible record and patient manifests by task;
- exclusions with reason codes;
- review-validation report; and
- a pending admission candidate that still records `source_admission_authorized=false`, `training_ready=false`, and `model_use_authorized=false`.

A separate Phase 1 admission record must authenticate the evidence and grant only the confirmation purpose. Training use is never granted to BUSI-WHU under this design.

## Success condition

Success means the repository can prove, before any model output is produced, exactly which independent patients and records are eligible for which confirmation tasks, why exclusions occurred, who reviewed them, what rights decisions apply, and that nothing from BUSI-WHU influenced model development. It does not mean the model wins, the confirmation passes, or the project is ready to submit.
