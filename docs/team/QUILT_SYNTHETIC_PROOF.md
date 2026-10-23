# QUILT synthetic proof obligation

**Date:** October 17, 2026  
**Status:** exact pre-implementation specification; no tests or model evidence yet

## Purpose

This document defines the smallest synthetic evidence that must exist before QUILT may touch biomedical data. It tests
whether the proposed estimator identifies a planted presentation-interface subspace, whether its gates reject
non-identifiable cases, and whether common implementation shortcuts create false recovery.

The synthetic program must be deterministic, standard-library or NumPy-sized, CPU-only, and independent of model
weights. Passing it proves algebra and fail-closed behavior only.

## Reference coordinate system

Use an exact low-dimensional parameter space with ordered basis `e1 ... e8`:

- planted interface subspace `N = span(e1, e2)`;
- planted fact subspace `S = span(e3, e4, e5)`;
- unused/noise complement `R = span(e6, e7, e8)`.

Use at least four fact vectors spanning `S` and three presentation interfaces whose centered effects span `N`. Every
fact must appear under every interface in the exact-identification fixture so complete-panel centering is possible.

The estimator consumes gradients and pairing metadata, not the planted bases. The planted bases are available only to
the synthetic judge.

## Conformance cases

| ID | Construction | Required result |
|---|---|---|
| S0 exact additive prompt intervention | `g_zv = s_z + n_v`, complete factorial facts × strict prompt interfaces, identical serialized targets, no noise | Cross-unit template-centroid estimator recovers rank 2; maximum principal angle to `N` is within tolerance; projected gradients retain all `S` energy and remove all centered `N` energy |
| S1 centered noise | Add seeded zero-mean noise in `R` at registered scales | Centroid recovery/stability degrades with signal-to-noise ratio and improves with independent-unit count; pass only inside the registered boundary |
| S2 incomplete panel | Remove interfaces nonuniformly by fact | Primary estimator rejects the incomplete unit; a separately named graph reconstruction reports the exact reduced estimand and never substitutes between-fact rows |
| S3 fact/interface sampling correlation | Correlate interface availability with fact while retaining a balanced complete-panel subset | Complete-panel estimator recovers from the balanced subset; an unpaired covariance comparator is biased |
| S4 subspace overlap | Add a fact component in `e1` | Overlap gate rejects; projection is shown to remove the known clinical-signal component |
| S5 multiplicative interaction | `g_zv = A_v s_z + n_v` with interface-specific rotation of `S` | Interaction-residual gate rejects the additive-identifiability claim; no successful “nuisance recovery” label is emitted |
| S6 per-view normalization trap | Compare centered `unit(g_zv)` with center-first common unit scaling | Per-view normalization fails exact cancellation for a constructed unequal-norm case; production validator forbids it |
| S7 stochastic-state trap | Add independent dropout-like noise to the two views | Non-identical execution-state receipt rejects calibration before covariance estimation |
| S8 rank misspecification | Fit `k = 0, 1, 2, 3, 4` to planted rank 2 | Under-rank leaves interface energy; over-rank removes `S`/`R` energy or loses stability; only the predeclared selection rule may choose rank |
| S9 shuffled/between-fact control | Assemble panels or differences across different facts | Control basis fails planted-`N` recovery or is flagged by metadata; it cannot pass as the real-panel condition |
| S10 random controls | Same-rank random, removed-energy-matched random, and scalar shrinkage | Controls match their intended rank/energy/norm quantities but not planted-`N` recovery |
| S11 module scaling | Two modules with identical planted structure but 100× gradient scale difference | Module-local estimator recovers both; prohibited global covariance is demonstrably dominated by the large module |
| S12 sign/order invariance | Permute facts/interfaces and flip SVD signs | Projector `UU^T` and judgment remain identical within tolerance |
| S13 sketch fidelity | Compare exact template-centroid matrix SVD with each proposed deterministic sketch size | Registered sketch either meets projector error bound or rejects; no silent approximation |
| S14 LoRA gauge trap | Construct equivalent `BA = (BC)(C^-1A)` factorizations with different raw factor gradients | Raw trainable-`A/B` geometry differs and is rejected; frozen-`A` coefficient coordinates remain the declared geometry |
| S15 zero/nonfinite/extreme gradients | Insert zero, NaN, infinity, and norm outliers | Each produces the exact registered rejection; no clipping or deletion occurs without a receipt |
| S16 duplicate weighting | Repeat records from one already identified duplicate group or repeat one template row | Duplicate-group collapse plus unit-first complete-panel weighting preserves equal unique-unit mass and template balance; treating repeated records as new units or raw rows fails the negative comparator |
| S17 token-length confound | Multiply one interface gradient by a target-length factor before and after target-token normalization | Registered normalization removes the planted scalar effect; remaining difference is reported separately |
| S18 optimizer-rotation trap | Project a raw gradient into `N`'s complement, then apply a seeded nonscalar diagonal preconditioner whose output has nonzero `N` energy | Raw-gradient-only projection fails; projection of the final preconditioned/clipped/regularized step removes `N` energy, and the applied parameter delta matches that final step |
| S19 fixed-basis rotation | Replace frozen `A` by `R A` and coefficients by `B R^T` for seeded orthogonal `R`; compare effective updates under projected SGD and elementwise Adam-style preconditioning | Projectors and effective SGD updates are equivalent after coordinate transport; any coordinate-wise optimizer non-invariance is measured and forbids an intrinsic/gauge-invariant claim |
| S20 panel/graph topology | Use complete three-interface panels, then multiple connected edge graphs for the same planted effects, a disconnected graph, and duplicate parallel edges | Template-centroid estimator is topology-free and obeys rank at most `m-1`; raw edge covariance changes under graph topology; optional graph reconstruction is invariant within tolerance or rejects; disconnected components reject or are named separately |
| S21 partial-projection semantics | Apply `lambda = 0, 0.5, 1` to a vector with known nonzero `N` component and advance one exact step from `B = 0` | Only `lambda = 1` passes the complement invariant; partial values retain exactly the predicted nuisance energy and are labeled dose-response ablations, never quotient conditions |
| S22 optimizer-state contamination | Feed two gradient sequences with identical complement projections but different nuisance components into projected SGD/momentum and into Adam-style raw-state/final-step projection | Confirmatory projected SGD/momentum produces identical applied deltas; Adam-style state can change the allowed delta despite zero final nuisance energy and is labeled exploratory |
| S23 interaction-rank trap | Give each fact a different centered interface interaction so the stacked `d_zv` matrix has rank greater than `m-1`, while the balanced template-centroid matrix still has rank at most `m-1` | Production estimator uses only template centroids for the primary basis; stacked-row implementation fails conformance; residual energy is reported and rejects when above the registered ceiling |
| S24 source-imbalance trap | Create one large source with a source-specific interface direction and several smaller sources sharing the planted `N`; repeat already identified duplicate-group records only in the large source | Duplicate collapse followed by equal-source then equal-unique-unit centroids recovers the shared direction; naive raw-row/all-unit averaging rotates toward the large-source artifact and fails the negative comparator |
| S25 perturbation boundary | Add a known source-deviation/residual perturbation `E` around a rank-2 shared centroid matrix and sweep its norm across the preregistered singular-gap boundary | Below-bound projector error obeys the registered deterministic bound; at or above the non-identifiable boundary the estimator rejects instead of emitting recovered-rank evidence |
| S26 multi-view mean-gradient comparator | Compare compute-matched Q0 updates from independently sampled views with Q3-MV updates that synchronously average one unit's complete panel; include a linear case where they are algebraically equal and a registered interaction/order case where paths may differ | Equality is reported exactly when implied; any difference is attributed to synchronization/path, not a fictitious new gradient; Q3-MV never satisfies QUILT's nuisance-removal invariant merely by averaging |
| S27 unseen-template subspace transport | Fit `U` using one planted template family; evaluate a lineage-disjoint complete audit-template family whose effects are either inside the same `N` or contain a seeded off-span component | In-span audit templates meet the exact registered `coverage` floor while fact means stay below the `overlap` ceiling without modifying `U`; off-span and zero-denominator cases reject; template-family lineage crossing is a structural failure |
| S28 multiplicative difficulty scaling | Set `g_zv = c_zv f_z + n_v` with prompt-specific cross-entropy error scales, including a case whose balanced centered centroid is aligned with the planted fact span | Additive recovery is rejected; the runner reports fact-overlap and the interaction-model advantage; no nuisance-removal success is emitted merely because the centroid spectrum is stable |
| S29 high-dimensional centroid power | Generate module-local centroids in dimension `D` with seeded residual variance and sweep the planted spike through the registered finite-sample noise boundary while varying independent-unit count | Below-power modules reject; above-boundary recovery improves with independent units; a noise-dominated top singular vector can never pass because it looks numerically low rank |

