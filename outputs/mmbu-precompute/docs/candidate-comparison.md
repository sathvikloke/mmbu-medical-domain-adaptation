# Joint candidate comparison from supplied grades

`mmbu_prep.comparison.compare_candidates` compares two or more named candidates on the same strictly aligned evaluation population. It computes each candidate's adaptation score and uses shared group-bootstrap draws to estimate a confidence interval for each **difference in adaptation scores**. It does not grade responses, choose a checkpoint, declare a winner, or estimate hidden leaderboard performance.

Every interval produced by this helper is labeled exploratory and unadjusted for multiplicity. A confirmatory interpretation requires separately predeclared comparisons, a justified multiplicity procedure, valid independent groups, and a frozen analysis population/protocol. Those conditions are not established by calling this function. The existing [measurement contract](statistics.md) also applies.

## API and input

```python
from mmbu_prep.comparison import compare_candidates

result = compare_candidates(
    candidates,          # mapping: candidate name -> list of pregraded rows
    weights=None,        # optional mapping: record_id -> positive finite weight
    iterations=1000,
    seed=0,
    confidence=0.95,
)
```

Candidate names must be nonblank strings, and there must be at least two candidates. Each row has the same required fields as `metrics.score_rows`:

```json
{
  "record_id": "example-001",
  "source_id": "reviewed-source",
  "group_id": "independent-patient-or-slide",
  "task": "global_classification",
  "base_correct": 0,
  "adapted_correct": 1,
  "context_correct": {"modality": 1, "body_part": 0}
}
```

Grades must already be available under an explicit grading policy. The helper reuses the score module's row validation, weight normalization, aggregate arithmetic and percentile calculation. It neither parses task answers nor supplies a semantic judgment or failure-credit policy.

All candidates must have exactly the same record-ID set. For each record ID, they must agree on `source_id`, `group_id`, `task`, and the exact set of annotated `context_correct` field names. Context grades can differ; annotation coverage cannot. Candidate records may arrive in different orders. Missing/extra IDs, duplicate IDs, mismatched metadata, missing grades, unsupported tasks/fields and zero-context-field rows raise `ValueError`. The function does not take an intersection, impute grades, discard failed predictions, or silently resolve inconsistent duplicate rows.

Each candidate supplies **its own** `base_correct` vector. Base grades need not equal those of another candidate, because their declared base checkpoints may differ. A duplicate record within a candidate is rejected even if only its baseline grade conflicts. The helper cannot detect a semantically mismatched baseline when there is just one apparently valid grade per ID.

The caller must bind each candidate's grade file to its experiment ledger, including base revision, adapted candidate revision, prompt/template version, data/record manifest, judge/grading policy version, and failure/exclusion policy. There is no required baseline-ID field in this API, and the helper cannot certify that these identities match the supplied grades. Agreement on record IDs and metadata also does not prove that questions, references, images or grades are correct; record provenance and review remain separate gates.

## Stable alignment and weighting

Candidate names and record IDs are sorted lexicographically. The first sorted candidate supplies the reference metadata after every candidate's rows have passed validation; other candidates must match it exactly. Sorting does not privilege that candidate's grades. Group/source traversal is also stable.

With `weights=None`, every aligned row has equal mass. Repeated rows from the same image/group retain their row mass; they are not deduplicated. With supplied weights, the mapping must name **every aligned record ID exactly once** and contain no extra IDs. Values must be positive finite numbers, with booleans rejected. They are normalized in the common sorted record order and applied identically to every candidate. Zero, negative, nonfinite, oversized unsupported integer and underflowing weight ranges are rejected using the shared metrics contract. Large finite equal weights such as `1e308` are supported through scaled normalization.

The result returns the sorted `record_ids` and `normalized_weights` map so the comparison population and weights are inspectable. Caller-provided row-array order and weight-map insertion order do not affect seeded results. Record/source/group/name strings are preserved exactly rather than normalized or merged.

To use a reviewed development-mixture proxy, compute weights with `source_balanced_weights` on the same aligned records, then key those weights by `record_id` before passing them here. This helper does not infer a hidden distribution or require that all four task groups are represented for an ordinary descriptive comparison. A full-task balanced proxy still requires all task groups through the score module's separate validation.

## Score differences and shared resampling

For each candidate, context grades are averaged within each example before weighted averaging across examples. Task accuracy `T`, context accuracy `C`, and base accuracy `T_base` use the same row weights. Its adaptation score is:

```text
S = (0.8*T + 0.2*C) * (T - T_base)
```

