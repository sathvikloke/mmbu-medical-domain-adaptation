# MMBU project dossier

**Updated:** October 23, 2026  
**Audience:** teammate, reviewer, mentor, or judge who needs the project in five minutes  
**Current status:** strong audited scaffold and native feasibility evidence; no biomedical performance result yet

## The project in one sentence

Adapt a general-purpose vision-language model for a biomedical-image benchmark so it answers image questions and
reports requested image metadata more reliably, while testing whether it actually uses the image and preventing the
adaptation from damaging capabilities the base model already had.

## Why a person should care

Medical-image AI can look competent while failing in ways that matter to people: it may recognize a concept only when
choices are supplied, ignore the image and rely on wording, lose localization after answer-only tuning, or improve one
task while silently regressing another. A useful system should not merely produce more fluent answers. It should retain
visual dependence, handle the same medical fact across whole-image, region-grounded, localization, and context
questions, and expose negative trade-offs instead of hiding them in one aggregate score.

The near-term impact is a more auditable development and evaluation process for a candidate research model on
heterogeneous medical images—not a diagnostic product or a claim of clinical safety. Clinical use would require
separate prospective validation, regulatory review, workflow testing, and qualified human oversight that this
competition project does not provide.

## What the competition asks, in plain language

MMBU shows a model a biomedical image and a question, then scores the answer; some routes ask about the whole image,
some identify a region or coordinates, and some request context fields associated with the image. “Answer” could mean
the abnormality requested by the question, while “context” could mean source-authoritative metadata such as modality
or body part; the final organizer-controlled context prompt and scoring details are not fully known. A useful entrant
must improve the answers and preserve the requested context behavior: polished formatting or metadata alone cannot
compensate for worse task performance.

## The actual competition idea

The flagship is **B2 dual-objective answer-and-context adaptation** using parameter-efficient fine-tuning (PEFT): a
small learned adapter changes the model without replacing its base architecture.

1. train the answer behavior needed for classification, grounded classification, localization, and related task
   outputs;
2. train only source-authoritative requested context fields, masking unknown fields rather than inventing them;
3. normalize loss mass by the underlying patient, slide, study, or other independent unit so sources with more derived
   views do not receive accidental extra influence;
4. compare five matched arms under the same records, updates, tokens, compute, serializer, and evaluator: the
   untouched base (`B0`), plus progressively broader adapter architectures (`B1-L` and `B2-P`) each trained once with
   task-only targets and once with answer-plus-context targets; then compare the strongest survivor with matched
   external systems; and
5. promote only a model that improves task and context endpoints while passing image-use, negative-flip,
   preservation, invalid-output, runtime, and fresh-offline-load gates.

This is deliberately a simple entrant. The challenge score rewards performance, not architectural complexity. If the
simpler answer-only model wins the frozen comparison, that is the model to submit.

## What is potentially interesting—and what is not novel

Shared LoRA, multitask supervision, medical grounding, context prediction, per-origin view weighting, preservation,
and low-budget base selection all have prior art. The project must not market their combination as a new learner.

The only surviving system-level research hypothesis is narrower: **does answer/context co-training interact with
independent-unit mass normalization, beyond the effect of either component alone?** The prospective `SYS-A0`–`SYS-A3`
factorial tests that interaction. An exposure-equalized repeat should collapse the normalization effect, and a
duplicate-view perturbation should leave the unit-normalized estimate invariant. A separate hypothesis asks whether
base selection by adaptation response beats selection by untouched-base strength on a second unopened cohort.

These are conditional empirical claims, not achieved novelty. Direct medical multitask systems and general transfer
selection methods make the current honest ratings low: system novelty **3.5/10**, learner-method novelty **2.0/10**,
and pre-result paper novelty **3.0/10**. No amount of extra prose can raise them. A prospectively frozen, matched,
replicated interaction result could create a defensible system contribution; a failed result should retire that claim
without preventing the strongest competition recipe from being used.

## Why this is still a credible win strategy

| Strength | Why it matters |
| --- | --- |
| Direct score alignment | The training and evaluation plan treats answer performance and requested context as separate endpoints instead of assuming one will improve the other. |
| Architecture preservation | The primary path exports ordinary adapter/projector artifacts rather than requiring an exotic inference service. |
| Visual-use controls | Image swaps, no-image cases, answer-changing images, positive/negative flips, and localization checks are designed to detect text-only or format-only gains. |
| Leakage resistance | MMBU public examples and derivatives are barred from training and recipe selection; source-held-out external evidence drives decisions. |
| Honest simplicity | B0/B1/B2 and matched controls can identify whether added complexity earns its cost. |
| Reproducibility | Exact model/runtime pins, synthetic native preflights, offline reloads, immutable evidence, and fail-closed validators reduce avoidable execution failures. |

