# Decisions and unresolved gates

This is the team's human-readable register at handoff. The source records are the [protocol register](../../outputs/mmbu-precompute/configs/protocol-register.json), [source registry](../../outputs/mmbu-precompute/configs/source-registry.json), [model registry](../../outputs/mmbu-precompute/configs/model-registry.json), and [resource record](../../outputs/mmbu-precompute/configs/resources.json). All scientific owner roles below remain **unassigned** until the team records an assignment.

## Working decisions already supported

| Decision | Basis and limit |
| --- | --- |
| Keep the competition shortlist empty; retain the three pinned Qwen snapshots only as engineering subjects | Processor compatibility was tested, but no prospectively frozen model-selection decision and receipt or performance ranking exists. B1/Qwen2.5-VL-7B-Instruct is the exact Phase 1 native-runtime fixture; it is not a selected competition base. |
| Keep real sources and records pending | Rights, overlap, intended-use/release compatibility, and biomedical conversion review are incomplete |
| Preserve separate task/context/judge input builders and provisional output profiles | The published brief and public card conflict; neither silently overrides the other |
| Require explicit uint16 presentation and verified native assistant boundaries | Tested intensity-loss/scaling and Qwen3.5 thinking-prefix counterexamples |
| Use token-weighted shifted assistant loss and test actual trainer integration | Synthetic unequal-microbatch probe; trainer behavior remains unverified |
| Retain negative results and use one untouched confirmation after selection | Prospective research design and checked local receipt lifecycle |
| Demote QUILT from flagship to diagnostic branch | Independent adverse review plus LoRA-FA, GPM/InfLoRA, AND-mask/Fish/Fishr, R2F, and direct 2026 medical-VLM paraphrase-consistency antecedents; multiplicative loss scaling can make the estimated basis task-bearing. See [the binding disposition](QUILT_ADVERSE_REVIEW.md). |
| Select the competition base by a frozen adaptation-response frontier, not untouched performance | Track 2 score multiplies adapted task/context quality by base-relative task gain; base-only ranking is misaligned. The F0/joint-decision/F2 process remains public-firewalled and measures response to one fixed screen, not intrinsic adaptability. See [frontier](BASE_SELECTION_FRONTIER.md) and [red-team](BASE_SELECTION_REDTEAM.md). |
| Bind the October 25 competition reset to Track 2 and a four-model adaptation-response bake-off | The completed two-source shakedown proves mechanics but cannot select Qwen2.5-VL, an adapter arm, or a context objective. Qwen3-VL-8B, InternVL3.5-8B-HF, Qwen2.5-VL-7B, and OctoMed-8B enter the same staged protocol; gated sub-27B models are excluded. No larger run starts before the official-style context metric, data portfolio, exact revisions, compute cap, and stop rules in [the decision memo](COMPETITION_DIRECTION_DECISION_2026-10-25.md) are frozen. |
| Bind schema, freeze, and execution as separate states | The October 18 executability audit found that detailed prose still left context-missing behavior, confirmation closure, compute limits, and scientific values to the implementer. The [experiment-freeze contract](EXPERIMENT_FREEZE_CONTRACT.md) now blocks execution until the packet, literals, roles, decision function, and authorization are hash-bound. |
| Propose an answer-first candidate ladder for the next reviewed contract revision | A fresh three-AI-review audit found that task performance enters both factors of the official score while context changes only one. The proposal retains the exact matched B1-L/B2-P task-only and dual arms, but would let context co-training earn promotion only through task noninferiority and uncertainty-aware score improvement. It is non-executable and does not supersede the acknowledged handoff packet until a successor is resealed and independently acknowledged. See the [answer-first strategy](../superpowers/specs/2026-10-23-answer-first-evidence-coupled-strategy-design.md). |
| Freeze MOSAIC on the current source grid | The optimistic source-adjusted scaffold is rank deficient and aliases modality/specimen/task with source; adding records to the same cells cannot repair identifiability. A future crossed grid is a new evidence state and does not inherit the former rating. |
| Do not automatically implement a novelty probe | Exact searches found that CVPR 2022 already uses characteristic-function frequency supervision for count/position/subregions and that Divide and Count already enforces regional inclusion–exclusion/additivity. MRFSS and WRLVT fall to 5.2 and 4.8 concept novelty; neither justifies implementation before a prospectively frozen repeated B2/B4 residual on admitted, non-public external data, or a precisely cited independently replicated residual matching the task, modality, and constraints with a predeclared reason B2 cannot address it. |
| Close the scoped pre-evidence learner-mechanism search with zero survivors | An orthogonal second pass rejected scene-language compilers, acquisition-provenance factorization, and redundant semantic codewords against direct primary antecedents and score-breadth constraints. Reopen costly mechanism work only under the qualifying-residual rule above. Low-cost system, data-objective, and evaluation audit remains open but cannot alter frozen Lane 1 or consume GPU time. |
| Reject direct multiplicative-score training as novelty or a safe loss | Differentiating `(0.8T + 0.2C)(T - T_base)` produces only state-dependent task/context weighting, and the context coefficient is negative while task gain is negative. Use ordinary frozen dual-objective training; apply the score only after the positive-gain floor in prospective uncertainty-aware selection. |

