# Experiment workflow

The [audited strategy v2](../../outputs/MMBU-domain-adaptation-plan-v2.md) preserves historical scientific rationale, including an earlier provisional model order. This guide supplies the current prospective workflow and supersedes that order: the competition shortlist remains empty until E01 is prospectively frozen and receipted. All actual model experiments remain pending; current software implements preparation and recordkeeping, not a training runner.

## State the question and authority first

Every experiment has a named owner, one hypothesis, a declared purpose, and a stopping condition. Check the [decision register](DECISIONS.md) before committing compute. A schema-independent engineering probe may proceed while official evaluation is unresolved; an official-score claim or schema-specific production training requires the corresponding authority.

Use one of these labels consistently:

| Label | Meaning |
| --- | --- |
| Engineering diagnostic | Synthetic checks, parsing, preprocessing, source inspection, export/load mechanics, or toy grading arithmetic |
| External-development proxy | Actual model comparison on explicitly permitted external data with its population and grading limits disclosed |
| Official-protocol local result | Permitted local evaluation with the confirmed official protocol/harness; still not a hidden-set score |

All results currently in the handoff are engineering or source-review evidence. The tools' use of the brief's formula does not make a score official.

## E00–E05 order

| Stage | Work | Gate to advance |
| --- | --- | --- |
| E00 | Resolve task/context fixtures; use B1 only as the pinned native-runtime fixture to load, run a small forward pass, export, and reload a non-quantized BF16/FP16 model | Pinned contract for score claims; verified native model path and measured resources. Passing this gate does not admit or select B1 as a competition base. |
| E01 | Prospectively freeze the eligible candidate universe and the [base-selection adaptation frontier](BASE_SELECTION_FRONTIER.md); run mechanical F0, freeze every F2 artifact/failure, then open the joint decision base and adapted arms together | Valid receipts, viability within actual hardware/budget, comparable base/adapted outputs, and a deterministic adaptation-response decision rather than a base-only ranking |
| E02 | Matched language-adapter pilots plus bounded visual-adaptation probes | Reviewed eligible data, actual trainable-module support, sound masks/loss normalization, measured exposure/cost |
| E03 | One evidence-motivated data or visual change against the retained baseline | Useful development evidence with source/task regressions investigated |
| E04 | Repeat promising recipe on another seed and scale modestly | Gain persists enough to justify cost; maintain a recoverable submission baseline |
| E05 | Select and freeze checkpoint/seed before opening confirmation; evaluate once; reproduce exported artifact | Honest confirmation result, fresh-environment reproduction, provenance, and release checks |

No current competition candidate order exists. B1's fixture role and any processor-probe ordering cannot select or
eliminate a competition base. Untouched base performance alone also cannot select a base because the challenge rewards
adapted performance and base-relative improvement. Run model comparison only after the prospective E01 candidate
universe, F0/joint-decision/F2 rule, matched conditions, and receipts are frozen. Do not eliminate a candidate solely
because it is slower to configure, has different format behavior under an unresolved contract, or uses a different
effective training exposure. After two unsuccessful attempts at an unchanged hypothesis, document what failed and
revise the mechanism before another attempt.

## Before a run

Record source/model/processor/protocol revisions; code and environment; seeds; exact population and independent groups; checkpoint identities; generation and grading policy; trainable modules; input presentation; sampling weights and realized exposures; practical-gain and task-regression thresholds; resampling plan; intended cost and finish time. Resolve source purposes and review status before model use. The baseline and adapted model receive matched processing and inference conditions.

Use the executable schema in [experiment records](../../outputs/mmbu-precompute/docs/experiment-records.md). The historical templates in `configs/` intentionally fail that schema because key decisions are unresolved; do not treat them as runnable configurations. The documented CLI supports validation, artifact receipts, and confirmation transitions, but does not launch training or grade predictions.

Freeze the actual artifact scope, including all intended checkpoint bundle members, data manifest, grading policy, and run configuration. Retain the receipt hash outside the mutable run directory. The checker can verify the declared files and their membership; it cannot prove that a checkpoint index describes an actual model or that an upstream revision is valid merely because it is a nonempty string.

