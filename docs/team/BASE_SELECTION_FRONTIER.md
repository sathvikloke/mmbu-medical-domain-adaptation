# Base-selection adaptation frontier

**Date:** October 17, 2026  
**Status:** prospective design; no candidate is selected and no model result exists  
**Purpose:** choose a Track 2 base without using MMBU public examples or confusing base strength with adaptability

The binding adverse corrections are recorded in
[BASE_SELECTION_REDTEAM.md](BASE_SELECTION_REDTEAM.md).

## Defect being repaired

The official prospective score is

`S = (0.8T + 0.2C)(T - B)`

where `B` is the frozen base model's task performance and `T,C` are the adapted model's task and context performance.
Ranking untouched bases by `B` cannot identify the best entrant. A stronger base may leave less measured improvement;
a weaker base may have more headroom but a worse adapted ceiling. For fixed adapted `T,C`, the derivatives are:

- `∂S/∂B = -(0.8T + 0.2C)`;
- `∂S/∂C = 0.2(T - B)`; and
- `∂S/∂T = (0.8T + 0.2C) + 0.8(T - B)`.

This makes task adaptation and base-relative gain central. It does **not** authorize deliberately crippling a base,
selecting from public MMBU results, or claiming an external proxy equals the hidden objective.

## Eligible candidate universe

Freeze every base identity before comparative outputs exist. Each candidate must be an unchanged, publicly released,
eligible checkpoint with immutable model/processor revisions, license, architecture, total/active parameter count,
native precision, and disclosure. Quantizing, pruning, disabling modules, changing prompts, or otherwise degrading a
base to enlarge `T-B` creates a different base identity and is ineligible for the primary screen.

The pinned `model_slot::B1` runtime fixture is not automatically a competition candidate. Candidate admission requires the challenge
size/release route, local loader/package feasibility, license, and a prospective resource cap. A configuration failure
does not prove a model scientifically inferior; preserve it as mechanical failure evidence.

Before F0, the frontier manifest binds the complete candidate/revision list, per-architecture module-map digests,
trainable-parameter ratio band, hard memory/time limits, equal setup-attempt/hour allowance, seed policy,
`max_candidates`, `max_total_gpu_hours`, and `max_failed_jobs`. Missing literals return `frontier_not_frozen`; they are
not chosen by the implementer. The binding readiness rules are in the
[experiment-freeze contract](EXPERIMENT_FREEZE_CONTRACT.md).

## Three-stage screen

Before F0, freeze disjoint independent-group/source roles: `frontier_train` for screen fitting,
`frontier_tuning` for checkpoint/early-stop decisions, and untouched `frontier_decision` for the one-time base choice.
No patient/study/slide/parent/duplicate group may cross roles. Base and adapted outputs on `frontier_decision` remain
masked until every candidate's F2 checkpoint, seed, artifact digest, and failure status is committed.

### F0: mechanical viability, no biomedical selection

For every frozen candidate, use the same synthetic shape and serializer fixtures to prove native load, image forward,
bounded generation, non-quantized BF16/FP16 export, fresh offline reload, exact saved-key closure, and measured peak
memory/time. F0 may eliminate only a prospectively defined hard incompatibility or resource-limit failure.

### Joint decision base arm: untouched base characterization

Only after every F2 artifact, seed, and failure status is committed, run every untouched base on the untouched
`frontier_decision` population with the same semantic task/context prompt bytes transformed by each pinned native chat
template, image
presentation, generation budget, parser, and grader. Seal the raw outputs and record `B_proxy`, context, output validity,
visual-dependence panel, cost, and source/task slices only in the one-time joint decision receipt after all F2 candidate
artifacts are frozen. Effective prompt/token IDs and the frozen reasoning/thinking policy are receipted. A candidate
that cannot express the common condition is ineligible; native defaults are descriptive only. The base arm is
descriptive and cannot select a base by itself or change F2 training.

### F2: standardized micro-adaptation response

Train exactly one prospectively frozen shared-PEFT screen per base on the same admitted `frontier_train` units, using
only `frontier_tuning` for early stopping and checkpoint choice.
The screen is deliberately ordinary: projector plus late-language LoRA where natively available, no MOSAIC, QUILT,
B4, candidate-specific data, public examples, or candidate-specific hyperparameter search. Before any output exists,
bind:

