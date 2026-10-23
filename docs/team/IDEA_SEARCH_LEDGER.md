# Research idea search ledger

**Updated:** October 18, 2026  
**Purpose:** prevent renamed rediscovery, novelty inflation, and repeated work

## Decision rule

A new **learner mechanism** enters the implementation portfolio only if it has a challenge-relevant causal hypothesis,
a differentiating update rule or architecture absent from the closest prior work, loader/compute feasibility, matched
controls that can kill its interpretation, and a safe evidence path that does not touch MMBU public data. An attractive
acronym is irrelevant.

Competition-system, data-objective, and evaluation contributions are separate search classes. They may remain in
low-cost design and prior-art audit without a new learner mechanism, but they cannot alter frozen Lane 1, consume GPU
time, or borrow a method-novelty claim. Their admission test is a distinct benchmark-relevant claim, closest-complete-
system separation, and a matched component ablation that rules out more data, more supervision, more updates, more
compute, stricter filtering, or evaluator tailoring.

## Candidate ledger

| Candidate | Initial attraction | Strongest adverse evidence | Decision |
|---|---|---|---|
| Dual-objective answer-and-context shared PEFT | Directly optimize both documented score components while retaining a base-architecture-preserving B2 path, pending loader/package confirmation | Multi-task/context supervision and PEFT are established; direct medical VQA/grounding studies and transfer-selection methods narrow H1/H2 to empirical residuals; no new update rule, literal freeze packet, or local model evidence | **Primary competition lane, not a novel learner.** Prospective competition value 8.4; subjective pre-result competition-system innovation 4.2, system novelty 3.5, method novelty 2.0, and paper novelty 3.0. Unit-normalize exposure and require separate task/context gains plus matched component ablations |
| Canonical label-emission control | Diagnose whether a model recognizes an external source concept but fails to emit an accepted biomedical label; compare raw source labels with a reviewed canonical vocabulary | Answer normalization, fixed-vocabulary VQA, multi-reference generation, VQA soft targets, semantic answer embeddings, and canonical-label SFT are established; one public MMBU participant's local scores are informative but non-official and vocabulary-sensitive | **Add as bounded post-B2 competition ablation, not a replacement learner.** Competition fit 9.0, system novelty 4.0, learner-method novelty 2.0, current evidence 1.5. Keep options out of inference and prohibit public-set-derived vocabulary choices |
| Marked Random-Frequency Set Sketching (MRFSS) | Use random characteristic samples of a complete marked instance measure as a permutation-free training-only target spanning count and spatial layout | CVPR 2022 already uses characteristic-function frequency supervision to capture count, position, and subregion counts; point-query/count-localization/Fourier work further narrows the difference | **Demote; no automatic implementation.** Concept novelty 5.2, paper novelty 4.5, competition fit 6.8; class marks and a VLM head are integration differences |
| Withheld Region-Lattice Valuation Training | Enforce additive/monotone region-set laws while withholding one task vertex to test genuine transfer | Divide and Count already applies inclusion–exclusion to regional counts and enforces aggregation to global count; local-consistency/divide-and-conquer counting, CyCo, MedRegA, Point-Detect-Count, CoHD, and grounding consistency further narrow it | **Demote; do not implement.** Concept novelty 4.8, paper novelty 4.0, competition fit 6.5, feasibility 5.4; withheld/null-law controls improve rigor, not central novelty |
| Latent medical scene-language compiler | Emit a hidden canonical entity/attribute/coordinate/count/context scene and render the requested answer in one pass | Open-vocabulary scene graphs, Scene Language, MedCLM, and region-grounded medical instruction tuning already occupy it; executable compilation risks an extra inference component | **Reject.** Concept/paper novelty 3/3; any benefit must beat equal-token direct multitask JSON supervision |
| Acquisition-provenance factorization | Separate biological content from modality/stain/preparation/magnification provenance and supervise both | BIOMEDICA, UniMed-CLIP, MCPL, MeDSLIP, Anatomy-VLM, and ordinary provenance auxiliary classification occupy the useful mechanism; weak connection to counting/localization | **Reject.** Concept/paper novelty 4/3; insufficient score breadth |
| Redundant semantic codewords | Reconstruct answers from randomly erased class/spatial/count code projections | Error-correcting output codes, GETok, MedRegA, Point-Detect-Count, and unified task tokens occupy it; repair decoding risks postprocessing | **Reject.** Concept/paper novelty 3/2; likely label smoothing/decoder redundancy |
| Direct multiplicative-score training | Train on a minibatch surrogate of `(0.8T + 0.2C)(T - T_base)` | Its gradient is only state-dependent weighted task/context scalarization; it adds no update direction, introduces batch covariance, and gives context the wrong sign while task gain is negative | **Reject.** Concept/paper novelty 2/1; retain the formula only for positive-gain-gated candidate selection |
| Routed semantic LoRA experts / MOSAIC | Factorize modality, specimen/scale, and task-geometry adaptation; test unseen combinations | MedQwen/Sparse Spectral LoRA, BioFact-MoE, LoRA-Mixer, Med-MAT, CrossMed, CCFT, two-stage medical mixture-LoRA, and the October 2026 task-specific medical image-parsing LoRA system directly overlap; the current source-adjusted grid is non-identifiable | **Frozen on the current grid.** Current competition value/concept novelty 4.5/5.5; a genuinely crossed future design must pass G-1 and be rescored before B2/B4/shuffled-routing comparison |
| Plain annotation-view consistency | Same source fact expressed as class, box, mask, count, open, and closed views | CocoCon, SOrT, general cross-task consistency, VividMed/MIMO, and medical multi-consistency rewards already cover the broad claim | **Do not claim as architecture novelty.** Keep as task-aligned curriculum/control |
| Generic PCGrad/CAGrad for medical multi-task PEFT | Resolve conflicts among MMBU-like training tasks | PCGrad and CAGrad are established; application alone is weak novelty | **Baseline only** |
| Same-fact gradient consensus | Keep the update common to multiple task interfaces | PCGrad/CAGrad, augmentation gradient agreement, cross-task consistency, GRAM, iGSP, and gradient-subspace work narrow the claim | **Superseded by QUILT's controlled nuisance-identification design** |
| QUILT interface-gradient quotient | Use strict same-fact prompt panels with identical targets and source-balanced template centroids to identify and remove a shared candidate prompt nuisance; ordinary LoRA at inference | R2F averages same-fact paraphrase LoRA gradients; LoRA-FA fixes `A`; GPM/InfLoRA use SVD-derived orthogonal update constraints; AND-mask/Fish/Fishr target gradient invariance; a 2026 CHIL paper already trains medical-VLM LoRA for paraphrase consistency, while its companion shows consistency can hide loss of image reliance; multiplicative loss scaling can place task gradients in the estimated basis | **Demote to gated diagnostic/negative-result branch.** Honest concept novelty 3.5 and competition idea 4.0; retain the failure tests, but do not build the main submission around it |
| Visual-nullspace LoRA | Constrain an adapter to be zero on question-only activation directions so it acts only on image-conditioned residual directions | GNSP, null-space visual prompt tuning, orthogonal continual-learning PEFT, modality-specific adapters, and Jacobian/KL analyses make null-space preservation crowded | **Do not promote.** Potential QUILT/B2 preservation control only after exact activation geometry and cost are defined |
| Shared medical-fact tangent recovery | Estimate a prompt-invariant update subspace from cross-view gradient covariance instead of subtracting nuisance | Invariant-feature subspace recovery, Domain Gradient Equilibrium, SubGD, and classical multi-view subspace learning already cover invariant/shared gradient or representation recovery | **Reject as successor headline.** It may be a QUILT diagnostic but does not clear the novelty bar |
| Annotation-lattice path consistency | Require class, grounding, localization, and count predictions to agree along every deterministic annotation path | Robust Learning Through Cross-Task Consistency already uses inference-path invariance over a task graph; Point-Detect-Count already studies medical multi-task LoRA | **Keep as a data/evaluation invariant, not method novelty** |
| Image-question interaction-gradient LoRA | Use matched/question-only/wrong-image differences to retain only visually supported adapter updates | CORAL already trains medical VLMs with hard-negative image swaps; DE-CaGI is explicitly causal gradient intervention for evidence-grounded Med-VQA; counterfactual VQA debiasing is broad | **Reject as headline.** Retain image-swap and text-only probes as controls |
| Concept-weighted or mask-aligned medical PEFT | Steer a small adapter toward named medical concepts or source masks while preserving general ability | ConceptVLM already provides concept-aware medical-VLM LoRA; KPL-METER uses knowledge-enhanced multimodal PEFT; MPA-VQA combines mask-prompt contrastive alignment and object grounding | **Reject as headline.** Source-supported concepts and masks remain useful supervision, but do not create a novelty claim by themselves |
| Neyman-orthogonal visual residual tuning | Cross-fit a question-only nuisance model and train the multimodal adapter with an orthogonalized residual score | VQA question-only adversaries and causal debiasing are established; double machine learning protects a low-dimensional causal estimand under explicit assumptions, not an arbitrary high-dimensional generative training loss | **Reject until a valid estimand and orthogonal score are derived.** Do not borrow the DML theorem by analogy |
| Annotation-cycle gradient holonomy | Penalize Lie brackets/order dependence around valid task cycles rather than only first-order conflicts | Lie-bracket geometry of neural training and task-update commutators already exist; Hessian-vector products add material cost; benefit to one-pass competition inference is unproved | **Reject for the competition path.** Interesting theory project, poor current risk/compute ratio |
| Algebraically coherent adapter generators | Learn composable adapters for annotation transformations, enforce path identities, then distill into one base-architecture-preserving LoRA | Adapter composition, cross-task path consistency, dynamic cross-task LoRA, and the Categorical Atlas of PEFT cover most ingredients; exact generator/path claim remains untested and loader compatibility is unconfirmed | **Hold, not promote.** Requires a distinct algebraic prediction and a cheaper proof before displacing QUILT/B2 |
| Fisher-metric QUILT | Whiten prompt-interface gradients with an empirical Fisher/K-FAC metric to reduce coordinate dependence | GRIT already combines K-FAC, Fisher-guided reprojection, and dynamic-rank LoRA; FoRA uses Fisher selection plus Stiefel-constrained LoRA; natural-gradient/Fisher geometry is established and expensive at VLM scale | **Reject as successor headline.** It adds compute and prior-art burden without a unique MMBU prediction; retain only as future geometry research if Euclidean QUILT specifically fails |
| Proof-carrying answer/evidence decoder | Require an answer plus a machine-checkable region or semantic certificate | Grounded reasoning, versatile grounding VLMs, prototype grounding, and consistency rewards are crowded; hidden evaluator may not accept extra output/custom decoding | **Reject for primary competition path** |
| Canonical semantic-atom decoder plus deterministic renderer | Predict one latent fact representation and render every task interface deterministically | Unified structured decoders and task compilers are adjacent; final prompt/parser is unresolved; custom wrapper increases loader risk | **Hold as future architecture study, not current entrant** |
| Test-time consistency/adaptation | Adapt on semantically equivalent prompt variants at inference | WACV 2026 test-time VLM consistency already exists; challenge runtime/stateless rules and repeated passes create risk | **Reject for submission unless organizer explicitly permits and runtime is measured** |
| Base-relative safe residual gate | Fall back to the base when the adapter appears visually unsupported | Mixture/routing, confidence gating, preservation regularization, and causal visual-dependence methods are crowded; calibration can overfit and custom inference risks packaging | **Diagnostic/control, not headline idea** |
| Adaptation-frontier base selection | Compare frozen bases after one matched micro-adaptation screen because Track 2 rewards adapted performance times base-relative gain | Hyperparameter/model selection by learning curves and low-budget proxies is established; one screen measures recipe-specific response, not intrinsic adaptability | **Competition strategy, not method novelty.** Retain the public-firewalled F0/joint-decision/F2 process because base-only ranking is mathematically misaligned with the challenge score |
| Factorial/Möbius update decomposition | Decompose a crossed modality × specimen/scale × task grid into main and interaction effects, predict held-out cells, and compile stable effects into one LoRA | Task Arithmetic already uses three-corner analogies to improve a fourth task; compositional merging, LoRA Soups, task-vector bases, and direct functional non-additivity audits cover the core operation | **Diagnostic only; reject as flagship.** Use the interaction/gauge checks to falsify MOSAIC. Competition idea 5.2, concept novelty 5.8, paper novelty 4.3 |
| Frozen general-plus-biomedical vision encoders | Fuse native general visual tokens with a biomedical specialist inside one legal end-to-end VLM | LEO, MoVE-KD, METEOR, MedPLIB, and Anatomy-VLM cover multi-encoder fusion/distillation and specialist/local medical vision | **Post-B2 competition ablation, not novelty.** Potential upside 7.4; requires duplicate-native control, full active-parameter accounting, loader closure, and measured cost |

