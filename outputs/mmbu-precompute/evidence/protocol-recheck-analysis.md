# Analysis of the October 4 official-source recheck

**Conclusion: no registered protocol conflict is resolved by these captures.** The official dataset revision remains `069da7bbd6201a867039b548f3c02e103711ed4a`. The card's substantive visible body is unchanged from the saved October 3 HTML. Existing explicit engineering profiles remain useful; neither a later retrieval time nor an empty open-issues response supplies an authoritative choice between conflicting sources.

This read-only analysis used the already saved primary HTML/API responses in `work/protocol-recheck-2026-10-04`, their acquisition receipt `evidence/protocol-recheck-2026-10-04.json`, the prior card capture, and `configs/protocol-register.json`. No new network request, terms acceptance, message, issue submission, registry change or challenge-example access was performed.

## Evidence checked

The receipt records HTTP 200 retrievals on October 4, 2026, at approximately 18:12:57 UTC. All four saved file lengths and SHA-256 values were independently recomputed and matched it:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `challenge.html` | 58,959 | `6f70738ac6788ad473494a4fd5744243d0f0dfc58478a052ae197efbaae38831` |
| `public-api.json` | 190,269 | `23200375b90d6befe6e53af60bae77a712de5bab8b88a47628fd97eae33d6ea7` |
| `public-card.html` | 138,827 | `33b3d27382292aa52542d2882053fa12e95aa21f1f61d5055dd694b9f861e1d8` |
| `github-issues.json` | 2 | `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945` |

The [public dataset API](https://huggingface.co/api/datasets/mmbu/mmbu-public) still reports the same repository SHA, `lastModified: 2026-10-03T20:33:16.000Z`, `private: false`, `gated: auto`, and card license `other`. Its 3,151 sibling entries consist of 3,147 image paths plus `.gitattributes`, `README.md`, `metadata.jsonl` and `metadata.tsv`. The listing contains no executable context evaluator or harness file. Public metadata visibility does not bypass the dataset's gated access conditions.

The card comparison used Python's standard-library HTML parser to omit `script`/`style` data, retain visible block boundaries, collapse whitespace within lines, and select the body from the exact `MMBU-public` heading through the `metadata.tsv` description. Both October 3 and October 4 normalized bodies are byte-identical with SHA-256 `6a707043d0193890b1a04be43b80bffda7615aeb152c8202121f4ea9cb63f8bc`. Raw HTML hashes can differ because page wrappers or dynamic counters differ; that is not a contract change.

The [open GitHub issues endpoint](https://api.github.com/repos/akiranishii/mmbu-challenge/issues?state=open&per_page=100) returned exactly `[]`. This establishes no open entries in that endpoint at retrieval time. It says nothing about closed issues, discussions, private correspondence, office hours or later answers. In particular, absence of an open clarification issue is not organizer approval.

## Disposition by registered question

| Register item | Evidence in the new captures | Disposition |
| --- | --- | --- |
| PROTO-01: rationale placement | Card `Prompt` still places rationale before the final answer-only JSON object. It does not amend the earlier brief's answer/rationale JSON example or identify which governs the final harness. | Unresolved contradiction; keep explicit local profiles separate. |
| PROTO-02: malformed output | Card `Scoring` still sends missing/invalid JSON to raw-reply scoring. The brief's zero-credit rule has not been explicitly withdrawn. | Unresolved contradiction; no official-equivalent failure grading. |
| PROTO-03: multiple segmentation labels | Card segmentation suffix still permits several labels, while the shown judge's grounding gate asks for a single unambiguous concept. No multi-label reconciliation or test cases were added. | Unresolved internal inconsistency; preserve labels without asserting grades. |
| PROTO-04: context implementation | Site FAQ confirms separate task and biomedical-context passes and names six metadata categories. The card still documents task prompting/scoring only. No executable context prompt/schema, annotation mask, unknown policy or zero-field rule appears. | Unresolved implementation/coverage gap; high-level two-pass intent is reconfirmed. |
| PROTO-05: public-dev use | Site FAQ describes local evaluation on public development data and warns final private scores differ. Its short rules prohibit training on hidden examples and defer full rules to the brief. The gated card's technical split remains `train`. No explicit checkpoint/hyperparameter-selection permission or amendment to the brief's restrictions appears. | Unresolved permission boundary; local-evaluation intent does not authorize training/selection. |
| PROTO-06: task routing/detection | Card still distinguishes counting and region tasks, preserves already drawn regions, specifies displayed-image pixel xywh boxes and maximum pairwise IoU with a 0.5 cutoff. It adds no authoritative resize/inverse-transform implementation, empty-target rule or task-group reconciliation. | Existing provisional engineering information is reconfirmed; final matching/aggregation contract remains unresolved. |

Sources: the [saved official card's current public page](https://huggingface.co/datasets/mmbu/mmbu-public), [challenge site](https://akiranishii.github.io/mmbu-challenge/), and the earlier [challenge brief](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf) positions already recorded with page locators and hashes in the protocol register. This analysis did not refetch the PDF, so it makes no claim that its remote bytes were revalidated on October 4.

## Other reconfirmed facts and limits

The site repeats the domain-adaptation formula, separate T/C passes, tie-breaking on T, disclosed base, single end-to-end model, official-harness-only evaluation, and no evaluation-time ensembles/retrieval/web/tools. It names Sonnet-5; the card uses the `claude-sonnet-5` label. These are source-reported identifiers, not an executed judge calibration or a pinned immutable judge-runtime revision. The site links the brief, paper and registration page, but the inspected links do not supply a harness repository or a revised executable specification.

Nothing in these captures resolves generation/thinking settings, resolution/token limits, base/final loading settings, exact environment constraints, contributor-source overlap permission, or permissible handling of already medically adapted initialization. It remains appropriate to keep real source use and official-dev permission unapproved, preserve raw replies, avoid inferred failure/zero-context policies, and obtain explicit organizer clarification before official-score or eligibility claims. The existing organizer-question draft remains relevant and unsent.
