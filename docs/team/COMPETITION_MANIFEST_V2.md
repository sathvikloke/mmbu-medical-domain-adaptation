# Competition manifest version 2

**Status:** additive synthetic design contract; no execution authority
**Implementation:** `src/mmbu_phase1/competition_manifest_v2.py`
**Schema:** `mmbu.competition.manifest`, version `2`

## Why version 2 exists

Version 1 requires exactly one row for each of B0, B1-L, B2-P, and B2-F. That shape cannot represent matched task-only and dual-objective controls on the same architecture. Version 2 makes the candidate universe a variable-cardinality set of architecture/objective-profile pairs while preserving the existing authority, firewall, model, data, training, promotion, release, research-registry, state, unknown-value, and digest gates.

The v1 implementation and semantics are unchanged. The v1 validator rejects v2 records, the v2 validator rejects v1 records, and their canonical digests differ because the schema version and v2 family fields are digest-bound. A v1 receipt cannot authenticate v2 bytes.

## Objective-family field

Every v2 objective profile adds:

```text
matched_objective_family_id: nonempty string
```

Within one family, at most one profile may be task-only (`context_unit_share == 0`) and at most one may be dual (both task and context shares are positive). A dual profile requires a task-only profile in the same family. This turns “task-only versus task+context” into an explicit matched comparison rather than an informal label.

B0 has a null objective profile. Every adapted candidate resolves one declared profile. Candidate IDs remain architecture-qualified, and each `(architecture_id, objective_profile_id)` pair is unique.

## Canonical candidate order

Rows use the fixed architecture order B0, B1-L, B2-P, B2-F. B0 appears exactly once and first. Within an adapted architecture, task-only rows precede dual rows; profile IDs are then UTF-8 sorted. This ordering permits multiple profiles without allowing semantically identical records to acquire different bytes through row permutation.

## Five-arm causal graph

The first intended experiment has exactly these enabled arms and comparators:

| Candidate | Exact required comparators | Question isolated |
| --- | --- | --- |
| B0 | none | Unchanged base reference |
| B1-L task-only | B0 | Effect of language-side adaptation |
| B1-L dual | B0; B1-L task-only | Incremental effect of the context objective at B1-L |
| B2-P task-only | B0; B1-L task-only | Incremental projector contribution under task-only training |
| B2-P dual | B0; B1-L dual; B2-P task-only | Projector contribution under dual training and the within-B2-P context-objective effect |

The comparator map must equal the mechanically derived graph. A missing edge, an extra edge, a disabled candidate, a cross-family task control, or a skipped architecture rung rejects the manifest. Exact equality prevents a post hoc “useful comparison” from silently changing the multiplicity family or the claim.

## B2-F extension

B2-F may be present only as disabled in version 2. The inherited validator requires `enablement_rule=pre_output_f0_gate`, but v2 does not represent the receipt needed to prove that gate passed. A future schema revision must add that receipt and then extend the same rules one rung:

- B2-F task-only requires B0 and the identical B2-P task-only profile;
- B2-F dual requires B0, the identical B2-P dual profile, and the same-family B2-F task-only profile.

An absent immediate control rejects the higher architecture. The validator does not treat B0 as a substitute for a missing B1-L or B2-P control.

## What validation proves

Passing v2 validation proves only that the synthetic design record is closed, deterministically serialized, and contains the controls required for the stated causal comparisons. It does not authorize data acquisition, biomedical inspection, model loading, GPU use, training, evaluation, upload, or submission. It also does not prove learner novelty, biomedical validity, model improvement, compute feasibility, official-harness equivalence, or private-set generalization.

Scientific values—sources, ranks, modules, loss shares, schedules, seeds, budgets, thresholds, and promotion margins—remain unknown until separately chosen through the repository's prospective decision and authorization controls.
