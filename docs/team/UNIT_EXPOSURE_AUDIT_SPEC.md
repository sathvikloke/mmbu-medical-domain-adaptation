# Independent-unit exposure audit specification

**Date:** October 17, 2026  
**Status:** synthetic implementation work order; no data/model result  
**Purpose:** prevent annotation density, target length, batching, or schedule order from changing the intended objective

## Estimand

An independent biomedical unit—not a derived view, object, field, or target token—is the primary exposure unit. Before
prospective source/task/context balancing, every eligible unit has one canonical rational total mass. If a unit has
several endpoints or views, their weights partition that mass; they do not create more mass.

For unit `u`, endpoint `e`, view `v`, and supervised token `t`:

```text
sum_e endpoint_share[u,e] = 1
sum_v view_share[u,e,v] = endpoint_share[u,e]
sum_t token_share[u,e,v,t] = view_share[u,e,v]
```

Every equality is checked in canonical rational arithmetic before conversion to runtime dtype. The runtime receipt also
reports the floating-point realized totals and a registered tolerance. Under the local proxy, a zero-applicable-context
unit prospectively reallocates its context share to the task endpoint before the view rows are built; this explicit
profile rule is not a loader default. The official successor replaces it if the organizer specifies another policy.

## Required manifest inputs

Each eligible unit/view row binds:

```text
independent_unit_id
split_group_id
source_family_id
endpoint_id
task_form
requested_context_fields
view_id
supervised_token_count
unit_total_mass
base_unit_mass
prospective_balance_multiplier
effective_unit_mass
endpoint_share
view_share
token_normalization_id
schedule_position_or_epoch_rule
```

The audit consumes the frozen view manifest, objective profile, batch/accumulation plan, sampler seed, maximum updates,
drop-last policy, and invalid-record policy. It rejects missing rows, duplicate view IDs, mutable epoch lengths,
unreceipted filtering, or a sampler whose exact exposure cannot be reconstructed.

## Runtime aggregation rule

Compute a weighted sum of token losses and divide by the sum of the corresponding declared token weights over the
entire effective optimizer step. Do not average microbatch means, view means, field means, or device-local means with
equal weight when their denominators differ. Gradient accumulation and distributed reduction must preserve the global
weighted numerator and denominator. Empty-target microbatches reject before backward; they do not contribute zero.

If the trainer API cannot represent weighted numerator/denominator aggregation exactly, the candidate is not
implementation-ready. Changing the objective to fit the trainer is a successor design, not a harmless implementation
detail.

## Synthetic traps that must pass

1. **Annotation-density trap:** one global-label unit emits one view; one complete mask unit emits class, grounded,
   localization, and count views. Their total mass remains equal.
2. **Context-field-count trap:** one unit has one requested field and another has six. Their context endpoint mass is
   equal under the registered field-normalization rule.
3. **Target-length trap:** a one-token label and a long coordinate/rationale target retain the declared view mass.
4. **Microbatch trap:** unequal token counts across two accumulated microbatches match a single concatenated-batch
   reference gradient.
5. **Distributed trap:** asymmetric device-local denominators reproduce the single-process weighted reference.
6. **Drop-last trap:** the final partial batch cannot disappear unless the frozen sampler accounts for the missing
   unit mass identically across candidates.
7. **Invalid-view trap:** rejection of one derived view cannot transfer its mass post hoc or leave candidates with
   different unit populations.
8. **Schedule trap:** static, forward, reverse, and shuffled schedules contain the identical multiset of units, views,
   target UTF-8 bytes, and effective weights over every complete cycle; only order differs. Model-specific token counts
   are reported rather than required to be equal across tokenizers.
9. **Early-stop trap:** only complete-cycle boundaries with identical cumulative multisets and effective mass are
   eligible for schedule comparison or stopping; prefix checkpoints cannot win because easy views arrived first.
10. **Resume trap:** interrupted/resumed execution reproduces the same remaining sampler sequence and cumulative mass.

## Required report

Emit canonical and realized totals by unit, source family, endpoint, task form, context field, annotation-density bin,
epoch, optimizer step, and candidate. Report:

- minimum, maximum, median, and maximum absolute unit-mass deviation;
- endpoint and field coverage, including zero-applicable context units;
- supervised-token and optimizer-step counts;
- cumulative exposure curves for schedule comparisons;
- dropped/rejected rows with immutable reasons; and
- equality checks against every comparator's declared exposure contract.

The pre-training gate requires maximum canonical deviation from each prospectively balanced effective mass exactly zero
and realized/effective per-unit deviation at most 1%.
Comparator exposure mismatch is blocking even when total wall time or number of steps happens to match.

## Claim boundary

Passing this audit proves only that the intended objective reached the optimizer with the declared exposure. It does not
prove label correctness, medical validity, model improvement, source independence, or official-score alignment.
