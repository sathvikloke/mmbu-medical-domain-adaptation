# Claude handoff: bounded next work

**Prepared:** October 17, 2026  
**Mode:** competition-first read-only review and synthetic CPU engineering first  
**Do not start:** source downloads, model downloads, public-set evaluation, GPU training, uploads, or submission

## Objective

Turn the audited portfolio into the smallest executable, challenge-compatible B0/B1/B2 dual-objective answer/context
experiment without filling unknowns with defaults. Follow the binding
[independent idea arbitration](INDEPENDENT_IDEA_ARBITRATION.md) and
[competition-first recipe](COMPETITION_FIRST_RECIPE.md). Treat MedQwen/B4 as an independent reproduction unless
official code and weights become available; allow MOSAIC only if its source-factor gate passes; keep QUILT diagnostic;
and do not implement MRFSS or WRLVT without a later reviewed work order triggered by either a prospectively frozen
repeated B2/B4 residual on admitted, non-public external data, or a precisely cited independently replicated residual matching the
task, modality, and constraints with a predeclared reason B2 cannot address it. Low-cost system/data/evaluation audit
may continue, but it must not alter frozen Lane 1, consume protected evidence, or be relabeled as learner-method novelty.

## Packet closure and authority

The [experiment-freeze contract](EXPERIMENT_FREEZE_CONTRACT.md) is binding. This handoff is executable only when a
`handoff_dependency_manifest` lists the canonical bytes and SHA-256 of every normative dependency below. If a member is
absent or hash-mismatched, return only `packet_incomplete`; do not create schemas, tests, command plans, or code from a
partial packet. A dirty working tree or mutable branch name is not a packet identity.

The manifest is not its own trust anchor. Before any write, require a separately supplied `handoff_launch_receipt`
that binds `config/claude-handoff-dependencies.json` and its expected canonical digest, names the approving authority
and package scope, and is independently acknowledged as `approved`. The repository copy may record
`pending_human_digest_acknowledgement`, but that state permits read-only review only. A rewritten manifest plus a
rewritten local receipt is not proof of approval. At launch, the verifier must receive the trusted-channel
acknowledgement digest independently and authorize only the specifically requested A–I package if it appears in the
unique approved scope.

The authorization verifier is itself a manifest member at `tools/team.py` with role `authorization_verifier`. Before
trusting its launch result, an operator must use an independently trusted SHA-256 implementation to compare those exact
bytes with the verifier member hash inside the independently acknowledged manifest. Self-verification alone is not a
trust anchor; an altered verifier invalidates the packet even if it prints success.

Claude may implement closed schemas, validators, and synthetic negative fixtures at `schema_ready`. Claude may not
choose hyperparameters, candidate profiles, loss shares, margins, seed sets, compute caps, data roles, or other
scientific values. `experiment_freeze_ready` is forbidden until the complete scientific-decision receipt predates all
model and biomedical outputs. Package D remains a parameterized `not_copyable_not_authorized` template until the exact
MOCS run-authorization object exists.

## Binding reading order

1. [Package A reconciliation](PACKAGE_A_RECONCILIATION.md) and the dated
   [package-status snapshot](CLAUDE_PACKAGE_STATUS.md), then the [Phase 1 acceptance contract](../phase1/ACCEPTANCE.md) and [schemas](../phase1/SCHEMAS.md)
   plus the binding [experiment-freeze contract](EXPERIMENT_FREEZE_CONTRACT.md)
