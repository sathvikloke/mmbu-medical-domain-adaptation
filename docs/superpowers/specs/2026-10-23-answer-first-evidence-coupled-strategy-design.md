# Answer-first, evidence-coupled Track 2 strategy

**Date:** October 23, 2026  
**Evidence class:** official scoring contract, primary-literature review, repository audit, and three independent AI-agent adversarial review passes; no qualified-human review or biomedical model result  
**Status:** non-executable strategy proposal; the currently acknowledged handoff packet remains authoritative until a separately reviewed successor is resealed and independently acknowledged  
**Proposed decision:** retain the existing B0/B1-L/B2-P family, but replace a presumptive dual-objective flagship with a task-first selection ladder; admit context co-training and evidence-coupling only when matched external evidence earns them

## Executive decision

The project should not pivot to a new architecture before obtaining biomedical evidence. The current shared-PEFT family is well aligned with the challenge and already has bounded native feasibility evidence. Its weakness is not implementation quality. Its weakness is that the dual-objective member was described as the flagship before any real comparison showed that context supervision helps rather than harms the much more valuable task endpoint. This proposal does not alter the current sealed dependency manifest or authorize an experiment.

The competition lane is therefore:

1. establish the untouched base (`B0`);
2. freeze language-only and projector-plus-language task-only candidates (`B1-L task`, `B2-P task`);
3. freeze each task-only candidate's matched answer-plus-context counterpart after the context contract is sufficiently bound;
4. promote context co-training only when it improves the frozen score proxy while remaining task-noninferior and passing regression, visual-use, serialization, cost, and held-out-source gates; and
5. permit one evidence-coupling challenger only after the baseline reveals the specific localization or visual-reliance residual it is designed to repair.

“Task first” describes promotion priority and causal interpretation, not sequential result opening. All five profiles,
comparators, and decision rules must be committed before any decision-bearing output is opened. This is a selection
system, not a new learning algorithm. The entrant is the simplest surviving member, whether that is task-only or
dual-objective.

## Why task comes first

Track 2 uses

```text
S = (0.8T + 0.2C)(T - B)
```

for adapted task performance `T`, context performance `C`, and frozen base task performance `B`. For positive task gain,

```text
dS/dT = 1.6T - 0.8B + 0.2C
dS/dC = 0.2(T - B)
```

Task performance affects both factors; context changes only the first. Near a modest positive adaptation gain, the local value of a task point can be tens of times larger than the value of a context point. Context supervision therefore cannot be promoted because it is intuitively useful or because it raises `C`; it must preserve `T` within a prospectively frozen noninferiority margin and improve the uncertainty-aware score contrast.

The exact margin, resampling hierarchy, simultaneous-error rule, seeds, and missing-stratum behavior remain unknown until the scientific freeze. This document does not choose them.

## Human story

The judge-facing sentence is:

> A biomedical image model should give the right answer, point to the right evidence when the task asks for it, and avoid inventing unsupported image context—without breaking answers the base model already got right.

This is relatable and accurate. It does not claim diagnosis, patient benefit, clinician time savings, clinical-grade localization, or safe deployment. The near-term human value is a more auditable biomedical perception model and development process.

The four visible behaviors are:

- **right answer:** source-held-out classification, grounded classification, localization, and counting where the admitted source supports them;
- **right evidence:** authoritative full-image and region/coordinate views agree on the source concept, and answer-changing visual pairs change the prediction in the registered direction;
- **no invented context:** only source-authoritative requested fields receive training or credit, with unsupported fields measured separately rather than guessed; and
- **do not break prior competence:** positive and negative flips are reported separately, with base-conditional preservation eligible only after a real negative-flip residual appears.

## Frozen competition ladder

The minimum family remains five arms. The four adapted arms use identical admitted units and matched optimizer family,
supervised-token budget, updates, active-compute envelope, seeds, and troubleshooting allowance. All five arms use
identical evaluation units, prompts, serializers, runtime conditions, endpoints, and evaluation roles:

| Arm | Trainable scope | Objective | Decision role |
| --- | --- | --- | --- |
| `B0` | none | none | frozen base reference |
| `B1-L task` | language LoRA | answer task only | simplest adapted candidate |
| `B1-L dual` | language LoRA | answer plus authoritative context | matched context increment at B1-L |
| `B2-P task` | native projector merger plus late-language LoRA | answer task only | visual-adaptation candidate |
| `B2-P dual` | same as `B2-P task` | answer plus authoritative context | matched context increment at B2-P |

The first decision-bearing comparison remains exactly the five enabled arms already supported by the candidate-manifest contract. Adapted arms receive matched training budgets; `B0` is not trained. All five arms receive identical evaluation conditions, and task-only arms are evaluated on the same task and context endpoints as dual arms. The same troubleshooting and opening budget applies to every trained arm. A context arm cannot rescue nonpositive task gain, a task regression beyond the frozen margin, or a failed visual-use gate.

The 75/25 answer/context share demonstrated mechanical execution in a synthetic native preflight only. It has no
scientific priority. A successor may include it only with a prospective loss-scale rationale and matched alternatives
declared before outputs; no allocation may be tuned on the MMBU public set.

## Conditional evidence-coupling challenger

The only preferred post-baseline mechanism is a training-only answer–localization consistency condition on admitted units that contain an authoritative class and authoritative region geometry.