## External evidence still needed

The October 14 organizer reply resolved part of the historical question draft. The authoritative sanitized governance
receipt is [Phase 1 organizer clarification](../phase1/ORGANIZER_CLARIFICATION.md), and the readable answer map is
[Organizer clarifications](ORGANIZER_CLARIFICATIONS.md). The older draft remains evidence of what was asked; it is no
longer an unsent next action. The October 6 Discord answer explicitly rejects raw-reply fallback and the October 14
direct reply independently says malformed JSON is incorrect, so local behavior remains fail-closed despite the
contradictory card text. Public-set selection is
organizer-permitted but locally forbidden by the stricter project firewall; independently obtained contributing-source training splits are allowed with
full disclosure; an explicit “any one” detection request takes one box and passes at IoU at least 0.5; enrollment is
complete; the best current written deadline is December 31, 2026 at 23:30 PST, pending final-form display verification.
The authenticated [Discord audit](DISCORD_RULE_AUDIT_2026-10-24.md) records exact message locators, timestamps, authors,
and observed pin state. None of these answers supplies a final harness or model result.

| ID / decision | Missing fact or deliverable | Blocks | Suggested workstream |
| --- | --- | --- | --- |
| PROTO-01: task prompt | Current card at visible README revision `b2faa991...` specifies rationale before a terminal answer-only JSON object and exact task suffix routing; current metadata head `d1132643...` separately expands judge label sets in 904 rows. The October 17 Discord transcript adds last-field selection and thinking-block removal. Raw card bytes, chat rendering, generation settings, exact extraction grammar, and an executable drift check are not yet receipted | Protocol-equivalent production serializer and schema-specific training; revision-matched score comparison | Model/evaluation |
| PROTO-02: malformed output | The October 6 Discord answer says official scoring does not fall back to the raw reply; the October 14 direct email independently says malformed JSON is incorrect. The conflicting card fallback is preserved as revision drift. | Exact final parser implementation and harness bytes | Model/evaluation |
| PROTO-03: segmentation labels | Current suffix allows comma-separated multiple labels while the displayed judge Gate 1 requires one specific label-set concept | Multi-label grading and score-based promotion | Model/evaluation |
| PROTO-04: context pass | Confirmed only that prompts request applicable fields. Final prompt bytes, field registry/mapping, key schema, unknown convention, extra/missing-key treatment, zero-field behavior, parser, scoring, and exact task/context call topology remain unresolved. | Official C and S claims | Model/evaluation |
| PROTO-05: public development | Organizer permits public-result-driven selection, but the project deliberately retains a stricter no-public-optimization firewall; gated access and exact custody still require authority | Authorized access and any later proposal to revise the stricter local policy | Review/release |
| PROTO-06: detection/routing | “Any one” is resolved as exactly one predicted box matched to any ground-truth box at IoU >= 0.5; other multi/absent-target wording, resize/inverse transforms, and counting route remain unresolved | Final conversion profiles and official aggregation outside the confirmed case | Model/evaluation |
| Runtime and submission | Organizers described one autoregressive VLM with no loop/tools and simple Hugging Face execution, but exact loader commands, dependencies, hardware, memory/time/token/resolution/thinking limits, and final model/component requirements remain unissued | Eligible inference configuration and final release checks | Model/evaluation |
| Source policy | Contributing-source training splits are permitted; no organizer overlap-check/exclusion procedure exists and dataset-list disclosure is required. Record-level overlap auditing is a local scientific/provenance control. Source-specific rights and trained-weight release compatibility remain unresolved. Exact BUS-UCLM and PathMNIST/NCT-CRC questions were sent on October 23 and remain pending; see the [outreach record](SOURCE_CLARIFICATION_OUTREACH.md). | Real-source model use and expansion | Data/provenance |
| Source/record review | Rights basis, grouping, visual support, geometry, display policy, overlays, and named review decisions. Two qualified breast-imaging leads and the BUS-BRA corresponding author were contacted on October 23; no agreement or decision exists yet. | Training/dev/confirmation admission | Data/provenance plus suitable biomedical reviewer |
| UTC MOCS access | The [dated access audit](MOCS_ACCESS_AUDIT.md) preserves the October 18 route failure, but October 23 scheduler receipts establish bounded Slurm execution on MOCS A100s. B1 and B2-P measured runtime/CUDA memory, completed one synthetic optimizer step, exported, and reloaded offline; the separate answer/context job completed one singleton-accumulation step without a new export/reload claim. VPN/Duo/SSH path, durable account entitlement and quota, future queue availability, full-training throughput, multi-seed cost, heterogeneous-batch equivalence, and official-runtime equivalence remain unknown | Full biomedical training feasibility, measured multi-run cost, and official-runtime equivalence | Model/evaluation plus HPC support |
| Budget and people | Spending ceiling, weekly hours, storage, reviewer availability, and resource owner | Committing long or paid runs | Team coordination |
| Model experiments | Untouched predictions, matched adaptation, module support, repeated results, actual cost | Final base/recipe/checkpoint choice | Model/evaluation |
| Final confirmation | Eligible untouched cohort, frozen primary/seed/thresholds, retained anchors | Independent final comparison claim | Review/release |