2. [Project scorecard](PROJECT_SCORECARD.md), [independent idea arbitration](INDEPENDENT_IDEA_ARBITRATION.md),
   [research portfolio](RESEARCH_PORTFOLIO.md), binding
   [base-selection frontier](BASE_SELECTION_FRONTIER.md) and its [red-team](BASE_SELECTION_REDTEAM.md), and the
   [competition-first recipe](COMPETITION_FIRST_RECIPE.md) plus its binding
   [competition red-team corrections](COMPETITION_RECIPE_REDTEAM.md); the
   conditional [system-interaction hypothesis](SYSTEM_INTERACTION_HYPOTHESIS.md) is a preregistration target, not an
   admitted contribution or permission to expand Lane 1; the
   [multi-encoder branch](MULTI_ENCODER_BRANCH.md) is
   post-B2 and must not expand the initial compatibility scope; the
   [base-conditional preservation ablation](BASE_CONDITIONAL_PRESERVATION.md) is also post-B2 and must not replace the
   ordinary no-KL B2 or its separately identified unconditional-KL control; [weight interpolation](WEIGHT_INTERPOLATION_BRANCH.md) is post-B2 and
   limited to its closed coefficient set
3. [Annotation-to-task lattice](ANNOTATION_TASK_LATTICE.md), [context objective contract](CONTEXT_OBJECTIVE_CONTRACT.md),
   [unit-exposure audit](UNIT_EXPOSURE_AUDIT_SPEC.md), and the public-metadata
   [prospective source portfolio](DATA_SOURCE_PORTFOLIO.md) with its
   [metadata receipt](DATA_SOURCE_METADATA_RECEIPT.md), then the binding
   [source–factor incidence audit](SOURCE_FACTOR_INCIDENCE_AUDIT.md) and
   [crossover-source search](CROSSOVER_SOURCE_SEARCH.md)
4. [Organizer clarifications](ORGANIZER_CLARIFICATIONS.md) and the dated [task-protocol snapshot](TASK_PROTOCOL_SNAPSHOT.md)
5. [MedQwen reproduction gaps](MEDQWEN_REPRODUCTION_GAP.md)
6. [QUILT adverse review](QUILT_ADVERSE_REVIEW.md) and [factorial-update adverse review](FACTORIAL_UPDATE_ADVERSE_REVIEW.md), then the preserved [QUILT design](../superpowers/specs/2026-10-17-quilt-design.md), [MOSAIC design](../superpowers/specs/2026-10-17-mosaic-design.md), [novelty audit](NOVELTY_AUDIT.md), and [data gate](MOSAIC_DATA_GATE.md)
7. [QUILT synthetic proof obligation](QUILT_SYNTHETIC_PROOF.md), which is diagnostic and lower priority than Lane 1
8. [Release and submission rehearsal](RELEASE_REHEARSAL.md)
9. [MOCS access audit](MOCS_ACCESS_AUDIT.md)

If an older output conflicts with these files, stop and report the conflict. Historical reports are evidence, not
current decision authority.

## Execution order and write boundary

1. Accept the recorded QUILT adverse disposition as binding; do not rerun it to restore the old scores.
2. Package A is closed as `design_review_only` by [its reconciliation](PACKAGE_A_RECONCILIATION.md); do not rerun or
   extend it without a new approved scope.
3. B, C, H, and the command/schema design portion of D are only the next eligible requests. None may proceed until a
   fresh package-scoped receipt and digest acknowledgement authorize that exact package; sequencing never grants authority.
4. Package F owns the shared disabled-registry schema module and `[F]` fixtures; package G consumes that frozen schema
   read-only and owns only its H2 module and `[G]` fixtures. Package I runs only after F and G and consumes both modules
   read-only for composite and cross-claim `[I]` fixtures; it owns no schema or scientific values. This schema subtask may precede G, but the executable
   within-base competition manifest in F still requires G's immutable primary base-selection receipt. E may proceed
   only after B/C/G/F are passed or blocked for reasons E cannot affect, and only when A marks every QUILT
   semantic/geometry issue either `resolved in current design` or
   `blocking`; any `blocking` item stops E.
5. Do not submit D, load model weights, or use a GPU. The preflight remains a reviewed command plan and closed result
   schema until the account/allocation and run condition are separately authorized.
6. Place new review/design artifacts under `docs/team/` and synthetic code/tests only in the repository's reviewed
   Phase 1 locations. Do not rewrite hash-bound receipts, historical outputs, or authority registries to make new work
   appear pre-authorized.

Every changed file must map to one package and one acceptance row below. Mixed-purpose edits reject.

## Package acceptance matrix