For the same independent unit, construct matched supervised views:

1. full-image classification;
2. region-grounded classification using the frozen class-agnostic compositor; and
3. original-image coordinate localization.

The optional consistency term requires full-image and grounded answers to normalize to the same source ontology identifier. Independently authoritative answer-changing image pairs must track their respective targets. The official inference interface and artifact remain unchanged.

This arm is eligible for a **future successor specification only** if a frozen task-only or dual baseline shows a repeated held-out-source localization or visual-reliance residual. This document does not define or authorize its differentiable loss, weight, unit-mass accounting, token displacement, or execution. A successor would have to match the surviving baseline for units, tokens, updates, trainable parameters, active FLOPs, compute, and troubleshooting, and kill the condition if gains reduce to overlay or source cues, fail to improve both semantic and localization endpoints, or materially regress ordinary task score.

This mechanism has close antecedents in medical grounding, multitask consistency, and counterfactual visual-reliance training. It is a high-fit empirical challenger, not a high-novelty learner claim.

## Research claim boundary

The project may eventually support one of two empirical findings:

1. authoritative context or evidence supervision improves hidden-source biomedical perception without sacrificing the task endpoint; or
2. it does not, and task-first adaptation is the more reliable competition policy under heterogeneous medical supervision.

Either result is useful if prospectively frozen and replicated. Neither is a new optimizer or new adapter family. The answer/context-by-unit-normalization factorial remains a side study after the competition survivor exists; it cannot consume the first decision-bearing biomedical budget or delay the entrant.

Current honest ratings, before biomedical execution:

| Dimension | Score / 100 | Reason |
| --- | ---: | --- |
| Official benchmark alignment | 94 | Directly covers the scored task/context interfaces and base-relative comparison |
| Competition-recipe plausibility | 84 | Native path and controls are strong; data, contract, and performance evidence are missing |
| Human intelligibility | 82 | “Right answer, right evidence, no unsupported context, fewer regressions” is clear |
| Human/biomedical impact evidence | 55 | Biomedical relevance is real, but no workflow or clinical outcome is demonstrated |
| System novelty | 35 | The residual contribution is an empirical selection/interaction finding |
| Learner-method novelty | 20 | PEFT, multitask grounding, consistency, preservation, and routing are established |
| Empirical readiness | 36 | Native synthetic feasibility exists; admitted biomedical results do not |
| Evidence-weighted win readiness | 55 | The largest missing evidence is admitted data plus matched runs, not another idea |

Scores cannot rise through prose. A 90-plus competition assessment requires a valid admitted multi-family comparison, a surviving task/context candidate, source-held-out stability, measured cost, and official package rehearsal. A 90-plus learner-novelty score is not a realistic or necessary target for this challenge.

## Smallest next evidence packet

Before any **decision-bearing biomedical model run**, the packet must bind:

- BUS-BRA plus at least two independently admitted semantic-breadth source families for decision-bearing comparisons;
- exact candidate digests and trainable module maps;
- exact task-only and dual exposure allocations;
- task noninferiority, score-improvement, regression, visual-use, malformed-output, and cost rules;
- source-held-out roles, seeds, group-resampling hierarchy, and one-opening confirmation policy;
- exact compute caps and output location; and
- the current organizer prompt/schema authority, with unknown context behavior remaining blocking rather than guessed.

The first decision-bearing run should execute the exact frozen five-arm comparison on the smallest external-only
population and budget that satisfy its prospective power, support, and decision rules. It is not an informal pilot and
cannot silently eliminate an arm or reuse its population for confirmation. If a run cannot change a declared decision,
it should not consume protected GPU or data evidence.

A separately authorized BUS-BRA-only engineering run may still test loading, target construction, gradients, loss,
throughput, memory, serialization, and failure handling. It cannot select, kill, or promote a scientific arm.

## Stop rules

- Do not start another broad novelty search before a frozen biomedical residual exists.
- Do not call context, localization, or explanation clinically useful without a qualified workflow study.
- Do not promote a context arm that trades away task performance merely because `C` improves.
- Do not add routing, mixtures, a specialist encoder, preservation, or interpolation until the simpler ladder exposes the failure each is meant to repair.
- Do not use MMBU public examples, outputs, labels, annotations, embeddings, or statistics to choose any arm.
- Do not let the side research factorial delay the simplest competition survivor.

## External boundaries reviewed

- [Official challenge brief](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf)
- [Official rules](https://akiranishii.github.io/mmbu-challenge/documents/mmbu-challenge-official-rules.pdf)
- [MMBU paper](https://arxiv.org/abs/2606.06696)
- [Sparse Spectral LoRA / MedQwen](https://arxiv.org/abs/2604.01310)
- [MIMO](https://openaccess.thecvf.com/content/CVPR2025/html/Chen_MIMO_A_Medical_Vision_Language_Model_with_Visual_Referring_Multimodal_CVPR_2025_paper.html)
- [VividMed](https://aclanthology.org/2025.naacl-long.89/)
- [MedRegA](https://proceedings.iclr.cc/paper_files/paper/2025/hash/414fd191b3246a19a55741b938380136-Abstract-Conference.html)
- [CORAL](https://arxiv.org/abs/2607.03647)
- [Medical VLM grounding and adaptation audit](https://arxiv.org/abs/2604.27720)