## Claim-class index

This index prevents a mechanism-only search from being generalized to the whole project. A row may support more than
one class, but every claim must name its primary class before it is scored.

| Claim class | Current members | Current disposition | Promotion-eligibility evidence; not a decision rule |
|---|---|---|---|
| Learner mechanism | MRFSS, WRLVT, MOSAIC, QUILT, direct-score training, gradient/subspace variants, multi-encoder fusion | **Zero admitted pre-evidence survivors in the scoped searches.** All are rejected, frozen, diagnostic, or post-B2 | Qualifying residual under the scoped rule below; fresh collision search; equal-budget mechanism-specific control |
| Competition system | Dual-objective B2, adaptation-response frontier, exact serialization, and public firewall; optional preservation/interpolation are excluded until separately promoted | **Two separately isolated conditional hypotheses, no admitted contribution.** Subjective pre-result estimates are 4.2 competition-system innovation and 3.5 system novelty, with 0.5 local evidence; see [the system-interaction contract](SYSTEM_INTERACTION_HYPOTHESIS.md) | `SYS-A0`–`SYS-A3` factorial, exposure-equalization null and duplication-invariance checks, strongest matched FLARE-style/mixture-LoRA system, separate frontier isolation against absolute-post-adaptation, delta-only, early-curve, and transferability controls, and independently governed source-parent replication under frozen decision objects |
| Data objective | Unit-normalized annotation views, authoritative context masks, geometry-derived views, answer-changing visual pairs | **Zero standalone survivors.** Useful leakage-safe, provenance-aware supervision construction; concept ceiling 4.0 and standalone paper/objective novelty 3.0 | Unit-normalized versus view-uniform matched test may establish competition value, not retroactive method novelty |
| Evaluation contribution | Same-unit task/context reporting, source-held-out slices, typed visual interventions, negative flips, malformed-output and cost slices | **Zero standalone survivors.** Preregistered source-macro dashboard of established diagnostics; usefulness 8.0, conceptual novelty 3.5, paper novelty 3.0 | Reopen only if one atomic statistic prospectively predicts an untouched clinically adjudicated endpoint beyond component metrics across independently governed medical source parents and replicates externally |

