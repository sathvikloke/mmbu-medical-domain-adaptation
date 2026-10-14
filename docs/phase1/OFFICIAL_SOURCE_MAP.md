# Official-source extraction receipt

**Status:** sanitized rule extraction for Phase 1 governance; not example data and not an executable official harness  
**Reviewed:** 2026-10-14  
**Origin class:** `official_rule_summary`

## Source identities

| Source | SHA-256 | Reviewed spans |
|---|---|---|
| `MMBU_challenge_update.pdf` | `68fb4c2685d3d3b501da6f92f0906f970d851b596e98fddede26fb6e2b6e4ba0` | pages 3, 5–12; rule-bearing text only |
| `mmbu-challenge-official-rules.pdf` | `30fb3241bd331eeaf0602b4ec24faf66b50f97c5d430cf814fdda80d62b80c8e` | pages 1–2; sections 1–11 |

An authenticated October 9 registered-team organizer bulletin, held outside this sanitized clone, directs teams to the challenge website and pinned Discord messages for details and answers. This metadata is an external audit warning, not clone-resident rule authority: the bulletin bytes and current pinned posts are not yet captured or hashed here. A Discord clarification can become contract authority only after an authorized read-only capture records exact content bytes or screenshot hash, organizer identity, server/channel, timestamp, pin state, and scope, followed by a reviewed contract revision.

Mutable website and Luma observations are likewise external freshness warnings, not support for any assertion in the binding map below, because their reviewed bytes are not in this manifest. They may identify a conflict or trigger recapture, but only a hashed capture added by reviewed contract revision may supply rule authority.

The exact seven-member manifest in this directory pins this receipt alongside the other binding Phase 1 contract members. A source-byte or receipt-byte change requires a new contract revision and review.

## Sanitized assertion map

| Contract assertion | Primary locator |
|---|---|
| Four task families; detection uses `[x, y, width, height]` and IoU at least 0.5 | brief page 3 |
| Track 2 is medical domain adaptation; the exact base must be disclosed; the brief describes an API-key evaluation route for models above 27B active parameters while Rule 1 gives public/ungated release wording for models below 27B. Whether both obligations apply above 27B and the treatment of exactly 27B are unresolved. | brief page 5 read with page 10 Rule 1 |
| Task and biomedical-context evaluation are independent passes; six possible context fields are scored only when annotated | brief pages 6–7 |
| Malformed or unparsable JSON gets no credit in the affected pass | brief page 7 and page 11 Rule 8 |
| Task grades may be fractional; context is averaged within example and then across examples | brief page 8 |
| Track 2 score is `(0.8T + 0.2C)(T - B)` and the organizer evaluates adapted and base models under identical conditions | brief page 9 |
| Sub-27B Track 2 models use the public ungated Hugging Face route; active counts include vision, language, multimodal projection, and adapters | brief page 10 Rule 1 |
| One checkpoint may enter only one track | brief page 10 Rule 2 |
| One end-to-end VLM is required; ensembles, cascades, auxiliary models, external OCR, retrieval, learned preprocessing/postprocessing, and orchestration are prohibited; multiple vision encoders are allowed when counted | brief page 10 Rule 3 |
| External information/tool APIs are prohibited during evaluation; the >27B submitted-model serving endpoint is a separate published route | brief page 10 Rule 4 read with Track 2 on page 5 |
| Official harness/settings, one processing pass, and no repeated sampling, self-consistency, iterative prompting, test-time adaptation, or weight modification | brief page 10 Rule 5 |
| MMBU examples, labels, annotations, and derivatives cannot be used for training, checkpoint selection, or optimization; major training sources and known overlaps must be disclosed | brief page 10 Rule 6 |
| Organizer inference uses BF16 or FP16; one frozen final model must be designated and uploaded per track before the deadline | brief pages 10–11 Rule 7 |
| Hardware, memory, runtime, and inference constraints are organizer-specified; participant failures do not automatically receive reruns | brief page 11 Rules 8–9 |
| Team acceptance, one-team membership, anti-collusion, and evaluation-integrity requirements | brief page 11 Rules 11–14 |
| Registration closes October 31, 2026; submission deadline is December 31, 2026; exact cutoff time/timezone is not supplied. | official rules page 1 section 3 |
| Prize/conflict exclusions include GXL, Anthropic, AWS, Highlanders, Biohub, Stanford AI Lab, organizers, holders of hidden evaluation material, judges/reviewers/evaluators, and Stanford MARVL | official rules page 1 section 5 |
| Entry requires model outputs and a short method write-up through Hugging Face | official rules page 1 section 6 |
| Participants retain model/code ownership and grant publication rights for team name, scores, and method summary | official rules page 2 section 9 |

## Excluded content classes

This extraction excludes all example images, example questions, answers, labels, example IDs, public-set row statistics, duplicate analysis, benchmark outcome statistics used for model selection, and example-derived design choices. It includes only rule/contract language and non-example release metadata.

The source PDFs contain figures and benchmark discussion. Their presence does not transfer those contents into this receipt. Developers use this receipt and `CONTRACT.md`, not the source PDFs, for Phase 1 governance.

## Review attestations

| Reviewer | Review mode | Disposition |
|---|---|---|
| Codex primary audit | Independent claim-to-page review of the saved PDF extraction and rendered rules pages | accepted as sanitized machine-assisted bootstrap review |
| `/root/competition_research` | Separate rule/competition red-team against the live sources and saved hashes | accepted as sanitized machine-assisted bootstrap review |

These are two independent machine-assisted reviews, not human legal advice and not an organizer ruling. A named human reviewer must sign any later legal, prize-eligibility, source-rights, or submission decision that requires human authority.

## Known unresolved items

- exact official harness commit, prompt bytes, task JSON property names, parser details, judge rubric, and runtime limits;
- exact submission destination, output-production workflow, receipt, and deadline timezone;
- adapter-only versus merged/full-weight eligibility;
- quantized stored-weight and mixed-kernel eligibility;
- treatment of independent training splits from MMBU-contributing source datasets;
- exact active-parameter definition for any future MoE candidate;
- whether above-27B models require both public/ungated Hugging Face release and an API, and the treatment of exactly 27B;
- current rule-bearing pinned Discord clarifications and office-hour notices; no irreversible rule-sensitive choice may treat this source inventory as complete until an authorized capture is reviewed.

Authority precedence is: later formal rules or a scope-specific written organizer clarification/material-change notice; then the published challenge brief and current official site for nonconflicting statements; then provisional summaries. Captured pinned organizer posts and written bulletins enter at the scope their text supports, never by channel name alone. Conflicts are quarantined rather than silently resolved.

An unresolved item stays unresolved until a written organizer artifact or authenticated captured pin is added with its own hash, author/channel, timestamp, scope, and contract revision.
