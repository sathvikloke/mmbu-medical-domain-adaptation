# Competition-first recipe red-team

**Date:** October 17, 2026  
**Scope:** design logic only; no data, model, or result claim

## Disposition

The competition-first direction survives, but successive passes found invalid visual-reliance shortcuts, adaptive-
selection risks, overbroad authority blocking, an undefined comparator edge, and a rationale-fabrication path. The
binding recipe and manifest specification are amended by the resolutions below.

## Findings

| Severity | Finding | Why it matters | Binding repair |
|---|---|---|---|
| Critical | `normal accuracy - blank-image accuracy` is not a causal image-reliance measure | A candidate can enlarge the gap by becoming worse on an out-of-distribution blank input; the metric can rise without using valid image evidence better | Treat blank/no-image as a shortcut alarm only. Never reward a larger gap by itself. Require normal-image non-regression plus separately valid answer-preserving and answer-changing paired interventions |
| Critical | “Wrong-image swap within a compatible stratum” does not define the expected answer | A same-label swap can be ignored and still pass; a different-label swap creates an invalid hybrid unless the prompt remains generic and the swapped image has its own authoritative atom | Use only source-authorized counterfactual pairs where the exact same generic prompt/template is valid for both images and each image has its own source target. Score target tracking for both directions. Otherwise mark the probe inapplicable |
| High | Geometry perturbation mixes invariance and sensitivity | Small overlay jitter that preserves the referred object should not change the answer; moving the region to a different annotated object should change it. One undifferentiated metric cannot test both | Register `answer_preserving_geometry` and `answer_changing_geometry` separately, with source-authoritative targets and applicability rules |
| High | Per-checkpoint safety testing can become another adaptive validation channel | Checking every checkpoint and choosing the one that passes the nicest safety slice reuses the development set and inflates selection | Development may drive early stopping under one frozen scalar/hierarchy. Untouched validation is opened once for the already selected candidate/checkpoint and deterministic promotion rule |
| High | Base-preservation KL can preserve base errors and suppress needed adaptation | Unconditional distillation rewards the base even when it is confidently wrong or off-domain | Freeze the preservation population and eligibility rule before training. Report the no-KL ablation. Use known-correct/approved general items where labels exist; otherwise call it behavior retention, not correctness preservation |
| High | “Same budget” is ambiguous across language-only and projector-plus-LoRA candidates | Equal optimizer steps do not equal examples, supervised tokens, active FLOPs, or wall time; a larger candidate can win through extra compute | Freeze both an exposure-matched primary comparison and a measured-compute sensitivity comparison; always report trainable parameters, active FLOPs, peak memory, and wall time |
| Medium | A rationale-before-JSON protocol has no automatically valid rationale supervision source | Training fabricated rationales can inject unsupported medical statements; answer-only targets may violate the visible prompt contract | Freeze separate `rationale_policy` and `answer_policy`. Never synthesize medical rationales from a label, box, mask, or metadata. Use exact admitted source-supported rationale text only; otherwise train answers and label the protocol mismatch |
| Medium | Macro-source/task robustness cannot claim official-score optimality | Hidden source/task weights and judge behavior are unknown | Use macro-source/task as a robustness decision, report natural-weight sensitivity, and never call it the official objective |
| High | Global authority blocking prevents useful independent work | A final context prompt or judge ambiguity is irrelevant to loading the pinned model, measuring memory, or proving export/reload; treating it as a universal stop delays evidence and invites last-minute integration failure | Bind blockers to transitions: native preflight, data/experiment freeze, validation opening, and official release each require only the authority they actually consume |
| High | “Beat the simpler LoRA” is undefined for B1-L and for multiple objective profiles | B1-L has no simpler adapted candidate; disabled architectures and answer/context allocation profiles make a fixed architecture-only chain ill-defined | Give every architecture/objective-profile pair a unique candidate ID. Freeze its comparator map after prospective enablement: every adapted candidate→B0, same-profile simpler architectures where enabled, and the task-only/static controls required to isolate its claim |
| High | Rationale supervision can silently fabricate medical evidence | Turning labels, boxes, masks, or metadata into fluent explanations creates unsupported training claims and may reward hallucinated evidence | Default to explicit answer-only training; permit rationale-bearing targets only with immutable source text, derivation authority, rights, and answer-consistency receipts; prohibit model-generated and label-template rationales |

## Correct visual-dependence panel

Every probe has a typed estimand and can be `inapplicable`; inapplicability is not failure and cannot be imputed.

1. **Normal competence:** performance on the authoritative normal image/target pair. This can never regress beyond its
   registered tolerance.
2. **Blank/no-image shortcut alarm:** prediction stability, confidence, and accuracy without usable image evidence.
   This is descriptive evidence of text-prior exposure, not a quantity to maximize.
3. **Answer-preserving visual intervention:** a source-authorized or deterministic transformation proven not to change
   the target (for example, permitted display/overlay perturbation inside tolerance). Require prediction/score
   invariance while preserving normal competence.
4. **Answer-changing paired-image intervention:** two independently valid source units use the same generic prompt and
   serializer but have different authoritative targets. Score whether predictions track each image's own target in both
   directions. Do not create a hybrid label.
5. **Grounding sensitivity:** for multi-instance units only, compare two source-annotated regions under the same generic
   region question; each region retains its own authoritative class. Separately test answer-preserving overlay jitter.

The gate is conjunctive: normal competence, answer-preserving invariance, and answer-changing target tracking must meet
their registered bounds. A blank-image gap cannot compensate for failure of any of them.

## Selection hierarchy

1. Use development roles for the frozen early-stop statistic and candidate selection only.
2. Select exactly one candidate/checkpoint before opening validation.
3. Run the fixed validation panel once with shared resamples and simultaneous bounds across every primary and blocking
   safety endpoint.
4. Emit `promoted`, `no_eligible_candidate`, or `retired` mechanically.
5. Do not inspect a failed validation result and promote the runner-up on the same population. Doing so converts the
   population to development and requires a new independent validation population.

## Residual ceiling

This red-team pass originally held the competition-design score at **8.8/10** because it removed logical errors without
new evidence. The later independent arbitration found and repaired a separate context-objective omission and raised
the prospective design judgment to **9.0/10**. The October 18 executability audit supersedes that estimate with
**8.4/10** after finding uninstantiated scientific values, ambiguous context-missing mass, confirmation-role conflicts,
and unconfirmed loader compatibility. None of these numbers is model evidence; eligible data, native measurements,
the official evaluator, and empirical results remain absent.