Contracts, manifests, and governance support validity and reproducibility. They do not enter the learner-method class.
No row can promote a score or claim from these qualitative requirements. Before any promotion, a claim-specific
prospective decision object must freeze the primary estimand, independent unit, comparator, minimum worthwhile effect
or noninferiority floor, resampling/uncertainty method, multiplicity rule, exact replication count and independence
definition, missing-data behavior, and conjunctive pass/fail function. It must predate all outputs used by the decision.

## Active hierarchy

1. **Lane 1:** B0/B1/B2 dual-objective answer-and-context adaptation maximizes the chance of a valid strong submission;
   curriculum order is only an ablation.
2. **Lane 3 / diagnostic research:** QUILT is retained for a possible rigorous negative result, not as the primary
   novelty hypothesis.
3. **Lane 2 / secondary novelty:** MOSAIC proceeds only if independent source structure makes its factorization
   identifiable.
4. **B4:** MedQwen/Sparse Spectral LoRA remains a mandatory literature comparator and possible independent reproduction,
   not our novelty.
5. **Factorial-update audit:** a pretraining diagnostic for MOSAIC's additivity assumption, not a submission method;
   see [the adverse review](FACTORIAL_UPDATE_ADVERSE_REVIEW.md).
6. **Learner-mechanism work:** no probe is automatically authorized. MRFSS and WRLVT are both demoted by direct
   frequency and region-additivity counting antecedents.
