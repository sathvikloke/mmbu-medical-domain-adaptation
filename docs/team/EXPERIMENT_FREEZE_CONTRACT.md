# Experiment-freeze contract

**Date:** October 18, 2026  
**Status:** binding design gate; no experiment is frozen or authorized  
**Purpose:** separate schema engineering from scientific choice and prevent an implementer from inventing missing values

## Three distinct readiness states

1. `schema_ready`: versioned schemas, cross-field validators, and synthetic negative fixtures exist. Placeholder or
   unknown scientific values are allowed only in a deliberately non-runnable fixture.
2. `experiment_freeze_ready`: every value below is literal, authority-backed where required, hash-bound, and fixed
   before model or biomedical outputs. No `unknown`, placeholder, adjective, or environment-derived default remains.
3. `execution_authorized`: the frozen manifest also has the separate account/allocation, data-purpose, model/cache,
   and run authorization required for that exact stage.

Passing `schema_ready` never implies the other two states. Claude may implement and test schemas, but may not select
scientific values or convert a non-runnable fixture into a frozen experiment.

## Namespace rule

Identifiers are qualified everywhere they could collide:

- model/runtime fixture: `model_slot::B1`;
- competition architectures: `recipe_arch::B0`, `recipe_arch::B1-L`, `recipe_arch::B2-P`, and
  `recipe_arch::B2-F`;
- workflow stages: `workflow_stage::E00` through `workflow_stage::E05`; and
- frontier stages: `frontier_stage::F0`, `frontier_stage::joint_decision_base_arm`, and `frontier_stage::F2`.

An unqualified `B1`, `B2`, `F1`, or `validation` in an executable record rejects.

## Packet closure and canonical identity

Before a Claude work package is executable, one `handoff_dependency_manifest` lists every normative dependency with
relative path, byte count, lowercase SHA-256, media type, and role. Missing, extra, path-aliased, or hash-mismatched
dependencies yield only `packet_incomplete`; they authorize no schema, code, command plan, or experiment change.

The manifest cannot authenticate itself. Launch additionally requires a separately supplied
`handoff_launch_receipt` that binds the manifest's relative path and expected canonical SHA-256, names the approving
authority and permitted package scope, and has status `approved`. A receipt stored beside the packet is an operational
pointer, not a cryptographic trust anchor, unless its expected digest was acknowledged through an independent trusted
channel. The verifier must receive that trusted-channel acknowledgement digest independently at launch and match it to
the receipt; a digest found only inside the repository never authorizes itself. Approval is package-scoped to unique
members of A–I, and authorization is computed for the specifically requested package. Missing, unmatched,
out-of-scope, or `pending_human_digest_acknowledgement` status yields
`packet_unanchored`; read-only review may continue, but no schema, code, command plan, or execution is authorized.

Executable records are validated closed objects and serialized as RFC 8785 JSON. Numeric scientific scalars are
integers or reduced rational objects `{ "numerator": int, "denominator": positive_int }`; runtime measurements may use
finite decimals only where their schema permits them. Lists are ordered unless the schema explicitly declares a
sorted-set field. A record's SHA-256 is computed over the canonical object with its own digest field omitted. Every
referenced ID resolves through an artifact registry to path, SHA-256, and media type. YAML snippets are explanatory,
not canonical bytes.

## Scientific-decision receipt

`experiment_freeze_ready` requires one pre-output `scientific_decision_receipt_id` binding all of:

```yaml
candidate_profiles: []
frontier_candidates_and_revisions: []
training_budget:
  max_optimizer_steps: literal
  max_gpu_hours: literal
  max_wall_hours: literal
  max_failed_jobs: literal
  max_retained_checkpoints: literal
optimizer: {name: literal, lr_by_parameter_group: {}, betas: [], eps: literal, weight_decay: literal}
schedule: {name: literal, warmup_steps: literal, clipping_norm: literal, accumulation_steps: literal}
seed_set: []
objective_profiles: []
preservation: {population_digest: literal, coefficient: literal, temperature: literal, direction: literal, token_mask: literal}
checkpoint_rule: {frequency_steps: literal, statistic: literal, patience_or_grid: literal, tie_rule: literal}
optional_branches_enabled: []
```

The receipt also binds exact module maps, ranks, alpha/dropout, balance multipliers, rationale/output profiles, and
every decision-function literal. Values may be chosen only by the named scientific owner under the prospective design;
Claude may check completeness and consistency but may not choose them. Revised hypotheses consume the same frozen
global compute budget; they do not replenish it.

`recipe_arch::B2-F` is disabled by default. It may be enabled only at `frontier_stage::F0`, before biomedical outputs,
by a frozen synthetic workload digest, literal peak-memory headroom, literal wall-time cap, and zero OOMs over a bound
number of runs. Its Boolean enablement and profile digest then become immutable.

## Data roles and one opening

The manifest names disjoint group/source roles explicitly:

```text
frontier_train
frontier_tuning
frontier_decision
recipe_train
recipe_development
recipe_confirmation
visual_probe_construction
visual_probe_audit
```

A closed role-disjointness matrix binds patient/study/slide/specimen/source-parent/duplicate and prompt-lineage rules.
`frontier_decision` may not alias recipe development or confirmation. Source-held-out claims require at least one
admitted training source family and one independently grouped held-out source family; any stronger macro-source
inference binds its own minimum support. Insufficient support returns `experiment_freeze_blocked`, never a silently
dropped endpoint.