| Package | Required artifact | Pass condition | Blocking result |
|---|---|---|---|
| A: portfolio reconciliation | Claim-to-gate table with evidence links, counterexample, severity, repair, and unknowns | Dual-objective B0/B1/B2 is primary; optimizer mass is unit-normalized; curriculum is an ablation; the conditional system interaction is challenged against its closest complete systems without promotion by prose; MOSAIC remains gated; MRFSS and WRLVT are demoted; every material claim is sourced or labeled hypothesis | Re-promoting a diagnostic/probe or conditional system claim by prose, missing direct antecedent, official-protocol overclaim, annotation-density weighting, or unfixed high-severity issue |
| B: lattice and exposure fixtures | File-to-contract trace, synthetic derivation/exposure fixtures, negative tests, exact command/receipt | Every deterministic edge round-trips; unit/view/token weights preserve one canonical unit mass through batching, accumulation, schedule, and resume; prohibited derivations fail closed without real biomedical/public data | Label invention, split/duplicate crossing, annotation-density or field-count weighting, mean-of-means aggregation, unequal schedule exposure, incomplete-count acceptance, public input, or a weakened validator |
| C: compatibility map | Revision-scoped tensor/module table, formulas, state-dict plan, and loader-risk comparison | Every observed name/shape cites exact pinned source; every unobserved mapping is `unknown`; B2 and custom paths have explicit synthetic tests | Floating revision, inferred tensor name/shape presented as fact, weights loaded, or custom loader assumed accepted |
| D: MOCS plan | Parameterized `not_copyable_not_authorized` template, closed result schema, resource cap, failure matrix, and abort criteria | Plan binds scheduler/account/allocation/model/cache/runtime evidence and cannot become copyable or start a job without the separate run condition | Job submission, copyable command before authorization, unbounded resource request, network/model fallback, missing export/reload, or secrets in evidence |
| E: QUILT diagnostic proof | Reviewed design/test matrix, then deterministic CPU runner and canonical evidence bundle only after higher-priority Lane 1 gates | Every S0–S29 case and required negative comparator executes; invalid regimes reject; outputs are labeled `synthetic_algebra_only` | Skipped case, post-hoc tolerance/rank, stacked-row primary estimator, optimizer-state contamination mislabeled safe, or biomedical/model claim |
| F: competition-first manifest | Immutable synthetic experiment manifest plus validators for closed B0/B1-L/B2-P/B2-F architecture/objective-profile pairs, canonical-rational answer/context shares, masks, per-unit loss mass, sampling, geometry frame, serializer, preservation, typed visual-dependence probes, statistics, and promotion; package F also owns the shared v1 registry module, H1/composite representation, and `[F]` fixtures | Every pair and comparator is declared; public data cannot enter; unavailable context is masked; total exposure is normalized by independent unit; loss shares sum exactly to one; every `[F]` registry fixture passes; v1 research objects cannot transitively enter a generic Phase 1 experiment or delay Lane 1; no model/data run occurs | Hidden profile, invented context, annotation-density weighting, unequal schedule exposure, public-set dependency, geometry/output mismatch, invalid counterfactual targets, failed visual-dependence gate, missing base control, adaptive candidate creation, or any executable path from a v1 research object |
| G: base-selection frontier manifest | Closed synthetic F0/joint-decision/F2 manifest/test matrix for candidate admission, screen-specific module maps, exposure and compute matching, context partial-identification bounds, seed policy, robust selection, and handoff of one immutable base digest to F; G consumes the frozen v1 schema and owns only the H2 module and `[G]` fixtures | Base-only ranking is impossible; unknown context cannot be filled; unequal exposure, asymmetric troubleshooting, rank reversal, confirmation failure, or public-set dependency yields unresolved/no-selection; every `[G]` fixture passes; H2 receipts cannot satisfy primary competition selection; no weights/data run occurs | Claiming intrinsic adaptability, guessed context, model-specific tuning, selected-winner-only exposure advantage, runner-up rescue on reused confirmation, an unreceipted base entering F, editing the F-owned schema, or enabling the research comparison without a separate versioned execution contract |
| H: source-portfolio admission design | Source-to-atom/factor matrix and metadata-only intake decision packet for BUS-BRA, BUS-UCLM, selected MedMNIST+, BBBC038, and conditional BUSI-WHU | Every fact cites a primary record; rights, grouping, source family, task atoms, overlap, release, and role are separate fields; unknowns stay unknown; source-adjusted rank and leave-one-family-out connectivity are reported; no pixels, restricted files, or MMBU examples are opened | Treating a repository license as weight-release approval, treating wrapper subsets as independent sources, guessing patient joins, counting trivial object labels as semantic transfer, hiding the recorded rank deficiency, or downloading data |
| I: disabled-registry integration | Post-F/G synthetic composite and cross-claim tests consuming the frozen F and G modules read-only | Every `[I]` fixture begins from one fully valid registry, mutates exactly one field or relationship, and rejects for the intended reason; H1, H2, composite, and full-system artifact bindings close transitively; no schema, scientific value, data, model, or execution state changes | Missing valid dependency, early unrelated rejection counted as a pass, F or G module edit, mixed-purpose fixture, receipt laundering, pooled claim, or executable transition |

