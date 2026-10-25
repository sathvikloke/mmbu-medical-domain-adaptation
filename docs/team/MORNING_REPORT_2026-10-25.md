# MMBU morning report — October 25, 2026

## Bottom line

The strategy and evaluator work passed. After storage cleanup, all five exact model revisions downloaded successfully. The first GPU F0 array then failed before Python initialization because its Slurm launcher omitted the required MOCS Python module load. No model loaded and no scientific conclusion was drawn.

## What passed

- **Track decision:** Track 3 remains the evidence-backed provisional primary. Track 2 remains a serious backup and possible second entry. Track 1 is inactive.
- **Evaluator:** the official-style context successor strictly parses one raw JSON object, scores only the requested subset of the six published context fields, separates validity from correctness, and rejects fences, duplicate keys, trailing material, unknown or missing keys, and non-string values.
- **Freeze:** five exact candidate IDs and revisions, one generated image, one prompt and target, matched LoRA/optimizer settings, comparison rules, one-attempt policy, and one-A100-hour ceiling are closed in a validated manifest.
- **Repository verification:** 465 tests passed before cluster launch, with two optional-dependency skips.
- **Evidence preservation:** failed jobs `85746` and `85751`, their receipts, and logs remain preserved in their separate run roots.

## What failed or did not run

- All five model downloads in job `85746` failed under the home-backed GPFS quota.
- The one authorized clean scratch reacquisition, job `85751`, also failed under the account-level GPFS quota despite abundant cluster-wide free space.
- After cleanup, acquisition job `85823` passed for all five exact revisions.
- GPU array `85828` failed all five tasks with exit code `127` because `libpython3.12.so.1.0` was unavailable before the runner started.
- No model was loaded. No forward pass, backward pass, LoRA update, save, offline reload, deterministic prediction check, GPU memory measurement, or model-runtime measurement occurred.
- A failing regression test reproduced the missing module declaration; the repaired launcher now requires `module load python/3.12.12`, and the focused suite passes.

## Track decision and uncertainty

**Primary:** Track 3, provisionally, because its score does not depend on a fragile base-relative improvement term and the size exponent is modest.

**Backup:** Track 2, seriously, because medium models may provide a higher final-quality ceiling if adaptation produces replicated positive base-relative gains.

The following organizer questions remain unresolved and must not be guessed:

1. Whether this registration covers both Tracks 2 and 3 or requires an update.
2. Whether separately trained checkpoints from the same public base may enter both tracks.
3. Whether one team may win more than one track.
4. Whether a designated checkpoint may be replaced before the deadline and whether validation attempts are limited.
5. The exact Track 3 `P` and `Pmax` treatment for the 4,659,865,088-parameter Qwen3.5-4B checkpoint.
6. Whether the organizer's Qwen3.5-4B acceptance is a named exception or a general nominal-4B rule.
7. How an already medically adapted Track 2 starting checkpoint must be disclosed and loaded.

## Required next approval

The exact snapshots are now present and revision-verified. The next action requiring approval is **one replacement F0 launch using the repaired Slurm environment, without reacquiring models or changing any frozen scientific setting**. Until that approval is given, do not relaunch, load models, train, evaluate, upload, submit, or select a winner.

The later decision-bearing experiment remains a matched unchanged-base versus adapted comparison on one frozen external-biomedical development population with three seeds. It is not authorized and should not be launched before F0 produces valid memory/runtime and reload evidence.