7. **Scoped search stop:** the orthogonal second pass has zero learner-mechanism survivors. Reopen costly mechanism
   work only after a prospectively frozen repeated B2/B4 residual on admitted, non-public external data, or a precisely cited
   independently replicated residual matching the task, modality, and constraints with a predeclared reason B2 cannot
   address it. Low-cost system, data-objective, and evaluation ideation may continue without changing Lane 1 or
   consuming protected evidence.

The numbering preserves the existing portfolio IDs; it is not a priority typo.

## Latest mechanism-specific search

An October 17 follow-up searched the exact conjunction of paraphrase panels, same-example gradient differences,
environment/invariance subspaces, and orthogonal projection. It recovered the already logged adjacent families—SubPT,
null-space prompt tuning, invariant-feature recovery, prompt-sensitivity analysis, paraphrase-robustness training, and
general gradient-subspace projection. A subsequent exact search found R2F's same-fact multi-view paraphrase LoRA
gradient aggregation, a closer ingredient-level antecedent, though not source-balanced centered nuisance removal. The
search still found no direct antecedent for QUILT's complete estimator. That is only a `not found` result: it does not
establish priority, and R2F lowers rather than raises the novelty score.

## What would justify another search

The successor learner-mechanism search was activated after QUILT acquired closer direct antecedents, then concluded
with zero admitted learner-mechanism survivors. It may reopen only under the qualifying-residual rule above. A
successor must change the causal mechanism, target that observed bottleneck, and not combine the failed acronyms.

Cheap system, data-objective, and evaluation searches remain open. They must state their claim class explicitly and
cannot raise system novelty to 5.0 or above without a matched full-system versus component-ablation result under the same
records, updates, compute, serializer, and evaluator. Contracts and governance improve validity; they are not learning
methods.

## Anti-loop rules

- Search the exact mechanism and its mathematical synonyms before assigning a novelty score.
- Add every close antecedent, even if it lowers the score.
- Separate “not found in this search” from “first.”
- Record rejected ideas and why they failed.
- Do not raise novelty because the design document became longer.
- Do not combine two medium-novelty ideas and average their weaknesses away.
- Competition promotion is based on frozen evidence, not novelty; official scoring gives no complexity bonus.
- Score competition value, competition-system innovation, system novelty, learner-method novelty, and paper novelty separately.