- the architecture-specific module map and proof that it implements the same functional profile;
- exposure-matched optimizer updates, independent-unit/view IDs, and target UTF-8 bytes; model-specific supervised
  token counts are reported covariates rather than an equality constraint across tokenizers;
- trainable-parameter ratio and absolute count;
- one compute-matched sensitivity cap using measured active FLOPs/wall time;
- identical task/source weights, prompt families, losses, rationale policy, seeds, and checkpoint rule; and
- a failure policy for a model that cannot express the shared profile.

After every checkpoint/artifact digest is committed, evaluate each adapted screen on the same untouched
`frontier_decision` units as the joint decision base arm and open base/adapted outputs together once. Compute a clearly named external proxy
`S_proxy = (0.8T_proxy + 0.2C_proxy)(T_proxy - B_proxy)`. If the final context protocol is unavailable, do not silently
substitute guessed official fields. Constrain `T_proxy,B_proxy,C_proxy` to `[0,1]`; a nonpositive or sub-margin task gain
is ineligible before ranking. For eligible positive task gain, report the partial-identification interval from
`0.8T_proxy(T_proxy-B_proxy)` at `C=0` through `(0.8T_proxy+0.2)(T_proxy-B_proxy)` at `C=1`, plus any separately named
non-binding context proxy. A base decision is provisional unless the frozen robust-dominance/sensitivity rule survives
that context range.

## Selection rule

Use shared independent-group/source bootstrap draws across every base/adapted pair. A base is eligible only if it:

1. passes F0 and the challenge release/size route;
2. improves task performance by the frozen practical margin under the standardized screen;
3. has no blocking output-validity, source/task, visual-dependence, context-proxy, or preservation regression;
4. meets both exposure and measured-resource caps; and
5. fresh-loads the standardized adapter twice without network access.

Among eligible bases, select the one with the highest simultaneous lower bound on the preregistered primary contrast
only when the context-uncertainty rule also permits selection.
If bounds overlap inside the practical-equivalence region, choose deterministically by: simpler loader/package path,
lower measured resource use, then stronger worst-source/task performance. Do not choose by point estimate, public MMBU
behavior, name recognition, or the candidate receiving more troubleshooting/tuning.

The chosen base then enters the B0/B1-L/B2-P/B2-F recipe. `frontier_decision` cannot be reused for recipe tuning or the
final untouched `recipe_confirmation` population. Candidate-specific recipe tuning after base selection uses its
separately declared development role. A post-opening change retires `frontier_decision` into development and requires a
new independent decision population.

## Mandatory negative controls and reports

- Report raw `B_proxy`, adapted `T_proxy,C_proxy`, gain, score proxy, and resource exposure separately; a high proxy
  cannot hide a poor adapted model.
- Recompute under frozen natural-mixture and macro-source/task weights; a rank reversal makes selection unresolved.
- Report whether the winner changes between exposure-matched and compute-matched views.
- Preserve all failed loads, malformed outputs, and negative flips.
- Prefer the same frozen seed set for every base. If the resource plan instead uses one common screening seed and one
  independent selected-base confirmation seed, freeze that two-stage rule in advance; a failed confirmation yields no
  selection and cannot promote the runner-up on the reused cohort.
- State that the screen selects an external-development hypothesis, not a hidden-set winner.

The estimand is **response to the frozen screen**, not intrinsic model adaptability. Candidate-specific tuning could
change the order and is outside this decision claim.

## Builder self-check

The design is implementable only after the candidate universe, exact global/stage compute and failure caps, admitted data, native module trees, MOCS measurements,
and task/context proxy are available. No field may be inferred from a model family name. The most likely implementation
mistakes are silently unequal target-token exposure, architecture-specific module cherry-picking, reusing the same
population for base and final candidate confirmation, and treating missing context authority as permission to invent a
schema. Each is an automatic rejection condition.

## Honest effect on current score

This closes a planning defect but adds no model evidence. Competition strategy remains **8.8/10** until a literal
frontier packet exists; its no-new-evidence ceiling is **8.9/10**. Native F0/joint-decision/F2 receipts are a new
evidence class. Empirical evidence remains **0.5/10**.
