# Development diagnostics and judge calibration

`diagnose_candidates` accepts the same named, fully aligned pregraded candidates as `compare_candidates`. It reports natural-mixture paired scores; a balanced proxy only if all four broad task groups are present; and four prospective stress mixtures giving one task group weight0.4 and each other group0.2. Within a task, sources have equal mass and examples within a source/task have equal mass. Counting is combined with global classification for these weights, but retains its own descriptive task breakdown.

The supplied population is never intersected or reduced to make candidates align. Missing task coverage is reported explicitly; partial coverage produces only natural-mixture and descriptive subgroup diagnostics. Source and task tables use natural example averages within their named subset. Pairwise bootstrap intervals share groups across candidates, preserve source mass, and remain conditional on the chosen sources and supplied grades. The mixtures are development assumptions, not estimates of the hidden evaluation distribution.

A point-rank reversal is flagged whenever the same candidate pair's score difference changes sign across the predefined mixtures. A zero or broad interval does not become a winner claim. There is no multiplicity adjustment, hidden-set estimate, automatic promotion, or model selection. This makes the task-mixture sensitivity proposed in the audited research plan executable.

```sh
PYTHONPATH=src python3 -m mmbu_prep diagnose examples/candidate-grades-toy.json --bootstrap 1000 --seed 17
PYTHONPATH=src python3 -m mmbu_prep calibrate /path/to/calibration-grades.jsonl
```

Calibration rows require unique `case_id`, `stratum`, `sampling` (`random` or `targeted_disagreement`), and explicit integer `human_grade`/`judge_grade` in0/1. Missing decisions cannot silently vanish. The report gives confusion counts, agreement, sensitivity, specificity and predictive values separately by sampling frame and stratum; undefined denominators are null. Deliberately oversampled model-disagreement cases never contribute to a pooled population accuracy. No statistical interval is manufactured from unknown clustering or sampling design.

The caller must establish how cases were sampled, whether review was blinded, who provided human grades, how disagreements were adjudicated, and whether the selected reference is medically correct. These functions cannot certify those facts. High agreement alone does not validate a semantic judge or show that candidate rankings are stable. The shipped toy grades remain software fixtures, never model results.
