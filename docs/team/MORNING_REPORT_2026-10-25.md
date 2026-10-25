# MMBU morning report — October 25, 2026

## Bottom line

The strategy and evaluator work passed. All five exact model revisions were acquired and the approved repaired F0 array reached terminal evidence: Qwen3-VL-8B, Qwen3-VL-2B, and InternVL3.5-2B passed every engineering gate; Qwen3.5-9B and Qwen3.5-4B failed closed because their frozen expected parameter counts did not match their native loaded model objects. No biomedical-quality conclusion was drawn.

## What passed

- **Track decision:** Track 3 remains the evidence-backed provisional primary. Track 2 remains a serious backup and possible second entry. Track 1 is inactive.
- **Evaluator:** the official-style context successor strictly parses one raw JSON object, scores only the requested subset of the six published context fields, separates validity from correctness, and rejects fences, duplicate keys, trailing material, unknown or missing keys, and non-string values.
- **Freeze:** five exact candidate IDs and revisions, one generated image, one prompt and target, matched LoRA/optimizer settings, comparison rules, one-attempt policy, and one-A100-hour ceiling are closed in a validated manifest.
- **Repository verification:** 465 tests passed before cluster launch, with two optional-dependency skips.
- **Evidence preservation:** failed jobs `85746` and `85751`, their receipts, and logs remain preserved in their separate run roots.
- **F0 passes:** three candidates completed one LoRA update, adapter save, fresh-process offline reload, deterministic prediction equality, and memory/runtime measurement without MMBU public or biomedical content.

## What failed or did not run

- All five model downloads in job `85746` failed under the home-backed GPFS quota.
- The one authorized clean scratch reacquisition, job `85751`, also failed under the account-level GPFS quota despite abundant cluster-wide free space.
- After cleanup, acquisition job `85823` passed for all five exact revisions.
- GPU array `85828` failed all five tasks with exit code `127` because `libpython3.12.so.1.0` was unavailable before the runner started.
- A failing regression test reproduced the missing module declaration; the repaired launcher now requires `module load python/3.12.12`, and the focused suite passes.
- Approved replacement array `85836` completed without retrying any task.
- Qwen3.5-9B and Qwen3.5-4B failed at the frozen parameter-count gate before GPU placement or adaptation. Config-only diagnostic reconstruction found `9,409,813,744` and `4,539,265,536` parameters respectively, rather than the frozen `9,653,104,368` and `4,659,865,088` values.
- These two failures do not establish model infeasibility; they establish that their identity contract requires correction before another bounded attempt.

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

The next action requiring approval is **an identity-contract amendment backed by the native post-tie counts, followed by one bounded F0 attempt for only Qwen3.5-9B and Qwen3.5-4B using the existing snapshots**. Do not rerun the three passing candidates.

After the shortlist has complete F0 evidence, the first decision-bearing experiment remains a matched unchanged-base versus adapted comparison on one frozen external-biomedical development population with three seeds. It is not authorized. No MMBU public-set evaluation, upload, submission, full training, or model selection occurred.