The [organizer question draft](../../outputs/mmbu-precompute/docs/organizer-questions.md) is historical; use the dated reply registers above for current state. The [Einstein handoff](../../outputs/mmbu-precompute/docs/einstein-handoff.md) refers to obsolete infrastructure and contains no MOCS GPU diagnostic; use the current native traces instead. A local preflight exit of zero means a report was written, not that remote training is viable.

Historical v0.1–v0.3 reports preserve an earlier Qwen baseline/challenger/fallback order as part of the recorded handoff. That order is superseded for new competition decisions; do not treat those immutable reports or the model registry's historical role labels as current selection authority.

## Record a resolution

For each decision, record date, named owner/reviewer, exact question, authoritative evidence and revision, selected policy, affected files/experiments, and what remains uncertain. Retain the old record and mark the new one as superseding it. Update the relevant executable registry only when its declared purpose and evidence are justified. A deadline or successful parser run cannot supply missing authority.

Use the [data checklist](../../outputs/mmbu-precompute/docs/data-review-checklist.md) for source decisions. Suitable human biomedical review must be identified explicitly; historical AI-agent reviews do not fill that role. Keep organizer clarification, source-use review, and medical-label review distinct even when one person coordinates them.

## Calendar and stop conditions

The historical strategy's AoE deadline assumption is superseded by the October 14 organizer email naming Pacific
Standard Time and the October 3 pinned Discord answer naming December 31 at 23:30. Retain the earlier internal freeze,
then verify the exact displayed timestamp when the final form arrives.

If access is still unresolved on October 9, the plan calls for local data/contract work and a reduced experiment queue. The seven-day sprint begins when access and compute are ready; it is a work-order target, not a runtime promise. Maintain the planned 15% compute reserve and base later commitments on measured per-run costs. Do not erase data review, untouched baselines, or export testing to recover a missed calendar milestone.