A package can be `passed`, `blocked`, or `not_run`; `designed` and `schema_ready` are not `passed`. Partial evidence never
upgrades another package. If any required source is unavailable, return the exact missing artifact and smallest safe
next read-only step. Use qualified identifiers from the freeze contract; unqualified `B1`, `B2`, or `F1`, and generic
`validation` used for the competition confirmation role, reject in an executable record.

## Work package A: portfolio reconciliation review

Return one table with columns `claim`, `supporting evidence`, `strongest counterexample`, `severity`, `repair`, and
`still unknown`. Start by verifying that the competition-first recipe, QUILT adverse disposition, scorecard, portfolio,
and idea ledger agree. Then cover:

- whether the task lattice can introduce label leakage, pseudoreplication, ontology shortcuts, or source shortcuts;
- whether each independent unit receives equal total optimizer mass before prospective source/task/context balancing and
  whether missing context fields remain masked rather than inferred;
- whether B2-P and B2-F are genuinely parameter- and active-FLOP-matched;
- whether MOSAIC routing is non-circular and identifiable;
- whether the factorial interaction statistic predicts function-space composition failure beyond ordinary task-vector
  analogy, update norm, cosine similarity, and seed variance; do not treat Möbius notation as novelty;
- whether every proposed novelty claim survives the cited routed-LoRA, spectral-LoRA, and compositional-medical work;
- whether H1 answer/context × unit-normalization and H2 adaptation-response frontier selection remain separately
  identified, with visual-dependence/preservation treated only as common gates and no pooled conjunction score;
- whether the promotion rule could select on noise or repeated validation access;
- whether the one-time masked `recipe_confirmation` opening, shared paired resamples, and simultaneous confirmatory bounds cover
  every contrast that can promote or block QUILT;
- whether any custom adapter/router state can plausibly violate a standard challenge loader; and
- whether any code path still assumes the historical rationale-inside-JSON profile, silently repairs malformed output,
  or invents multi-label judge behavior not present in the current card.

For QUILT specifically, try to disprove that within-unit centered gradients over complete same-fact prompt panels
identify nuisance. Check LoRA
factor gauge, deterministic calibration, per-module geometry, answer-length/tokenization confounds, fixed-basis capacity,
teacher-forcing versus generation mismatch, and whether random-energy or scalar-shrinkage controls can explain the
entire proposal. Compare the claim directly with GERNE's gradient-difference debiasing. Search for closer prior art
before commenting on novelty.

