# Measurement contract for the local arithmetic tools

The scoring functions require explicit binary judgments. They do not replace the organizer's semantic judge or decide whether malformed output receives zero or fallback grading. Grade production, format policy, example eligibility, and judge calibration must be settled upstream and versioned. Synthetic examples are arithmetic fixtures only.

For each example, average only its annotated context fields. Then average those per-example values over the same weighted example population used for task accuracy. Compute T, C and the base task accuracy first, then S=(0.8T+0.2C)(T−T_base). Negative adaptation is retained. Repeated-image rows remain rows; duplicate record IDs are errors. Rows with no annotated context fields are errors until official treatment is known.

Natural weighting gives every row equal mass. The balanced proxy gives each of four task groups equal mass, each source within a task equal mass, and each example within that source/task equal mass. Counting shares global classification's weight. The proxy refuses to manufacture a full-task ranking when a task group is absent. Source IDs must refer to genuinely distinct reviewed source units, not arbitrary shards of one dataset.

The library accepts explicit positive row weights and positive four-task weights. To perform the plan's sensitivity checks, call source_balanced_weights with each task at 0.4 and the other tasks at 0.2, then recompute the aggregates and product. These are hypothetical mixtures, not an inferred hidden distribution. Report all declared mixtures and preserve uncertain or reversed rankings. Do not choose the mixture that favors a desired winner.

The paired cluster bootstrap resamples groups with replacement independently within fixed sources. It carries base/adapted/context grades for each selected row together. Within each sampled source, original row weights are renormalized to preserve the original source mass. Task mass can vary within a source as groups are sampled; this is not a task-stratified bootstrap. This estimates conditional variability under that specified design, not source-transfer or training-seed uncertainty. Missing/untrustworthy patient/slide/batch IDs must be addressed before using it for scientific claims. Cross-source shared subjects require consolidation or a different resampling design; the scorer cannot infer them.

If any source has fewer than two groups, the tool withholds the interval instead of reporting false precision. Few groups/draws produce explicit warnings. The interval uses interpolated empirical percentile endpoints. No interval establishes a probability of winning, and a small positive development estimate does not account automatically for adaptive model selection.

Selecting a model among multiple candidates needs joint paired comparisons on the same resamples and a specified decision rule; the current helper computes an adaptation-score interval for one candidate. It must not be used to declare one candidate superior by comparing separate confidence intervals. The first pilot can use descriptive differences while the prospective practical-effect threshold, shared-candidate comparison and calibration are finalized.

Choose checkpoint and seed using development data. Record and freeze model/data/protocol/code hashes before opening confirmation. Retain the result even if disappointing. If its result informs changes, retire that set into development and acquire a new independent confirmation set before making another confirmation claim.

Judge calibration should include blinded base and adapted responses from every contender. Keep random audit samples separate from deliberately oversampled disagreement cases. Preserve human decisions and review uncertainty. The supplied CSV is a recording sheet, not a completed calibration or an automated adjudication.


Version 0.2 implements joint comparisons in `comparison.py` and the `compare` command; see `candidate-comparison.md`. The earlier single-candidate bootstrap remains available. Do not infer candidate superiority from comparing its separate intervals.
