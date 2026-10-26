# BUSI-WHU confirmation readiness

**Date:** October 25, 2026  
**Current status:** protocol mechanics implemented; authority-backed record resolution and real execution blocked  
**Evidence level:** CPU-only synthetic conformance, not biomedical or model-performance evidence

## What is ready

The repository now contains a prospectively frozen Track 2 confirmation protocol for the fixed Qwen3.5-9B dual-objective family on BUSI-WHU v3. The package provides:

- an exact protocol identity covering the model revision, three training seeds, LoRA recipe, prompts, parser, patient floor, resampling rule, decision margin, and one-attempt policy;
- a fail-closed checkpoint-lineage validator that rejects the old exploratory adapters, incomplete training-source purposes, a missing Qwen3.5 successor runtime gate, and any MMBU public-content use;
- exact patient-balanced task, context, `Q`, class, bootstrap, and sign-randomization calculations using reduced rational arithmetic;
- a non-rescuable primary decision requiring every seed delta, the family point estimate, and the one-sided lower bound to clear the frozen rule;
- a reference checker that reports the first missing gate in a fixed order, but intentionally stays blocked even when every field contains a digest because digest syntax is not proof that a real validated record exists;
- 60-patient positive, underpowered, and exact-threshold synthetic fixtures that are permanently barred from promotion and readiness claims.

The command is intentionally narrow:

```sh
python3 tools/busi_whu_confirmation.py validate-spec \
  --spec config/phase1/busi-whu-confirmation-spec-2026-10-25.json
```

Its other modes check a reference manifest or validate a synthetic fixture. The reference mode cannot authorize execution until it is connected to an authority-backed record resolver. The command has no acquisition, network, scheduler, model, training, GPU, or upload path.

## What remains blocked

No real confirmation run is authorized or ready. These records still need to exist and validate:

1. BUS-BRA and PathMNIST admission for the `train` purpose, including exact split manifests and record-level lineage.
2. A reviewed Qwen3.5-9B successor runtime gate covering native load, one real training path, save, fresh offline reload, and equality.
3. Three new checkpoints trained after source admission. The October 25 exploratory adapters cannot be reused.
4. BUSI-WHU v3 acquisition authorization and immutable archive checksums.
5. Rights review for acquisition, confirmation use, challenge use, disclosure, and trained-weight release.
6. Protected inventory and the complete image-to-patient and image-to-label joins.
7. An eligible-population manifest with at least 60 independent patients. Fewer patients produce an `underpowered` exploratory outcome, not a replacement-source search.
8. A QA plan derived only after inventory closes, followed by a separate QA lock and opening.
9. Exact and perceptual cross-source duplicate review.
10. Confirmation-purpose authorization, population lock, hermetic decision receipt, resampling artifacts, execution lock, and opening receipt.

Any missing item keeps the package blocked. Synthetic values or prose cannot substitute for a record.

## Scientific boundary

This work improves the honesty and reproducibility of the next experiment. It does not raise the project's measured novelty, competition readiness, or biomedical performance score. The development evidence still supports Qwen3.5-9B as the Track 2 confirmation candidate, while Track 3 remains the administrative provisional route until the organizer resolves the size rule.

The next larger action needs a separate user decision: begin the real admission sequence for the two training sources and BUSI-WHU. No data acquisition, model loading, HPC work, or training follows automatically from this package.