Treat QUILT's pair classes as non-interchangeable: strict prompt panels keep the image, grounding carrier, semantic
answer, and exact serialized target tokens fixed; open/closed answer-interface pairs and grounding-carrier pairs are
secondary or exploratory only. Verify complete-panel balance. The primary basis must use the `m` source-balanced template
centroids after within-unit centering, with equal source-group mass and then equal unit mass within source; only that
balanced centroid matrix has the unconditional `m-1` structural rank ceiling. Stacked unit-level centered rows can have
higher rank under fact-by-template interactions and are forbidden as the primary covariance. Report source-template
deviation and unit-template residual energy as falsification diagnostics. Graph connectivity applies only to the
separately named incomplete-panel experiment.
Also test the optimizer geometry rather than stopping at the raw gradient: a nonscalar Adam-style preconditioner can
rotate a projected gradient back into the nuisance span, so the final transformed step must be projected and the
applied delta receipted. Finally, rotate the fixed orthonormal `A` basis within its row subspace and determine which
claims remain invariant under projected SGD and which fail under elementwise adaptive optimization.
The confirmatory condition uses `lambda = 1`. Treat every `lambda < 1` condition as a named dose-response ablation that
is expected to retain nuisance energy and is ineligible for the complement-invariance or quotient claim.
The confirmatory optimizer must be projected SGD or linear scalar momentum whose state is updated only from projected
gradients and projected before use. A post-projected Adam-style condition is exploratory: nuisance energy can alter its
moments and therefore its allowed future step even when the final delta is orthogonal. Test two raw-gradient sequences
with identical quotient projections but different nuisance components; their confirmatory applied deltas must match.
The primary estimator uses identical complete prompt panels with at least three templates per independent unit,
within-unit centering, equal unit/template mass, and cross-unit averaging into one centroid per template before SVD.
The averaging is hierarchical: equal source-group mass, then equal independent-unit mass within source.
Do not feed all centered unit rows or all pairwise differences to the primary covariance: interactions can violate the
claimed rank ceiling, while dependent edges and graph topology can rotate a truncated basis. Any interaction-basis or
incomplete-panel graph reconstruction is secondary and must pass its own falsification fixtures first.
Freeze source-group-disjoint `basis_fit`, `basis_audit`, `adapter_train`, and `validation` roles before prompt expansion.
No independent unit or duplicate group may cross roles. A basis fitted and scored on the same units is not mechanism
evidence; a later all-admitted-data competition refit is submission-only evidence.
Independently freeze prompt-lineage-disjoint `basis_templates`, `audit_templates`, `train_templates`, and
`validation_templates`. QG-1 must test the frozen basis on never-fitted audit-template families without tuning it; final
transfer uses a separately untouched validation-template family.
Use the Categorical Atlas of PEFT as binding prior art for gauge/optimizer claims. Include a budget-matched ordinary
R2F-style synchronized complete-panel mean-gradient control, compute-matched against independently sampled Q0 views;
report exact equality where implied. Also include a paraphrase-augmentation control and, if its published procedure can be reproduced faithfully, a LAP-style adversarial
paraphrase condition. If faithful reproduction is infeasible, mark that comparator `not implementable from available
evidence`; do not substitute an easier method under the same name.

Do not rescore upward for completeness of prose. A score may rise only when a concrete failure mode is removed.

## Work package B: synthetic task-lattice slice

Implement only synthetic fixtures for the deterministic edges in `ANNOTATION_TASK_LATTICE.md`:

- mask to tight box under the pinned pixel convention;
- source box parse/serialize round trip;
- class plus box and class plus mask views;
- complete-instance-set counting;
- open/closed ontology normalization and deterministic option permutation;
- split-before-expansion enforcement; and
- rejection of missing lineage, incomplete counts, label invention, duplicate-group crossing, and public-source inputs.

Also implement every synthetic trap in `UNIT_EXPOSURE_AUDIT_SPEC.md`. The effective optimizer-step loss must aggregate
the global weighted numerator and denominator; an average of unequal microbatch or device-local means is a blocking
failure. Schedule variants must differ only in order, including at eligible early-stop checkpoints.

Use test-driven changes. Do not place real biomedical data in fixtures. Do not weaken a fail-closed gate to make a test
pass. Output a file-to-contract trace and the exact test command/result.

## Work package C: model-tree compatibility map

Without loading weights, inspect only pinned configuration/module source available under the authorized environment and
produce:

