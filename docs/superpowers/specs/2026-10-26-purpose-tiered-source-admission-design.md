# Purpose-tiered source admission design

## Intent

Unblock honest competition training on public biomedical dataset annotations without misrepresenting those annotations
as clinically validated ground truth. The current admission graph requires distinct clinical and visual QA attestations
for every proposed purpose, including training. That is stronger than the MMBU public-data rule, conflates two
different claims, and can freeze empirical progress even when exact rights, provenance, grouping, integrity, and
annotation-fidelity evidence exists.

## Decision

Admission remains fail-closed, but reviewer requirements become purpose-sensitive:

| Purpose class | Purposes | Required QA roles | Permitted claim |
| --- | --- | --- | --- |
| Engineering | `engineering` | visual QA | Mechanics on source-shaped records only |
| Dataset-annotation use | `train`, `release` | visual QA | The model used the exact publisher-provided annotations under the recorded limitations |
| Decision-bearing biomedical evidence | `adaptive_dev`, `confirmation` | distinct visual and clinical QA; adjudicator when disagreements exist | Performance on the reviewed biomedical endpoint within the frozen scope |

The project does not claim that publisher labels are clinically correct merely because they are usable for training.
Every training-facing report and model card must call them source annotations and retain the QA limitations digest.
Clinical/human-impact claims still require the existing qualified clinical review path.

## Goals

- Preserve exact artifact, rights, patient/group lineage, duplicate, custody, split, and purpose-authorization gates.
- Permit a training-only source to pass QA without a clinical reviewer when visual/annotation integrity passes.
- Continue requiring a distinct clinical reviewer for adaptive-development or confirmation use.
- Prevent a training-only receipt from being reused for confirmation or clinical-validity claims.
- Keep release-rights review independent from label clinical validity.
- Make the reviewer rule executable and adversarially tested rather than explained only in prose.

## Non-goals

- No real source is admitted by this change.
- No reviewer identity, signature, rights decision, QA outcome, or scientific value is fabricated.
- No MMBU public example is accessed and no public result guides a decision.
- No training, GPU use, model choice, track choice, upload, or submission is authorized.
- This does not weaken BUSI-WHU confirmation review or replace its clinical adjudicator.
- This does not turn an unreviewed source into a trusted clinical benchmark.

## Executable rule

`check_qa_receipt` always requires at least one approved `visual_qa_reviewer` attestation bound to the exact QA
receipt. If the receipt purposes contain `adaptive_dev` or `confirmation`, it additionally requires an approved
`clinical_qa_reviewer` attestation from a distinct role. Existing disagreement handling is unchanged: a nonzero
disagreement count requires the bound adjudicator attestation.

A receipt containing only `engineering`, `train`, or `release` must not be rejected solely because it lacks a clinical
attestation. Every other approval condition remains unchanged: frozen sampling, complete review, multiplicity-aware
thresholds, annotation-completeness disposition, shortcut probes, zero unresolved adjudications, chronology, opening
receipts, custody, rights, grouping, admission decision, and external source-admission authority.

The rule is monotone: adding `adaptive_dev` or `confirmation` increases evidence requirements. Removing a purpose
creates different canonical bytes and cannot preserve an earlier digest, lock, receipt, source transition, or
authorization.

## Claim boundary

Training-only admission supports only this statement:

> The exact public source annotations were used for competition training under the recorded provenance, rights,
> grouping, integrity, visual-QA, and limitation evidence.

It does not support “clinically correct,” “diagnostically valid,” “safe,” “expert verified,” or equivalent language.
Any evaluation used to select or confirm a biomedical result must satisfy the decision-bearing reviewer tier.

## Required tests

1. A train-only QA receipt with an approved visual reviewer and no clinical reviewer passes.
2. The same receipt fails when the visual reviewer is missing.
3. Adding `adaptive_dev` fails until a clinical reviewer is present.
4. Adding `confirmation` fails until a clinical reviewer is present.
5. Existing dual-review fixtures continue to pass unchanged.
6. Reviewer disagreement still requires a distinct adjudicator.
7. Documentation states that the relaxation admits no real source and authorizes no training by itself.

## Implementation surface

- `src/mmbu_phase1/admission.py`: centralize the purpose-to-required-QA-role projection and use it in
  `check_qa_receipt`.
- `tests/phase1/test_admission.py`: add direct positive and negative purpose-tier cases using the existing closed
  synthetic admission world.
- `docs/phase1/SCHEMAS.md`: document the purpose-sensitive reviewer rule and claim boundary.
- `docs/team/DECISIONS.md` and `docs/team/CURRENT_VERIFICATION.md`: record the change without changing the admitted
  source count, readiness rating, or execution authority.

## Self-review

The design deliberately does not create a shortcut around rights, grouping, custody, QA sampling, external authority,
or purpose authorization. Its only change is that a clinician is no longer required to certify labels that are being
used explicitly as publisher-provided training annotations rather than as decision-bearing clinical truth. The main
risk is semantic laundering after training; the explicit claim boundary and unchanged confirmation tier address that
risk, and the executable purpose projection prevents a training receipt from satisfying confirmation.