These properties improve the chance of a valid, explainable submission. They do not establish a probability of winning.

## What is already demonstrated

- The pinned Qwen2.5-VL 7B path loaded on a MOCS A100, used its visual path, performed finite forward/backward and one
  bounded optimizer step, exported the declared adapter scope, and reloaded offline; see the
  [B1 native trace](B1_NATIVE_PREFLIGHT_TRACE.md).
- The B2 projector-plus-language-adapter path and the answer/context unit-mass objective reached their declared
  trainable tensors under bounded synthetic native preflights; see the
  [B2 projector trace](B2_PROJECTOR_PREFLIGHT_TRACE.md) and
  [B2 dual-objective trace](B2_DUAL_OBJECTIVE_PREFLIGHT_TRACE.md).
- The repository has cross-version CI, optional-image coverage, tamper-evident evidence checks, strict public-data
  firewalls, and fail-closed experiment/release states.
- BUS-BRA has complete structural and duplicate-risk evidence, and a 244-record packet has been prepared for
  qualified-human review; no human review or source admission has been completed. The
  [review packet and validator](BUSBRA_HUMAN_REVIEW_PACKET.md) can bind future completed forms to decoded image
  dimensions, pixel-derived mask boxes, reviewer chronology, provenance, rights, and exact evidence bytes without
  granting source or model-use authority.

These are engineering and governance results. They are not evidence that adaptation improves medical performance.

## What remains unproved

- No biomedical source has completed medical, provenance, rights, purpose, and release admission.
- No valid biomedical B0/B1/B2 comparison, multi-seed result, or challenge-performance estimate exists.
- The final organizer context prompt, evaluator behavior, loader layout, runtime limits, and exact cutoff time remain
  incompletely bound.
- Heterogeneous concatenated-batch equivalence failed; the safe singleton-accumulation path is the only admitted native
  objective route today.
- No human peer review, clinical adjudication, official loader rehearsal, upload, or submission has occurred.

## Shortest honest path forward

| Order | Gate | Exit condition |
| ---: | --- | --- |
| 1 | Admit one source for engineering | A qualified, receipt-bound source enables a non-promotable real-path pilot of loading, target construction, gradients, loss, throughput, memory, serialization, and failure discovery. It cannot select or kill a scientific arm. |
| 2 | Admit the decision portfolio | Before any B1-L/B2-P selection, kill, or effect-floor decision, admit BUS-BRA plus at least two independent semantic-breadth families with prospective development and held-out-family roles. BBBC039 is capped wiring smoke only; BBBC038 is post-selection stress and neither can satisfy this minimum. |
| 3 | Freeze the scientific comparison | Exact B0/B1/B2 profiles, seeds, exposure, endpoints, margins, resampling, multiplicity, missing-data behavior, compute caps, and decision code predate decision-bearing outputs. |
| 4 | Run the matched biomedical comparison | B0/B1/B2 execute on the frozen multi-family roles; same-source and held-out-family results, visual dependence, task/context behavior, cost, and regressions stay separate. |
| 5 | Confirm only a survivor | A surviving comparison receives frozen independent seeds and one untouched confirmation role; failed hypotheses stop, and post-B2 ablations cannot delay the entrant. |
| 6 | Rehearse the official package | Fresh loader, runtime, artifact, disclosure, and rollback checks pass before any human-approved upload. |

## Decision rule for the team

Optimize for the strongest honest submission, not the fanciest acronym. Keep B2 as the primary lane until evidence
beats it. Do not claim novelty from infrastructure, compliance, or combining established parts. Do not change methods
because of MMBU public examples. When an experiment fails, preserve the failure, update the hypothesis, and spend the
next unit of compute only where a frozen comparison can change a decision.

## Source of truth

This dossier is an entry point, not a replacement for binding contracts. Use the
[project scorecard](PROJECT_SCORECARD.md) for evidence-separated ratings, the
[public model repository audit](PUBLIC_MODEL_REPOSITORY_AUDIT.md) for one reporting-only field observation and its zero-authority firewall disposition, the
[competition-first recipe](COMPETITION_FIRST_RECIPE.md) for the entrant, the
[system-interaction hypothesis](SYSTEM_INTERACTION_HYPOTHESIS.md) for the conditional research claim, the
[research portfolio](RESEARCH_PORTFOLIO.md) for lane priorities, and the
[decision register](DECISIONS.md) for unresolved external gates.
