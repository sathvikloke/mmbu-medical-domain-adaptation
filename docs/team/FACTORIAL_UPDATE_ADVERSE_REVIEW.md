# Factorial-update decomposition adverse review

**Date:** October 17, 2026  
**Disposition:** useful diagnostic; reject as a replacement flagship method  
**Evidence class:** primary-literature screen and prospective design only; no implementation or model result

## Candidate reviewed

The candidate would train cell-specific LoRA updates on a prospectively frozen crossed design such as
`modality × specimen/scale × task geometry`, express every adapter as its effective weight update rather than its
non-identifiable LoRA factors, and use effect-coded factorial/Möbius contrasts to separate main effects from
interactions. Entire joint cells would be held out. The proposed test was whether lower-order effects could predict the
held-out update and held-out performance, after which only stable effects would be compiled into one ordinary LoRA.

This is a cleaner scientific question than another router. It is not, on current evidence, a new competition method.

## Binding verdict

The strongest fatal objection is that the candidate's headline operation is task-vector arithmetic on a structured
grid. [Editing Models with Task Arithmetic](https://arxiv.org/abs/2212.04089) already evaluates an analogy of the form
`A:B :: C:D` and uses three task vectors to improve the fourth without training on it. Calling the corresponding
alternating sum a factorial or Möbius contrast makes the bookkeeping more explicit, but does not by itself create a
new learning mechanism.

The potentially distinct contribution is narrower: a preregistered **interaction audit** that determines when
annotation/task factors are sufficiently additive for composition and rejects composition when they are not. That is
a diagnostic protocol. It should strengthen or falsify MOSAIC's factorization assumptions, not replace B2 or MOSAIC
as the submission architecture.

## Closest primary antecedents

| Work | What it already covers | Consequence for this candidate |
|---|---|---|
| [Editing Models with Task Arithmetic](https://arxiv.org/abs/2212.04089) | Addition, negation, and three-corner analogy prediction of a fourth task vector | Missing-cell arithmetic is not new |
| [Realistic Evaluation of Model Merging for Compositional Generalization](https://arxiv.org/abs/2409.18314) | Shared evaluation of merging for compositional capabilities in vision, generation, and NLP | Held-out composition evaluation is not new |
| [LoRA Soups](https://arxiv.org/abs/2410.13025) | Merging separately trained LoRAs for binary skill composition | Composing low-rank skill updates is not new |
| [Task Vector Bases](https://arxiv.org/abs/2502.01015) | A theoretically motivated basis for scalable task-vector arithmetic | A basis decomposition of updates is not new by itself |
| [Localizing Task Information / TALL-masks](https://proceedings.mlr.press/v235/wang24k.html) | Common multi-task vector plus task-specific supports | Shared versus task-specific update structure is established |
| [Adaptive Projective Gradient Descent merging](https://proceedings.mlr.press/v267/wei25k.html) | Decomposes and reconstitutes a multi-task objective while retaining a shared task-vector subspace | Update decomposition and shared-subspace preservation are crowded |
| [WUDI-Merging](https://proceedings.mlr.press/v267/cheng25h.html) | Theoretical approximate task-vector subspaces and interference removal | A linear-subspace account is not new |
| [On Task Vectors and Gradients](https://proceedings.mlr.press/v322/zhou26a.html) | Relates early task vectors to gradients and bounds multi-epoch approximation error | Cell updates can reflect optimization path, not only semantic factors |
| [When Do Task Vectors Interfere?](https://arxiv.org/abs/2608.09490) | Functional non-additivity over task-vector surfaces with norm-matched controls and cross-model audits | Measuring non-additivity is directly adjacent |
| [Distilling Linearized Behavior for Task Arithmetic](https://proceedings.mlr.press/v306/sommariva26a.html) | Trains models to inherit linearized compositional behavior without inference overhead | Loader-safe compiled composition is not unique |
| [Saliency-Aware Model Merging](https://proceedings.mlr.press/v306/park26l.html) | Saliency decomposition and rank-wise LoRA merging | Selective LoRA component retention is established |
| [Two-Stage Mixture-of-LoRA](https://arxiv.org/abs/2609.14350) | Shared and task-specific LoRAs in a medical VLM across heterogeneous tasks | Medical factor/task adapter separation is already occupied |

No direct paper using the exact phrase “Möbius inversion over a medical annotation lattice” was established. That is a
negative search result, not evidence of priority. The operations and primary prediction are substantially covered by
the antecedents above.

## Only surviving sharp claim

The defensible claim is not “factorial adapters compose.” It is:

> Under a source-balanced, identifiable crossed medical design, prospectively estimated lower-order contrasts predict
> the function of an unseen joint adaptation cell within a frozen tolerance **if and only if** the measured held-out
> interaction energy is below a preregistered threshold.

This is useful only if interaction energy predicts out-of-cell functional error beyond update norm, seed variance,
cell sample size, and ordinary task-vector cosine similarity. Otherwise the factorial language adds no information.

## Minimum synthetic proof that can kill it

Run this before a biomedical GPU experiment:

1. Freeze one tiny backbone and adapt only identical LoRA target modules in a balanced `2 × 2 × 2` synthetic grid.
2. Generate an additive world with known main effects and a second world with a controlled three-way interaction.
3. Train every observed cell from the identical initialization, optimizer, steps, batch order, and example count across
   at least three preregistered seeds.
4. Convert each adapter to the effective update `ΔW = B @ A`; never compare LoRA factors directly.
5. Hold out one cell at a time. Predict it using the registered lower-order contrast, task-arithmetic analogy, the
   grand mean, nearest cell, and a same-budget joint model.
6. Measure both effective-update error and functional predictive-distribution error on untouched inputs.
7. Sweep interaction strength. The registered interaction statistic must order the resulting held-out functional error
   and detect the predeclared failure boundary.

Kill the candidate if it cannot recover the additive world, if ordinary task arithmetic matches it, if its statistic
does not predict functional error, or if seed noise is the same size as the estimated semantic effects.

## Identification and correctness risks

- **LoRA gauge:** `A` and `B` factors are non-identifiable. All contrasts must use effective `B @ A` updates or model
  function, with a fixed target-module inventory.
- **Optimization-path aliasing:** multi-epoch nonlinear updates are not controlled factorial responses. Identical
  training budgets and replicated seeds are mandatory; an early-gradient condition should be reported separately.
- **Source aliasing:** a factor level represented by one dataset is a dataset identifier, not a modality or specimen
  effect. G-1 must pass before semantic interpretation.
- **Missing-cell non-identifiability:** higher-order interaction for an unseen cell cannot be estimated from lower-order
  corners. The method must reject rather than impute when interaction evidence is high.
- **Unequal information:** masks, boxes, labels, counts, and reports differ in supervision entropy and annotation cost.
  Equal row counts do not create a balanced experiment.
- **Function/weight mismatch:** low weight error need not imply low prediction error and vice versa. Function-space
  evaluation is primary.
- **Selection leakage:** thresholds, held-out cells, and which interaction orders are retained must be frozen without
  using MMBU public outcomes.
- **Compute multiplication:** cell-specific adapters times seeds can cost more than one strong joint B2 model while
  producing no deployable advantage.

## Matched controls

The minimum comparison set is: B2 shared LoRA; same-budget joint multi-task LoRA; ordinary three-corner task
arithmetic; norm-matched random update; nearest observed cell; mean observed update; LoRA Soups/CAT where applicable;
shuffled factor labels; source-ID factors; and an oracle including the held-out cell, reported only as an upper bound.
Parameter count, active FLOPs, optimizer steps, examples, source mixture, and seed count must be matched or disclosed.

## Scores

| Dimension | Score / 10 | Reason |
|---|---:|---|
| Competition idea | **5.2** | Expensive cell training and no demonstrated advantage over one shared LoRA |
| Concept novelty | **5.8** | A medical factorial interaction audit is distinctive packaging, but the core arithmetic is established |
| Paper-level method novelty | **4.3** | No new learner, theorem, or estimator beyond structured task-vector contrasts is established |
| Feasibility | **5.0** | Loader-safe final output is plausible, but the crossed source design and repeated cell training are demanding |
| Expected upside | **6.4** | Could prevent a false compositional claim and turn a failure into a rigorous diagnostic result |

## Portfolio action

Do not promote this candidate. Incorporate its interaction statistic, gauge-safe effective-update comparison, and
missing-cell rejection rule into MOSAIC's G-1/mechanism audit. It may become a publishable diagnostic if it predicts
functional composition failure beyond existing task-vector interference metrics. It may not delay Lane 1, and it does
not raise the current novelty score.
