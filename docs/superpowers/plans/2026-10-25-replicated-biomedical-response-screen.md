# Replicated biomedical response screen implementation plan

**Spec:** `docs/superpowers/specs/2026-10-25-replicated-biomedical-response-screen-design.md`

## Global constraints

- Preserve all historical evidence and write every empirical artifact to a fresh run root.
- Never access MMBU public examples, confirmation splits, networks during GPU execution, uploads, or submission systems.
- Execute only the fourteen frozen conditions, once each, with at most five concurrent GPUs.
- Use test-first implementation and fail closed on any identity, population, output, or reload mismatch.

## File structure

- `src/mmbu_phase1/replicated_response.py`: closed manifest validation, condition expansion, official-context row transformation, matched-population checks, and aggregate descriptive calculations.
- `config/phase1/replicated-response-screen-2026-10-25.json`: frozen candidates, conditions, seeds, data sizes, hyperparameters, thresholds, and prohibitions.
- `tools/replicated_response_screen.py`: one-condition native training/evaluation/export driver with terminal receipts.
- `tools/replicated_response_reload.py`: fresh-process offline replay of one condition.
- `tools/replicated_response_screen.sbatch`: bounded fourteen-condition, five-concurrent-A100 launcher.
- `tools/prepare_replicated_response_portfolio.py`: rebuild a new official-context portfolio from the two pinned archives.
- `tests/phase1/test_replicated_response.py`: manifest, population, context, launcher, failure, and aggregation coverage.
- `docs/team/REPLICATED_RESPONSE_SCREEN_2026-10-25.md`: execution trace written only after terminal evidence exists.

## Task 1: Freeze and validate the screen

**Interfaces:** `load_manifest(path) -> dict`, `condition_by_index(manifest, index) -> dict`, and `official_context_row(row) -> dict` in `replicated_response.py`.

1. Write tests that reject altered candidates/revisions, seed lists, profile set, data sizes, confirmation access, retry expansion, public content, and unknown fields.
2. Run the focused test and confirm it fails because the module/config do not exist.
3. Implement the closed manifest, fourteen-condition expansion, and source-specific official-context transformation.
4. Run the focused test and require all Task 1 tests to pass.
5. Commit the freeze and validators.

## Task 2: Implement one-condition native execution

**Interfaces:** the driver consumes the Task 1 manifest/condition and writes one canonical terminal `result.json`; the reload driver consumes its adapter and reproduces predictions.

1. Write tests for one-shot output roots, fixed population selection independent of training seed, generic native loader use, exact LoRA target scope, base/adapted optimizer counts, failure receipt closure, and explicit offline fresh reload.
2. Run the focused test and confirm the new execution tests fail.
3. Implement the driver and reload path by reusing the proven F0 native loader/encoder and Lane 1 image store/scoring primitives without changing historical runners.
4. Require raw predictions, exact metrics, adapter inventory, selected-ID digests, update count, runtime/memory, and false public-content use in every passing receipt.
5. Run the focused tests and commit.

## Task 3: Add source rebuild and bounded scheduler envelope

**Interfaces:** the preparation tool emits a new compiled portfolio with successor context fields; the Slurm script maps one array index to one condition.

1. Write tests for exact source paths, new-output-only behavior, fourteen tasks, `%5` concurrency, one A100, four-hour cap, offline flags, and no nested submission.
2. Run the focused test and confirm failure.
3. Implement the preparation tool and Slurm envelope.
4. Run focused tests, the Phase 1 suite, link verification, and diff verification.
5. Commit.

## Task 4: Execute and aggregate

1. Stage the clean commit to a fresh MOCS scratch run root and verify free quota, archive checksums, snapshots, manifest digest, and no existing output directories.
2. Run the CPU portfolio rebuild once; verify byte/hash closure and fixed train/development populations before GPU launch.
3. Submit the fourteen-condition array with at most five concurrent A100 jobs and one attempt per condition.
4. Monitor without retrying. Preserve every failure.
5. After termination, validate every receipt and run the frozen aggregate calculation.
6. Write `docs/team/REPLICATED_RESPONSE_SCREEN_2026-10-25.md`, run focused/full verification, and commit the evidence.

## Review focus

- training seed must never change selected rows or their order;
- base and adapted conditions must load the exact same snapshot per model;
- no target token may leak into prompt-only generation;
- fresh reload must compare all raw prediction strings, not only aggregate metrics;
- PathMNIST's unavailable parent-patient grouping and both sources' incomplete human admission must remain explicit blockers;
- no aggregate may emit a promotion or official Track 3 multiplier.