Development chooses one `promotion_candidate_id` and freezes one checkpoint for it and every member of its declared
comparator closure. Those exact artifacts are opened together once on `recipe_confirmation`. Only the named promotion
candidate may be promoted. Failure returns `no_eligible_candidate`; no runner-up is tried on that population. B0 may
be a release fallback only if the rules permit it and it independently passes all mechanical/release gates. Any adapted
fallback requires a new untouched confirmation population.

## Context-missing policy

For the local proxy, requested context fields are the intersection of the bound proxy registry and source-authoritative
targets. A missing or ambiguous source target is not asked, serialized, scored, or assigned loss; no `unknown` sentinel
is invented. A unit with zero eligible context fields uses
`zero_applicable_training_policy = reallocate_context_share_to_task` and
`zero_applicable_evaluation_policy = exclude_and_report`. This preserves one total unit mass without treating absence
as a context label. The official successor contract must replace these proxy rules when the organizer publishes its
unknown and zero-field behavior.

## Exposure equivalence

Each unit records `base_unit_mass`, the prospectively frozen source/task/context `balance_multiplier`, and
`effective_unit_mass`. The exact pre-runtime audit verifies canonical mass; the realized tolerance applies to
`realized_mass / effective_unit_mass`, not to equality after intentional balancing.

Across different tokenizers, the primary frontier match is identical independent-unit/view IDs, target UTF-8 bytes,
and optimizer-step count. Model-specific token counts are reported covariates, not an impossible equality constraint;
a separately frozen compute-matched analysis is secondary. Curriculum schedules may be compared or early-stopped only
at complete-cycle boundaries where the full declared multiset and effective mass are identical. Prefix checkpoints are
ineligible.

## Decision function

The promotion and frontier decision function is a versioned, executable closed object, not prose. It binds:

```text
estimand and aggregation formulas; T/B/C range and score-proxy formula
primary contrast and positive task-gain floor
familywise alpha, bootstrap replicate count, seeds, and resample hierarchy
practical-gain and endpoint-specific nonregression margins
minimum support and missing-stratum rule
visual-probe statistics, directions, margins, and simultaneous family
invalid-output credit, nonfinite rule, candidate order, and tie sequence
```

For `T,B,C` on `[0,1]`, candidates with `T-B <=` the frozen positive-gain floor are ineligible. If authoritative
context is unavailable, compute the registered score interval over the frozen admissible `C` range and require robust
dominance; otherwise return `no_selection`. The Boolean decision is the conjunction produced by the exact function;
words such as “material,” “sufficient,” or “promising” have no executable effect.

Negative flips report both
`NFR_all = count(base_correct and adapted_wrong) / N` and
`NFR_cond = count(base_correct and adapted_wrong) / count(base_correct)`, plus positive flips and invalid outputs. The
decision object names which measure and margin enter the gate.

Every task-by-source visual-probe registry row is `required` or `inapplicable` with evidence, unit IDs, construction
digest, statistic, direction, threshold, minimum support, bootstrap family, and failure result. Missing minimum support
on a promotion-critical row yields `unresolved`, never a vacuous pass.

## Output and geometry closure

Training and inference bind separate byte-level `training_target_format_id` and `inference_output_format_id`. The latter
defines whether rationale prefix text is allowed, terminal-object extraction, duplicate objects, whitespace, trailing
text, and failure precedence. Answer-only training under a rationale-requesting inference prompt is an explicit
robustness mismatch, not protocol equivalence.

Geometry binds zero-based origin, pixel-edge and source-box inclusivity conventions, conversion equations, rounding
point/mode, clipping-versus-rejection policy, empty/multiple-box ordering, numeric serialization, and round-trip
tolerance through golden input/output bytes. `original-pixel xywh` alone is not a complete geometry contract.

## Resource and release closure

The first native MOCS preflight requires a separate `mocs_run_authorization` with scheduler, partition,
account/allocation, GPU count/type, CPU, RAM, wall time, storage, and cache roots. It is capped at `max_jobs = 1` and
`max_retries = 0`. Without that object, package D may emit only a parameterized
`not_copyable_not_authorized` template, never a runnable command or `passed` result.

An adapter-only release either contains every pinned base byte required for offline loading or relies on an official
loader-provided, hash-bound base cache. A mere remote base reference cannot pass an empty-cache network-denied load.
Remote verification stages exact downloaded bytes in quarantine, verifies inventory hashes, copies them to a fresh
cache, disables network, and only then loads and smokes. Deterministic reload compares exact token IDs and raw bytes in
two independent clean processes using the same frozen generation seed; any permitted nondeterminism requires a named
field-level tolerance fixed before output.

## Package/workflow crosswalk

| Workflow | Handoff packages |
|---|---|
| pre-`workflow_stage::E00` | A/B/F/G schema review plus H metadata-only design |
| `workflow_stage::E00` | C compatibility map and D native preflight only when separately authorized |
| `workflow_stage::E01` | G base-frontier execution |
| `workflow_stage::E02`–`E04` | F within-base execution |
| `workflow_stage::E05` | one-opening confirmation and release rehearsal |
| diagnostic only | E, never on the critical competition path |

No row in this crosswalk supplies missing authority or turns a design artifact into execution permission.
