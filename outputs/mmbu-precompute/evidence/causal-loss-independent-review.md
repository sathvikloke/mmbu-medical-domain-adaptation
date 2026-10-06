# Independent review of the synthetic causal-loss probe

**No actionable defect found within the probe's stated arithmetic scope.** The experiment-records reviewer did not author `tools/causal_loss_probe.py`. The reviewed script SHA-256 was `1ac6ac8c23896a6190042ab2b6a200322bfc1b8f0fd35c5f9c7e0b6a3937a365`.

On October 4, 2026, the reviewer replayed the probe to a temporary JSON report using the existing `work/processor-probe/.venv` environment. It exited **0**, passed **15** checks and reproduced the saved report apart from its timestamp. No dependency install, model, GPU or network access was used.

Independent enumeration confirmed 10 shifted supervised targets, split 3/7 across microbatches. A separate standard-library negative-log-softmax calculation from saved raw logits reproduced the combined mean loss. Central finite differences at epsilon `1e-6` reproduced the reported first-assistant and EOS logit gradients to absolute error below `1.7e-10`; ignored-next-target and final-unused-logit gradients were zero. The last prompt logit correctly predicts the first assistant target, and the logit preceding EOS receives its supervised gradient.

The [coverage audit](cpu-coverage-audit.md#independent-synthetic-loss-probe-check) retains the numeric results and five finite-difference sites without duplicating the raw report here. Correct accumulation divides both microbatch sums by the shared 10-target denominator; naive equal averaging of unequal microbatch means differs as expected.

This verifies a deterministic example of shift, label masking, cross-entropy reduction and gradients with respect to logits. It does not validate any model's parameter gradients, training framework, distributed reduction, mixed precision, optimizer, GPU configuration or model quality. The probe documentation preserves those limits.
