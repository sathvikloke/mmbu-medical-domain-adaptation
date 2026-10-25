# MMBU Discord rule audit — October 24, 2026

**Status:** authenticated read-only UI observation; useful rule evidence, but not a raw-byte export or executable harness  
**Server:** `MMBU Challenge` (`1544916153951060058`)  
**Primary channel:** `#general` (`1544916155947290818`)  
**Audited channels:** `#general`, `#ask-gxl`, `#anthropic-help`, `#office-hours`, `#solo-builders`, and `#ideas`

The audit used the registered team's logged-in Discord session. No message was sent, edited, reacted to, downloaded, or
forwarded. `#anthropic-help` and `#office-hours` were empty at the observed time; `#solo-builders` contained team-matching
messages; `#ask-gxl` concerned Paperclip access; and `#ideas` contained one organizer recommendation to read Microsoft's
OctoMed paper when designing training-data recipes. The rule-bearing material was in `#general` and its three pinned
messages.

## Dated organizer evidence

Every link below points to the exact Discord message observed in the authenticated UI. “Pinned” describes the state
visible on October 24, not a promise that the pin will remain.

| Date | Pin | Message | Verified rule signal | Conservative project consequence |
|---|---|---|---|---|
| Oct 2 | yes | [welcome and submission route](https://discord.com/channels/1544916153951060058/1544916155947290818/1555642393653411852) | Entrants must train an autoregressive VLM; a later form will collect team/submission information; models will be uploaded to Hugging Face; multiple-track entries require distinct models; organizers encouraged use of MMBU Public for internal evaluation and independent training data. | Keep the single-track plan and local public-set firewall. Treat the form and upload layout as unresolved until released. |
| Oct 2 | no | [evaluation harness](https://discord.com/channels/1544916153951060058/1544916155947290818/1555655213011177625) | The organizer said there was no official harness and directed teams to the Hugging Face prompting guide. | No local evaluator may be called official-equivalent without a later pinned harness/runtime. |
| Oct 2 | no | [public training data](https://discord.com/channels/1544916153951060058/1544916155947290818/1555657450059862099) | Public datasets are permitted with disclosure; the same answer conditioned permission-related data on permission, disclosure, and de-identification. | Rights, privacy, versioning, grouping, and disclosure remain local admission gates. |
| Oct 3 | yes | [format, tasks, dev use, and deadline](https://discord.com/channels/1544916153951060058/1544916155947290818/1556045387125624874) | JSON is the output format; counting is grouped into ungrounded classification; the dev set is open-VQA; checkpoint selection may use public-dev results without training on the set; the stated deadline is December 31 at 23:30; Track 3 alpha is 0.1. | Preserve strict JSON, counting coverage, and the stronger no-public-optimization policy. Combine 23:30 with the separate organizer-confirmed PST timezone, but verify the final form display before release. |
| Oct 4 | yes | [public-set revision](https://discord.com/channels/1544916153951060058/1544916155947290818/1556439953599238299) | The organizer announced a replacement at the same public-dataset URL with fixed or reworded questions. | Every public result requires an immutable dataset revision; scores across revisions are not silently comparable. |
| Oct 6 | no | [checkpoint and malformed-output precedence](https://discord.com/channels/1544916153951060058/1544916155947290818/1556896546543501366) | The organizer again permitted dev-based checkpoint selection but warned against using it as the sole metric, and stated: “Official scoring will NOT fall back to the raw reply.” The same message said the Pass 2 prompt would be shared later. | Malformed committed JSON is organizer-confirmed incorrect. The later Pass 2 statement conflicts with the Oct 3 claim that its prompt was already in the brief, so exact context bytes remain unresolved. |
| Oct 9 | no | [additional public-set edits](https://discord.com/channels/1544916153951060058/1544916155947290818/1558157942371389612) | The organizer reported another improvement round affecting roughly 50 public rows for specificity and option quality. | Freeze revision identity before any report; never pool or compare results from unknown revisions. |
| Oct 13 | no | [starting checkpoint](https://discord.com/channels/1544916153951060058/1544916155947290818/1559716675845357690) | Teams may start from a base model or an already fine-tuned model, but improvement is measured relative to the selected starting model; the organizer recommended a base checkpoint because a medical checkpoint may be harder to improve upon. | This resolves broad starting-checkpoint eligibility, not the best base. Retain the prospective adaptation-response frontier and disclose complete starting lineage. |
| Oct 18 | no | [distinct multi-track checkpoints](https://discord.com/channels/1544916153951060058/1544916155947290818/1561390854906716221) | Different tracks require separately trained, distinct checkpoints; Track 3 includes an efficiency term. | Continue focusing on Track 2 and do not reuse an artifact across tracks. |
| Oct 18 | no | [original source datasets](https://discord.com/channels/1544916153951060058/1544916155947290818/1561603393569693707) | In response to whether original source-dataset train splits may be used despite MMBU-source overlap, the organizer answered that this is allowed with disclosure. | Contributor proximity is not an automatic ban. Preserve independent acquisition, split/group lineage, rights review, disclosure, and the stricter MMBU-content firewall. |

## What remains unresolved

- Exact final Pass 2 prompt bytes, field registry, parser, and biomedical-context judge.
- Any later official harness plus hardware, dependency, generation, timeout, precision, and loader requirements.
- Multi-label segmentation scoring and all context missing/extra/unknown/zero-field behavior.
- Final form schema, Hugging Face repository ownership/visibility/layout, edit policy, and validation receipt.
- Whether the final deadline UI displays exactly December 31, 2026 at 23:30 PST; the internal release freeze remains earlier.

This audit changes rule knowledge, not model evidence, novelty, or readiness by itself. A later organizer statement or
final harness supersedes it only when the new source and date are retained.