- candidate Qwen vision, projector, attention, and MLP tensor names and shapes;
- B2 target-module options with trainable and active-parameter formulas;
- MedQwen paper equation to candidate-module mapping, with unresolved cells marked `unknown`;
- MOSAIC early vision tap, pooled question state, residual insertion, and state-dict plan;
- minimum synthetic gradient/state-dict/autocast tests; and
- standard PEFT versus custom loader/export risk comparison.

Do not implement or select a second vision encoder in package C. At most, add a separate `unknown/not_run` extension
row for the multi-encoder branch after the native B2 map is complete; its specialist release, duplicate-native control,
active-parameter count, fusion geometry, and offline closure are separate prerequisites.

No target map becomes authoritative until it is confirmed against the exact pinned model revision.

## Work package D: MOCS preflight plan

Prepare only a parameterized `not_copyable_not_authorized` template and result schema until a separate
`mocs_run_authorization` binds scheduler, partition, account/allocation, GPU count/type, CPU, RAM, wall time, storage,
cache roots, and the exact command environment. Do not call the template copyable or passed. Once that object and the
explicit run condition exist, the first preflight is capped at one job and zero retries and must be bounded to:

1. environment and scheduler receipt;
2. exact model/processor/cache hashes;
3. one native load;
4. one deterministic forward;
5. one synthetic training step for the lowest-complexity enabled `recipe_arch::B2-P` objective profile;
6. peak host/GPU memory and wall time;
7. save/export; and
8. fresh network-denied reload and matching forward.

The job must fail closed on an unpinned revision, network miss, unsupported dtype, missing cache, or state-dict mismatch.

## Work package E: QUILT diagnostic synthetic proof obligation

Do not implement this package until the QUILT adverse review is accepted, the design review has no unresolved semantic
or geometry contradiction, and higher-priority Lane 1 readiness work is not blocked by it. Passing this package cannot
restore flagship status or authorize biomedical training. Then review and, only after review, implement the cases in
[QUILT_SYNTHETIC_PROOF.md](QUILT_SYNTHETIC_PROOF.md) without biomedical data or model weights. The proof must include:

1. a linear generator with independently controlled fact and interface subspaces;
2. exact complete-panel template-centroid conformance vectors under known nuisance rank, with separately measured
   unit-by-template interaction residuals;
3. correlated fact/interface, shuffled-panel, between-fact, random-rank, random-energy, scalar-shrinkage, zero-gradient, and rank-error
   counterexamples;
4. a reparameterization test proving why raw trainable-`A/B` LoRA gradients are invalid and fixed-`A` coordinates are
   stable for this purpose;
5. an optimizer-rotation test proving why raw-gradient projection alone does not constrain an Adam-style applied step;
6. an orthogonal fixed-`A` basis-rotation test that reports effective-update invariance or rejects the optimizer claim;
7. connected/disconnected interface-graph fixtures plus an interaction-rank trap proving that the `m-1` ceiling
   belongs to the balanced template-centroid matrix, not stacked unit-level centered rows;
8. a source-imbalance trap proving that within-source row duplication cannot rotate the shared centroid basis;
9. a perturbation-bound fixture proving recovery below a registered singular-gap boundary and rejection at or above
   the non-identifiable boundary;
10. an R2F-style equal mean-gradient comparator over the same complete views and budget;
11. unseen audit-template effects both inside and outside the planted nuisance subspace, with template-family lineage
    crossing rejected;
12. multiplicative prompt-difficulty scaling that rejects when the centroid enters the task span;
13. a high-dimensional centroid-power fixture that rejects noise-dominated apparent low rank;
14. deterministic module-local covariance/sketch/SVD behavior; and
15. numeric tolerances derived from dtype and conditioning rather than chosen after test output.

Return a design and test matrix first. Do not write production code or describe a synthetic recovery as medical-model
evidence.

## Work package F: competition-first synthetic manifest

