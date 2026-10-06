# Decisions and unresolved gates

This is the team's human-readable register at handoff. The source records are the [protocol register](../../outputs/mmbu-precompute/configs/protocol-register.json), [source registry](../../outputs/mmbu-precompute/configs/source-registry.json), [model registry](../../outputs/mmbu-precompute/configs/model-registry.json), and [resource record](../../outputs/mmbu-precompute/configs/resources.json). All scientific owner roles below remain **unassigned** until the team records an assignment.

## Working decisions already supported

| Decision | Basis and limit |
| --- | --- |
| Begin with Qwen2.5-VL-7B-Instruct; compare Qwen3.5-9B; keep Qwen3-VL-8B-Instruct as fallback | Tested CPU processor compatibility and provisional execution order; no performance ranking |
| Keep real sources and records pending | Rights, overlap, intended-use/release compatibility, and biomedical conversion review are incomplete |
| Preserve separate task/context/judge input builders and provisional output profiles | The published brief and public card conflict; neither silently overrides the other |
| Require explicit uint16 presentation and verified native assistant boundaries | Tested intensity-loss/scaling and Qwen3.5 thinking-prefix counterexamples |
| Use token-weighted shifted assistant loss and test actual trainer integration | Synthetic unequal-microbatch probe; trainer behavior remains unverified |
| Retain negative results and use one untouched confirmation after selection | Prospective research design and checked local receipt lifecycle |

## External evidence still needed

| ID / decision | Missing fact or deliverable | Blocks | Suggested workstream |
| --- | --- | --- | --- |
| PROTO-01: task rationale | Organizer-selected rationale-in-JSON versus rationale-before-JSON schema and harness | Frozen production serializer and schema-specific training | Model/evaluation |
| PROTO-02: malformed output | Zero grade versus raw-response fallback, with fixtures | Official-equivalent scoring and format-dependent elimination | Model/evaluation |
| PROTO-03: segmentation labels | Multi-label policy reconciled with the shown one-concept judge | Multi-label grading and score-based promotion | Model/evaluation |
| PROTO-04: context pass | Prompts, requested-field masks, unknown convention, missing/zero-field rules, implementation | Official C and S claims | Model/evaluation |
| PROTO-05: public development | Explicit allowed local evaluation/selection operations and authorized gated access | Official-dev purpose; challenge records remain outside training | Review/release |
| PROTO-06: detection/routing | Pixel xywh conventions, resize/inverse transforms, multi/absent-target matching, counting route | Final conversion profiles and official aggregation | Model/evaluation |
| Runtime and submission | Pinned harness/dependencies; memory/time/token/resolution/thinking limits; final model/component requirements | Eligible inference configuration and final release checks | Model/evaluation |
| Source policy | Permitted use of contributing-source training data, declared overlap, and weight-release compatibility | Real-source model use and expansion | Data/provenance |
| Source/record review | Rights basis, grouping, visual support, geometry, display policy, overlays, and named review decisions | Training/dev/confirmation admission | Data/provenance plus suitable biomedical reviewer |
| Einstein access | Actual allocated GPU/count/VRAM, runtime behavior, quota, scheduler limits, availability | Model viability, measured pilot cost, load/forward/export | Model/evaluation plus IT |
| Budget and people | Spending ceiling, weekly hours, storage, reviewer availability, and resource owner | Committing long or paid runs | Team coordination |
| Model experiments | Untouched predictions, matched adaptation, module support, repeated results, actual cost | Final base/recipe/checkpoint choice | Model/evaluation |
| Final confirmation | Eligible untouched cohort, frozen primary/seed/thresholds, retained anchors | Independent final comparison claim | Review/release |

The [organizer question draft](../../outputs/mmbu-precompute/docs/organizer-questions.md) is ready and has not been sent. The [Einstein handoff](../../outputs/mmbu-precompute/docs/einstein-handoff.md) is ready; no remote GPU diagnostic is recorded. A local preflight exit of zero means a report was written, not that remote training is viable.

## Record a resolution

For each decision, record date, named owner/reviewer, exact question, authoritative evidence and revision, selected policy, affected files/experiments, and what remains uncertain. Retain the old record and mark the new one as superseding it. Update the relevant executable registry only when its declared purpose and evidence are justified. A deadline or successful parser run cannot supply missing authority.

Use the [data checklist](../../outputs/mmbu-precompute/docs/data-review-checklist.md) for source decisions. Suitable human biomedical review must be identified explicitly; historical AI-agent reviews do not fill that role. Keep organizer clarification, source-use review, and medical-label review distinct even when one person coordinates them.

## Calendar and stop conditions

The historical strategy records a December 31, 2026 end-of-day AoE deadline, ending January 1, 2027 at 06:00 Chicago. It proposes an internal December 28, 17:00 Chicago target and a deliverable ready December 20. These are the saved planning assumptions; confirm organizer changes before final scheduling.

If access is still unresolved on October 9, the plan calls for local data/contract work and a reduced experiment queue. The seven-day sprint begins when access and compute are ready; it is a work-order target, not a runtime promise. Maintain the planned 15% compute reserve and base later commitments on measured per-run costs. Do not erase data review, untouched baselines, or export testing to recover a missed calendar milestone.