For every lexicographically ordered pair, the reported quantity is:

```text
delta_S = S_left - S_right
```

A positive difference means the left candidate has a larger supplied-grade adaptation score under the stated population and weights. It does not establish a superior general model, a common-baseline adaptation advantage, or statistical significance. Differences are not clipped to `[-1, 1]`: for example, one valid candidate can have `S=-0.3125` and another `S=1`, producing a difference of `-1.3125`.

Each bootstrap iteration samples the original number of independent groups with replacement **within each fixed source**. A selected group contributes all its rows, including repeated-image rows. The exact same sampled row-index sequence and weights are then used for every candidate and every candidate's own baseline/context grades. Scores are recomputed from aggregates on the draw, then subtracted. Pairwise intervals are percentiles of those jointly drawn differences; they are not formed by subtracting independently computed confidence-interval endpoints.

Original row weights are normalized within each sampled source while preserving that source's original total mass. Group sizes may differ. Task mixture can change within a source as groups are sampled; this is not a task-stratified or source-transfer bootstrap. Group IDs are scoped by source for resampling. If reviewed lineage spans multiple source IDs, consolidate the units or use another analysis design before treating intervals as scientific evidence.

If any source has fewer than two groups, every pairwise interval is `None`; point scores and descriptive differences remain available. Fewer than ten groups in any source and fewer than 200 bootstrap iterations produce warnings. These warning thresholds are engineering reminders, not guarantees of adequate coverage above the thresholds.

`iterations` must be a positive integer; `seed` an integer (booleans rejected); `confidence` a finite value strictly between zero and one. The implementation uses Python's standard-library pseudo-random generator. Preserve the Python version along with seed, code hash, population, weights and grading evidence for reproducibility; cross-version random-stream identity is not claimed.

## Returned structure

```text
label: "joint_comparison_over_supplied_grades_not_official_evaluation"
official_evaluation: false
inference: "exploratory_pairwise_comparison"
candidate_names: sorted list of names
record_ids: sorted list of aligned IDs
n_candidates, n_examples
weighting: "uniform" or "record_id_weights"
normalized_weights: {record_id: normalized weight}
candidates: {name: {T, C, T_base, task_gain, S}}
pairwise: [{left, right, delta_S, interval}, ...]
bootstrap: {
    confidence, iterations, seed, groups_per_source,
    interval_type: "unadjusted_percentile",
    multiplicity_adjusted: false,
    estimand: "pairwise_adaptation_score_difference_conditional_on_fixed_sources_and_supplied_grades"
}
warnings: list of explicit scope/precision limitations
```

The function returns fresh result containers and leaves candidate rows and supplied weights unchanged. It reports all `K*(K-1)/2` pairs for `K` named candidates in stable order. There is no `winner`, rank, p-value, significance flag or automatic checkpoint-selection field. It currently retains pairwise bootstrap samples internally until percentile calculation; very large candidate/draw counts require corresponding memory and are not a streaming computation.

## Engineering checks and remaining scientific work

The 20 comparison tests include independently calculated signed scores, a difference below `-1`, zero differences for identical candidates under shared draws, opposing correlated rows, fixed source mass with unequal group sizes, per-example metadata normalization, named weight alignment, ordering invariance, one-group interval withholding, and invalid coverage/grade/weight/configuration cases.

The opposing-group fixture has four rows per group. One candidate is correct on the first group and the other on the second. Shared whole-group draws produce differences of `-1`, `0` or `1`; the test checks interval endpoints without pretending the toy fixture is a scientific coverage study. Identical candidates yield exactly `[0, 0]` for their difference, which would generally fail if candidate resampling were independent.

Run from the package root:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests -p test_comparison.py -v
```

[comparison-red.txt](../evidence/comparison-red.txt) preserves the initial 20 expected failures before the module existed. [comparison-green.txt](../evidence/comparison-green.txt) records 20 passing tests, the interpreter and exit code after implementation. These are software-engineering results over synthetic grade fixtures. Python 3.14.7 was exercised; the module uses standard-library features available in Python 3.11+.

Still required before scientific or checkpoint-selection claims: authoritative evaluation/grading policy, consistent blinded judge calibration across contenders, reviewed independent groups, documented baseline/candidate identity, frozen candidate/comparison hypotheses, a justified multiplicity/selection rule, prospective practical-effect thresholds, and an untouched confirmation procedure. No task-output judge, native model inference, biomedical data review, GPU run or final export is completed by this helper.