## Keep inputs and partitions separate

Training, adaptive development, untouched confirmation, and permitted official development are distinct purposes. Group patients/studies/slides/acquisition batches and related image/figure derivatives before assigning splits; preserve source lineage and audit cross-source intersections. Do not invent independent groups when identifiers are absent.

Task inference receives only allowlisted task inputs. Context inference is a fresh pass with only the image and official requested-field prompt. Reference answers, source annotations, judge-only options, prior model outputs, and cross-pass conversation/cache state must stay out of inference. Package selector tests do not establish state isolation in a future model runner; test that integration separately.

Review labels and coordinate frames before use, including empty masks, borders, uint16 display mappings, and overlays. A declared percentage of record draws is not necessarily a percentage of target-token loss. Record unique images, independent groups, visual tokens, and supervised target tokens alongside draw weights.

## Compare and report

The brief's prospective score is `S = (0.8T + 0.2C) × (T − T_base)`. Context fields are averaged within each applicable
example, then across the evaluation population; zero-field behavior remains unresolved. The dated
[task-protocol snapshot](TASK_PROTOCOL_SNAPSHOT.md) pins the currently visible task suffixes and judge but also records
malformed-output and multi-label contradictions. Each candidate retains its own untouched base. Preserve raw outputs;
the local production policy fails malformed committed JSON and never repairs it. Do not label raw-reply fallback or
multi-label scoring official-equivalent until organizer precedence or an executable harness resolves those branches.

Report T, C, task gain, S, output validity, examples/groups/sources, source/task breakdowns, paired uncertainty, seeds, and actual GPU-hours/API charges/wall time/human review time separately. Use paired group resamples that retain base/adapted outputs together and the declared source mixture. A bootstrap interval over the development population is not a guarantee about the hidden leaderboard.

If a surrogate judge is needed, pin it and calibrate on a separate blinded sample that includes all contenders' base/adapted answers. Report randomly sampled disagreement separately from targeted model-disagreement cases. If grading uncertainty can change the decision, obtain adjudication or defer elimination rather than manufacturing certainty.

## Validation access and multiplicity

Before producing any untouched `recipe_confirmation` output, freeze the complete candidate universe, primary contrast
vector, endpoint hierarchy, practical margins, familywise confidence level, resampling method/seeds, failure treatment,
and deterministic decision function. Use the same paired independent-group/source resample indices across candidates
and endpoints. When more than one confirmatory contrast or safety endpoint can block/prompt promotion, use the frozen
simultaneous max-statistic bounds rather than pointwise intervals or a control selected after viewing results.

Open the `recipe_confirmation` population once. Mask candidate identities from the analysis step and emit the frozen decision
before unmasking descriptive results. Exploratory candidates/slices cannot rescue a failed confirmatory family. Any
post-opening change to candidate, checkpoint, prompt, margin, endpoint, exclusion, resampling, or decision logic retires
that population into development and requires a new independent population for another confirmation claim.

## Confirmation and release

Choose the primary checkpoint and seed using development only. Freeze the untouched confirmation cohort, exact comparison, thresholds, and a narrow mechanical-failure fallback rule before opening it. Keep the freeze hash and latest-ledger hash in a separate trusted record, as the [confirmation guide](../../outputs/mmbu-precompute/docs/experiment-records.md) requires.

Record a disappointing result unchanged. A subsequent model change informed by confirmation retires that set into development; a new independent set is needed for a new confirmation claim. Local receipts can detect drift against retained anchors but cannot stop a person from opening data elsewhere or rewriting every copy of an unanchored ledger.

Before submission, follow the fail-closed [release rehearsal](RELEASE_REHEARSAL.md): verify the confirmed single-model
rules, non-quantized BF16/FP16 export, vision/projector/adapters, processor/template/generation files, dependencies, raw
outputs, source disclosure, clean network-denied loading, form dry run, human approval, upload receipt, post-upload
revision, and rollback evidence. No such release or model validation is established by this CPU handoff.
