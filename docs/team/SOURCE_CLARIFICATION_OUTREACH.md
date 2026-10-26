# Source clarification and reviewer outreach

**Sent:** October 23, 2026, before 23:40 CDT
**Status:** one substantive reply received; four source/reviewer questions remain unanswered and one reviewer sent an automatic absence notice
**Evidence class:** communication dispatch and retained reply record; no admission or review authority

Six targeted messages were sent from the team Gmail account. This record preserves who was contacted and the exact
decision gap each message is intended to resolve. A sent message is not a reviewer agreement, source clarification,
license decision, source admission, purpose authorization, or permission to open data.

## Medical-review recruitment

| Recipient | Public qualification evidence | Request | Current state |
| --- | --- | --- | --- |
| [Dr. Nicole Stranch](https://www.uthsc.edu/graduate-medical-education/residency-and-fellowship-programs/coordinators.php) | Public UTHSC/Memphis breast-imaging fellowship materials name her fellowship director | Discuss serving as the primary reviewer for the frozen 244-record BUS-BRA sample or refer another qualified breast-imaging physician | Sent; no agreement or review authority exists until a reply and qualification/conflict evidence are retained |
| [Dr. Margaret Szabunio](https://medicine.uky.edu/users/mmsz222) | University of Kentucky profile identifies her as Professor of Radiology and Chief, Division of Breast Radiology | Discuss serving as the independent reviewer for the 50 mandatory BUS-BRA exceptions and escalated records, or refer another qualified reviewer | Automatic absence notice received October 23; no agreement, referral, or review authority exists |

The outreach describes the fixed clinical-review scope: image interpretability, mask usability/completeness, clinical
plausibility of the recorded pathology and BI-RADS fields, and shortcut artifacts. It does not ask either recipient to
diagnose a patient, certify a model, decide rights, or approve clinical use.

## Source-author and steward clarifications

| Source | Recipient | Exact clarification requested | Current state |
| --- | --- | --- | --- |
| BUS-BRA 1.0 | [Dr. Wilfrido Gómez-Flores](https://aapm.onlinelibrary.wiley.com/doi/10.1002/mp.16812), corresponding author | Whether cases 110 and 536 are distinct acquisitions, share patient/acquisition lineage, must be co-assigned, or should be excluded; request the resolving source record if available | Sent; the existing provenance blocker remains unchanged |
| NCT-CRC-HE-100K / CRC-VAL-HE-7K | [Dr. Jakob Nikolas Kather](https://doi.org/10.1016/j.ccell.2026.05.014), source lead | Whether every patch maps to a source slide or patient, whether the 86 source slides represent 86 distinct patients, and whether the 50-patient confirmation cohort retains usable parent identity | The original mailbox auto-replied that it was unmonitored and supplied a corrected author address; the unchanged bounded question was resent to the corrected author address on October 26. No substantive answer exists, so PathMNIST remains ineligible for decision-bearing use until complete parent grouping is evidenced |
| PathMNIST-224 | [Dr. Jiancheng Yang](https://jiancheng-yang.com/), MedMNIST lead | Whether the published source-image mapping preserves enough information to recover the NCT-CRC slide/patient parent for every patch and whether an additional grouping field or mapping is recommended | Reply received October 26, 2026: the CSV maps samples to original patch IDs, but the response does not supply slide/patient IDs and refers that question to the original NCT-CRC-HE-100K authors. Retained in `outputs/source-clarification-replies/pathmnist-medmnist-2026-10-26.json`; PathMNIST remains blocked for decision-bearing development use |
| BUS-UCLM v3 | [Dr. Noelia Vállez](https://www.nature.com/articles/s41597-025-04562-3), corresponding author | Which of the conflicting CC BY 4.0 and CC BY-NC 4.0 statements governs v3 and trained-adapter release; whether four-letter prefixes are patient IDs covering every derived view; whether `Doppler=Y` means `Yes` | Sent; license and schema clearance remain failed |

## Reply handling

For every response:

1. retain the complete message with sender, recipients, subject, timestamp, and quoted question;
2. distinguish a direct answer from an inference, referral, or personal opinion;
3. record which exact source version, files, records, purposes, and release paths the answer covers;
4. keep unanswered parts unknown;
5. require an independent rights decision for competition use and trained-weight release even when an author describes
   a license; and
6. route medical-review volunteers through the frozen reviewer qualification, conflict, opening, and attestation
   process before any image is opened.

No reply may directly edit the active registries. It becomes candidate evidence for a separately reviewed, sealed
successor record.

## Follow-up rule

Do not send another message before October 30, 2026 unless a delivery failure supplies a corrected contact route. If
there is no response by then, send one short follow-up in the existing thread. Do not expand to mass outreach; add a
new qualified candidate only when the first contact declines, bounces, or remains silent after the follow-up.
