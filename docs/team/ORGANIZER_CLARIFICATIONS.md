# Organizer clarifications

This register records direct organizer answers separately from public rules and planning assumptions. It combines the
team email received October 14, 2026 with the authenticated read-only
[Discord rule audit](DISCORD_RULE_AUDIT_2026-10-24.md). Neither substitutes for a final harness or later organizer
amendment.

The binding privacy-preserving evidence pointer is the
[sanitized organizer clarification receipt](../phase1/ORGANIZER_CLARIFICATION.md). It records the reviewed authority
digests and deliberately omits contact identities, message locators, and benchmark examples; this readable table must
not silently add precision absent from that receipt or the retained private thread.

## Confirmed on October 14, 2026

| Topic | Organizer answer | Team policy |
|---|---|---|
| Public development set | Results may influence base-model, recipe, and hyperparameter selection, although the organizer warned that overfitting may not generalize to the private set. | Keep the stronger public-set firewall for model and recipe development. Do not use MMBU examples, outputs, labels, annotations, or derivatives for optimization or selection. A frozen-model audit, if later authorized by the team, is reporting evidence only. |
| Prompt and harness | The organizer said the prompt version should be provided on Hugging Face, pointed to a JSON example in the brief, said the context prompt was still being finalized, and described evaluation as a single call with no tools and no harness. The task prompt/schema was later observed separately on the October 17 public card. | Pin the final task and context prompt bytes and brief example before protocol-equivalent claims. Exact task/context call topology remains unresolved until the final context protocol is bound. |
| Malformed JSON | The October 6 Discord answer explicitly says official scoring will not fall back to the raw reply. The October 14 direct email independently says malformed JSON is incorrect. Together they supersede the conflicting public-card fallback text observed at README revision `b2faa991...`. | Preserve raw output and treat malformed committed JSON as failure; never repair it. |
| Context fields | The model is prompted only for applicable fields. An example without a stain field will not be asked for stain. | As a local fail-closed proxy policy, return exactly the requested field set and never invent non-requested values. Extra-key, missing-key, unknown-value, and zero-applicable-field scoring remain unresolved. |
| Detection with multiple ground-truth boxes | When the question says “any one,” emit one box. It is correct if IoU is at least 0.5 with one ground-truth box. | Use the confirmed any-one rule for those rows. Keep every-target behavior separate and only where explicitly requested. |
| Duplicate public images | The organizer acknowledged the two reported cases and said they would investigate; this reply supplied no correction, exception, or scoring disposition. | Keep both cases quarantined from local protocol claims until a later dated correction or exception is issued; later metadata drift alone does not resolve them. |
| Training splits from contributing datasets | Independent training splits may be used. October 2 and October 18 Discord answers also permit disclosed public/original-source training data despite possible MMBU-source overlap. No organizer overlap-exclusion service is provided. | Use only independently acquired, rights-reviewed records. Keep source, split, parent, and image hashes, and exclude known MMBU public examples and derivatives despite the absence of an organizer-supplied hidden-overlap check. |
| Starting checkpoint | An October 13 Discord answer permits either a base checkpoint or an already fine-tuned checkpoint and states that improvement is measured relative to the selected starting checkpoint. | Eligibility does not select the base. Retain the frozen adaptation-response frontier and disclose exact starting lineage. |
| Registration | Complete; no further team action required. | Record final members in the later organizer form. |
| Submission | A form will collect model/team/data details, and the model will be uploaded to Hugging Face. More instructions were expected in early December. | Prepare a fresh-loadable checkpoint and lineage-backed local disclosure worksheet, but do not assume repository visibility or upload without a separate user-directed release step. |
| Deadline | The email confirms Pacific Standard Time; the October 3 pinned Discord answer states December 31 at 23:30, the end of the Luma window. | Treat December 31, 2026 at 23:30 PST as the best current written cutoff, retain an earlier internal freeze, and verify the final form display. |
| Track 3 size rule | MoE models may have up to 12B total parameters with no more than 4B active at inference. The organizer identified the Qwen 3.5 4B class, approximately 4.6B actual parameters, as the maximum for “this category.” This appears responsive to the dense-limit question, but the quoted category wording is not a general parameter-count formula. | This answer concerns Track 3, not the Medical Domain Adaptation model choice. Preserve the class-based wording until formal rules incorporate it. |
| Discord evidence | The October 24 read-only audit records the exact server/channel/message locators, author, timestamp, observed pin state, and rule-bearing content for the material statements. | Use the dated audit for governance while retaining unresolved final-harness and Pass 2 questions. |

## Later public metadata drift

Pinned Discord messages announce a replacement public revision on October 4, followed by another roughly 50-row
improvement round on October 9. On October 23, the public repository API reported head
`d11326436d37a9a560549156bf205ef1b120aa36`, and the
Files and versions listing attributed both metadata files to an October 21 commit stating that 904 rows gained reviewed
closed-VQA options in the open judge label set. `README.md` remained attributed to `b2faa991...`. This is a public
revision observation, not a direct organizer clarification. It changes score comparability and must be pinned in any
report, but it does not resolve malformed-output, multi-label, context, runtime, or loader questions.

## Still unresolved

- Final context-prompt bytes and version.
- Final executable evaluation harness, if any, and dependency/runtime envelope. The current task card is transcribed in
  [the dated task-protocol snapshot](TASK_PROTOCOL_SNAPSHOT.md), but no raw-byte or runtime receipt exists.
- Exact hardware, memory, image-resolution, input/output-token, timeout/runtime, precision/quantization, dependency,
  thinking-mode, and generation settings; the unaudited Discord pointer does not resolve them.
- Disposition of the two reported duplicate-image inconsistencies.
- Exact upload form and disclosure granularity, Hugging Face destination/ownership/visibility/layout, edit policy,
  validation procedure, and receipt behavior. The project's detailed local inventory is conservative policy, not an
  organizer-confirmed form schema.
- Exact disclosure fields and loader treatment for an already medically adapted starting checkpoint, even though broad
  eligibility and base-relative comparison are now organizer-confirmed.
- Whether adapters, modified vision towers/projectors, or other changed modules are accepted by the evaluation loader,
  how they must be packaged, and how they must be disclosed.

Any later answer supersedes this register only when its source, timestamp, and exact wording are retained.
