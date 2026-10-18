# Package B synthetic implementation trace

**Observed:** October 18, 2026
**Scope:** authorized Package B synthetic CPU work only
**Verdict:** passed for the bounded synthetic slice described below

This receipt maps the Package B handoff clauses to implementation and negative-test evidence. It does not authorize or
claim model loading, biomedical/public data use, GPU work, training, evaluation, upload, or submission.

## File receipt

| Path | Bytes | SHA-256 | Role |
|---|---:|---|---|
| `src/mmbu_phase1/lattice.py` | 8,287 | `84ea1762c555f02b31e2b21abebf1f7b9ce01f9ece5469bfe3f2e0ae05d4dac1` | Synthetic deterministic lattice |
| `src/mmbu_phase1/exposure.py` | 9,827 | `89538a79418d7c183245f4696b82b2367284c7cbb2db86925a292becc56835fb` | Exact exposure and schedule audit |
| `src/mmbu_phase1/scope.py` | 16,763 | `5cd884caa73b0231235118bf05fc5ea0744f1c89dc6350b556c24ec799593ecc` | Fail-closed required-test inventory |
| `tests/phase1/test_package_b.py` | 12,561 | `37c786cddf5008de8a8c1b64b0ed9b63e286ade0b203c82f99793817009e0c0a` | Synthetic positive and negative fixtures |

## Contract trace

| Package B obligation | Implementation | Test evidence | Result |
|---|---|---|---|
| Mask to tight box under half-open original-pixel convention | `lattice.mask_to_tight_xywh` | `LatticeGeometryTests.test_mask_tight_box_uses_half_open_original_pixels` | Passed |
| Source box parse/serialize round trip without repair | `lattice.parse_source_box`, `serialize_source_box` | `LatticeGeometryTests.test_source_box_round_trips_without_normalization_or_repair` | Passed |
| Class plus box/mask, localization, and complete-count views | `lattice.derive_views` | `LatticeViewTests.test_class_box_mask_localization_and_count_views_share_lineage` | Passed |
| Ontology normalization, label round trip, and deterministic option ordering | `lattice.normalize_term`, `closed_options`, source-term gate in `derive_views` | `LatticeViewTests.test_open_closed_ontology_round_trip_and_seeded_permutation`; `test_incomplete_counts_label_invention_and_public_inputs_fail_closed` | Passed |
| Split-before-expansion, duplicate-edge, group-crossing, and lineage rejection | `lattice.validate_split_isolation` | `LatticeViewTests.test_split_before_expansion_rejects_group_and_lineage_crossing` | Passed |
| Public-source, incomplete-count, missing-lineage, and invented-label rejection | Closed synthetic-origin/unit validation in `derive_views` | `LatticeViewTests.test_incomplete_counts_label_invention_and_public_inputs_fail_closed` | Passed |
| Closed exposure manifest and exact unit/endpoint/view/token mass | `exposure.audit_rows` using `Fraction` | `ExposureAuditTests.test_annotation_density_context_fields_and_target_length_preserve_unit_mass`; `test_closed_manifest_and_endpoint_partition_fail_closed` | Passed |
| Global weighted numerator/denominator across microbatches/devices | `exposure.partial`, `combine_partials`, `weighted_loss` | `ExposureAuditTests.test_microbatch_and_distributed_aggregation_use_global_numerator_denominator` | Passed |
| Drop-last, invalid-view, and comparator-population equality | `exposure.compare_candidates` | `ExposureAuditTests.test_drop_last_invalid_view_and_candidate_population_drift_reject` | Passed |
| Schedule cycles, eligible early-stop boundaries, and exact resume prefix | `exposure.validate_schedules`, `eligible_stop_boundaries`, `resume_sequence` | `ExposureAuditTests.test_schedule_multisets_early_stop_and_resume_are_exact` | Passed |
| Package B tests cannot silently disappear from the root suite | `scope.REQUIRED_PHASE1_TEST_MODULES` | `Phase1PreflightTests.test_required_module_list_matches_the_scoped_suite` | Passed |

## Exact focused command and result

```text
PYTHONPATH=src python3 -m unittest tests.phase1.test_package_b -v
Ran 12 tests in 0.001s
OK
```

The implementation was also byte-compiled successfully and `git diff --check` passed before this receipt was written.
The repository-wide commands and their final counts are recorded separately in
[current clone verification](CURRENT_VERIFICATION.md).

## Deliberate limits

- The fixtures contain no biomedical or MMBU public examples; the only admitted origin literal is
  `synthetic_engineering`.
- This proves deterministic transformations and accounting behavior, not medical correctness, source admission,
  overlay-renderer safety, trainer integration, runtime floating-point tolerance, model quality, or competition score.
- The exposure implementation is the canonical one-unit-mass synthetic slice. A future prospectively balanced runtime
  with non-unit multipliers requires its own authorized implementation and evidence.
- Passing Package B does not raise any scientific result or execution-readiness claim for Packages C–I.