Before model weights or biomedical records are used, encode the decisions in
[COMPETITION_FIRST_RECIPE.md](COMPETITION_FIRST_RECIPE.md) under the exact fields and state transitions in
[COMPETITION_MANIFEST_SPEC.md](COMPETITION_MANIFEST_SPEC.md), using a closed synthetic manifest and validators:

1. immutable candidate IDs for B0, B1-L, B2-P, and conditional B2-F;
2. explicit module/profile fields whose unverified native names remain `unknown` rather than guessed;
3. source/task balancing, independent-unit grouping, split-before-expansion, and prompt-lineage holdout rules;
4. original-pixel `xywh` geometry with processor-frame and inverse-transform receipts;
5. exact protocol-proxy prompt/serializer IDs and an explicit rationale-target policy;
6. AdamW, budget, seed, early-stop, KL-preservation, negative-flip, and public-firewall fields;
7. normal competence, descriptive blank/no-image alarm, source-valid answer-preserving intervention, source-valid
   answer-changing paired-image/region intervention, and a conjunctive fail-closed promotion rule;
8. shared paired group-bootstrap seeds, practical margins, simultaneous decision rule, and one `recipe_confirmation` opening;
9. offline export/reload and release-rehearsal gates; and
10. optional A1/A2 ablations disabled by default and unable to appear after validation opens.

Also design, but do not enable, closed `SYS-A0`–`SYS-A3` research-comparison objects from
[SYSTEM_INTERACTION_HYPOTHESIS.md](SYSTEM_INTERACTION_HYPOTHESIS.md). They must bind separate task and context primary
estimands, the exposure-equalization equivalence/null prediction, independent-source-parent replication, exact
supervised-token/update/compute matching, and H1-specific kill rules. The optional composite object—not H1—binds the
complete-system comparators and superiority decision. Their existence cannot
authorize execution, add a candidate after protected evidence opens, or delay the primary B0/B1-L/B2-P/B2-F lane.
Use exactly the closed H1 and optional composite representations plus every `[F]` fixture in the disabled research-comparison
registry of [COMPETITION_MANIFEST_SPEC.md](COMPETITION_MANIFEST_SPEC.md); do not invent additional fields or scientific
values.

Use synthetic records only. Return the schema/test matrix for review before implementation. A passing manifest proves
that the experiment is specified; it does not prove data readiness, model compatibility, or performance.

## Work package G: base-selection frontier manifest

Before F can bind a competition base, encode [BASE_SELECTION_FRONTIER.md](BASE_SELECTION_FRONTIER.md) and
[BASE_SELECTION_REDTEAM.md](BASE_SELECTION_REDTEAM.md) as a closed synthetic manifest/test matrix:

1. immutable eligible base IDs, revisions, licenses, size/release routes, and pre-output enablement rules;
2. F0 mechanical gates separated from biomedical or score evidence;
3. disjoint group/source `frontier_train`, `frontier_tuning`, and untouched `frontier_decision` roles;
4. joint-decision untouched-base arm deferred until all F2 checkpoints/artifact digests and failures are committed;
5. F2 response to one frozen screen, with architecture-specific module maps declared before outputs and tuning confined
   to `frontier_tuning`;
6. independent units, images, visual tokens, supervised tokens, optimizer updates, active FLOPs, wall time, memory,
   troubleshooting attempts, and seeds bound for every candidate;
7. context partial-identification intervals and a robust-dominance/unresolved rule;
8. shared source-group resamples, simultaneous comparisons, mixture-rank-reversal behavior, and practical margins;
9. common-seed or prospectively frozen one-seed-plus-selected-confirmation policy with no runner-up rescue; and
10. one immutable selected-base receipt/digest or `no_selection`, consumed upstream of F.

Also design, but do not enable, `FRONTIER-U` and `FRONTIER-R` isolation records. The research claim requires different
selected immutable bases and a one-opening second untouched cohort under a separately frozen decision object. The
competition base-selection result remains valid even if this research comparison is absent or killed.
Use exactly the closed H2 object in the disabled research-comparison registry of
[COMPETITION_MANIFEST_SPEC.md](COMPETITION_MANIFEST_SPEC.md), consume the shared schema read-only, and implement every
`[G]` fixture in a G-owned module. Passing its synthetic fixtures proves representation only,
not selection quality or authority to open either cohort.