## Exact judgments

The synthetic judge must compute, not eyeball:

- recovered rank under the registered selection rule;
- principal angles between recovered and planted subspaces;
- projector Frobenius/operator error;
- fraction of planted interface, fact, and residual energy removed;
- source/fact/interface label predictability only where the fixture defines those labels;
- invariance digest across sign/order transformations;
- exact unit and pair weights;
- shared template-centroid, source-template-deviation, and unit-template-residual energy, plus the rank of each matrix;
- per-module unseen-template `coverage` and fact-gradient `overlap` ratios plus matched-random controls;
- perturbation norm, retained singular-value gap, and the registered projector-error bound;
- registered centroid-noise power statistic, effective dimension, independent-unit count, and pass/fail boundary;
- multiplicative-interaction fit advantage and task-span contamination ratio;
- retained-gradient norm and cosine; and
- nuisance energy in the diagnostic gradient, preconditioned step, final projected step, and applied parameter delta;
- applied-delta equality for raw-gradient sequences with identical quotient classes;
- effective-update discrepancy after permitted frozen-basis rotations; and
- rejection code for every invalid fixture.

Every tolerance is derived before execution from dtype, condition number, and algorithm error. A tolerance may not be
relaxed after seeing a failing fixture.

## Required negative comparisons

The proof is incomplete unless the same runner evaluates:

1. raw pooled gradients;
2. per-view unit normalization;
3. global instead of module-local covariance;
4. shuffled same-shape pairs;
5. same-rank random projection;
6. removed-energy-matched random projection;
7. scalar gradient shrinkage; and
8. PCGrad/CAGrad on a compatible small multi-objective fixture;
9. raw-gradient-only projection followed by nonscalar diagonal preconditioning; and
10. projected SGD versus coordinate-wise Adam-style updates under an orthogonal rotation of the frozen `A` basis; and
11. identical quotient-class gradients with different nuisance components passed through each optimizer state update;
12. R2F-style equal mean-gradient aggregation over the same complete views and budget; and
13. unseen audit-template effects both inside and outside the planted nuisance subspace;
14. a GPM/InfLoRA-style fixed projection basis constructed from non-template activity; and
15. supervised paraphrase consistency on a toy predictive model with a degenerate constant-output failure case.

These controls prevent the synthetic demonstration from succeeding merely because every low-rank projection denoises a
tiny toy problem.

## Artifact contract

One execution produces:

- immutable fixture specification and seed;
- canonical input digest;
- estimator configuration and implementation digest;
- exact and sketched basis/projector summaries;
- per-case judgments and rejection codes;
- raw numeric arrays small enough to inspect;
- environment and dependency receipt;
- command, exit code, and test inventory; and
- one summary that labels the result `synthetic_algebra_only`.

The run fails if any case is skipped, any expected negative control is absent, a digest changes during execution, or a
result is labeled biomedical/model/competition evidence.

## Promotion rule

Synthetic QG-3 passes only when S0 and all permitted noisy/sketched cases meet their predeclared bounds, S18 proves the
actual applied step stays in the allowed complement, S19 prevents optimizer-coordinate dependence from being mislabeled
as an intrinsic method, S20 enforces graph/rank identifiability, S21 prevents a partial-projection ablation from being
reported as a quotient, S22 proves the confirmatory optimizer depends only on the gradient's quotient class, every invalid or non-identifiable case rejects for the correct reason, every negative
comparator behaves as specified, and S23 prevents unit-by-template interactions from being hidden behind a false
`m-1` rank claim, while S24 prevents source volume from defining the shared nuisance direction. S25 must additionally
prove that approximate recovery is emitted only inside the preregistered perturbation regime. S26 must demonstrate that
QUILT's synthetic claim is not merely a consequence of averaging paraphrase gradients. S27 must show that
cross-template subspace transport is a falsifiable prediction rather than a fitted tautology. A pass allows read-only
module mapping and a bounded model-mechanics proposal. It does not authorize
biomedical training.
