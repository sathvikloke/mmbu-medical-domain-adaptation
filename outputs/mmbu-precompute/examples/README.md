# Engineering fixtures only

Five 16×16 PGM images contain procedurally drawn rectangles. They test paths, hashes, geometry and manifest handling; they contain no biomedical observations. The task tags exercise schema categories, not task competence. Box/mask classification fixture images are not complete organizer overlays or valid medical questions. No conversion should promote this source to training.

`pregraded-toy.jsonl` contains twenty manually constructed grade rows. Source A has adapted/context accuracy 0.9 and base accuracy 0.8; source B has adapted/context accuracy 0.3 and base accuracy 0.0. With equal source sizes, pooled T=C=0.6 and base T=0.4 give S=0.12. There are no actual model predictions or human judgments behind these rows. Their task/group assignments exist only to exercise the software.

The real 200–500-example biomedical engineering cohort is not yet built. It requires reviewed source eligibility, a pinned acquisition and conversion recipe, usable annotations and human review. These five fixtures must never be counted toward it.


`candidate-grades-toy.json` repeats the existing invented grade rows under two distinct toy names, reversing their input order. Its paired difference and interval must be zero. These are synthetic arithmetic fixtures, never predictions or a model ranking.