Use closed synthetic grades and resource facts only. Return the schema and negative-test matrix before code. Passing G
proves decision mechanics, not that any candidate loads, adapts, or will score well.

## Work package I: disabled-registry integration

After F and G pass independently, construct one fully valid synthetic registry from their frozen exported fixtures and
run every `[I]` composite/cross-claim negative fixture from
[COMPETITION_MANIFEST_SPEC.md](COMPETITION_MANIFEST_SPEC.md). Each test mutates exactly one field or relationship from
that valid baseline and must assert the intended rejection code, not merely any rejection. Consume F and G modules
read-only. Do not add schema fields, choose scientific values, open data, load a model, create an executable transition,
or let an H1/H2 research receipt satisfy a primary competition receipt. Passing I proves only closed cross-object
representation and validator ordering.

## Work package H: metadata-only source-portfolio admission design

Adversarially review [DATA_SOURCE_PORTFOLIO.md](DATA_SOURCE_PORTFOLIO.md) without downloading source files. Produce:

1. one row per exact release, upstream parent, and prospective task atom;
2. primary-source citations for license, version, counts, grouping claims, labels, masks/boxes, and official splits;
3. separate decisions for dataset access, competition training, derived-view creation, trained-weight release, and
   attribution—never one blanket `allowed` field;
4. conservative source-family joins, including BBBC038/039, ROCO/PMC-VQA, MedMNIST shared origins, and the Kvasir family;
5. a projected modality × specimen/scale × task-geometry incidence table labeled `metadata_projection_only`;
6. the exact fields that must be confirmed from BUS-BRA/BUS-UCLM archive listings and metadata before pixels;
7. a no-download intake sequence, stop conditions, and canonical receipt schema; and
8. an explicit two-level statement: the current metadata-only portfolio structure is a provisional fail under the
   recorded optimistic rank stress test, while exact admitted-data G-1 remains `not evaluated` until admitted rows
   populate and rank the frozen matrix.

Do not infer a patient identifier from filenames unless a primary source defines it. Do not promote BUSI-WHU because a
third-party repackaging shows masks. Do not count BBBC's object type `nucleus` as a meaningful medical class. A good H
result narrows the first intake and exposes blockers; it does not approve a dataset or raise the readiness score.

## Required final response

Return:

1. concise findings ordered by severity;
2. changed files and exact tests;
3. package status table (`passed`, `blocked`, or `not_run`) with one evidence path per status;
4. remaining unknowns, without guessed values;
5. whether `recipe_arch::B2-P` synthetic engineering is ready;
6. whether B4 is faithful, independent, or not implementable from available evidence;
7. whether MOSAIC passes G-1 (expected answer: `no` at the provisional portfolio-structure screen and `not evaluated`
   for exact admitted-data G-1 until a valid incidence table exists); and
8. whether QUILT's QG-0 through QG-3 are specified tightly enough to implement (expected current answer is design-only,
   not passed);
9. whether package G's base-selection frontier and package F's within-base competition manifest are review-ready;
10. whether package H preserves the Tier 1 ordering or changes it, with primary evidence; and
11. the single safest next authorized action.

Do not implement MRFSS or WRLVT in this handoff. MRFSS has a direct characteristic-function frequency-counting
antecedent; WRLVT has direct region inclusion–exclusion/additivity counting antecedents plus region/cycle consistency
overlap. A later synthetic work order would authorize only a review, never biomedical data or GPU work.

## Automatic rejection conditions

Reject the handoff if it claims model quality without a model run, describes public MMBU examples as training/dev data,
converts captions into unreviewed diagnoses, treats views as independent samples, guesses missing MedQwen details,
silently selects hyperparameters, ranks bases only by untouched performance, invents missing context values, starts a
GPU job, downloads source data, treats aggregate licensing as source admission, or relaxes a Phase 1 gate.
