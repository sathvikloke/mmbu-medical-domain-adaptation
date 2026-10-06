# Synthetic causal-loss normalization

The CPU probe compares a combined batch with two microbatches containing unequal numbers of supervised assistant targets. Summing each microbatch's cross entropy and dividing by the **total valid target count for the accumulation window** reproduces the combined loss and gradients. Averaging the microbatch means weights this fixture incorrectly.

This is deterministic arithmetic over independent synthetic leaf logits. No model is instantiated, checkpoint loaded, model forward pass run, optimizer applied, GPU accessed or source example used. It verifies a loss-normalization principle for this fixture, not a production trainer or model-training behavior.

Run from the project root using the existing processor-probe environment; no additional dependency is needed:

```sh
work/processor-probe/.venv/bin/python \
  outputs/mmbu-precompute/tools/causal_loss_probe.py \
  --output work/processor-probe/causal-loss-reproduction.json
```

The output must be a new file in an existing directory. Existing files/symlinks are refused. The script exits 0 when all checks pass and 2 on failed checks, unavailable dependencies or output errors. The tested environment is Python 3.12.14, torch 2.14.1, CPU float64, one PyTorch thread. No random numbers are used.

## Fixture and objective

The fixed batch has three examples, right-padded to eight positions and a seven-token synthetic vocabulary. PAD is token 0, EOS is token 1, and ignored labels use -100. These IDs are fixture conventions; they do not prescribe a Qwen tokenizer or production EOS/newline policy.

| Example | Prompt tokens | Assistant targets including EOS | Right-padding positions | Microbatch |
| --- | ---: | ---: | ---: | --- |
| 0 | 2 | 3 | 3 | A |
| 1 | 4 | 2 | 2 | B |
| 2 | 2 | 5 | 1 | B |

For a causal objective, logit position `t` predicts label position `t+1`. The probe compares `logits[:, :-1, :]` with `labels[:, 1:]`. Prompt targets and right-padding targets are ignored; EOS targets remain included. This gives three valid targets in A, seven in B and ten in the combined batch.

If microbatch `j` has cross-entropy sum `s_j` and valid shifted target count `n_j`, the tested combined mean is:

```text
L = (s_A + s_B) / (n_A + n_B)
  = s_A / 10 + s_B / 10
```

The correct accumulation performs backward on each `s_j / 10`, accumulating into the same synthetic logit tensor. Its scalar/gradient result is compared with one combined-batch backward. The counterexample instead accumulates `(s_A/3 + s_B/7)/2`, which gives the two microbatches equal weight despite their unequal target counts. This is equivalent only in special cases; this fixture deliberately has different microbatch mean losses.

The probe independently recomputes each supervised term with standard-library scalar log-sum-exp, and each logit derivative as `(softmax - one_hot_target) / 10`. Thus it also checks the PyTorch calculation against a separate scalar and analytical implementation, rather than only comparing two uses of the same loss helper.

## Measured results

| Quantity | Executed value |
| --- | ---: |
| Microbatch A cross-entropy sum / target count | 5.559592892142769 / 3 |
| Microbatch B cross-entropy sum / target count | 17.02506497409063 / 7 |
| Combined mean loss | 2.2584657866233395 |
| Correct token-normalized accumulated loss | 2.2584657866233400 |
| Naive equal-microbatch-mean loss | 2.1426748849350300 |
| Correct accumulated versus combined loss absolute difference | 4.440892098500626e-16 |
| Correct accumulated versus combined maximum gradient difference | 0 |
| Naive versus combined loss absolute difference | 0.11579090168830941 |
| Naive versus combined maximum gradient difference | 0.05730282619049436 |
| Combined versus independent analytical maximum gradient difference | 1.3877787807814457e-17 |

The equality tolerance is absolute `1e-12`; the counterexample must differ by more than `1e-6` in both loss and gradients. All 15 checks passed. [causal-loss-probe.json](../evidence/causal-loss-probe.json) includes exact logits, token IDs, attention masks, labels, all four gradient arrays, environment, script hash and individual checks. [causal-loss-log.txt](../evidence/causal-loss-log.txt) records the command output. [causal-loss-verification.json](../evidence/causal-loss-verification.json) records exit 0 for the initial run and identical replay apart from timestamp, plus expected exit 2 for an existing output and for the bundled runtime without PyTorch. The existing report's bytes were preserved and missing-PyTorch execution wrote no report.

## Masking and causal boundaries

“Ignored prompt targets have zero loss gradient” refers to the shifted prediction sites, not every logit located within a prompt. The exact check is that `combined_gradient[:, :-1, :][labels[:, 1:] == -100]` is zero. The final sequence-position logits also have zero gradient because the shifted objective supplies no successor target there.

The **last prompt-position logit predicts the first assistant token** and therefore correctly receives nonzero gradient. The probe records these boundary locations explicitly: example 0 logit 1 predicts label 2, example 1 logit 3 predicts label 4, and example 2 logit 1 predicts label 2. EOS labels at positions 4, 5 and 6 are supervised at the preceding logit positions 3, 4 and 5 respectively, each with nonzero gradient. Right padding contributes neither target count nor gradient. An all-ignored shifted target set is explicitly rejected before dividing by zero.

These are derivatives with respect to independent logits only. In a real autoregressive model, a supervised assistant loss can backpropagate through prompt hidden states and model parameters. The probe does not test attention masks or claim that prompt representations are gradient-free.

## Practical limits

The result covers unweighted, unsmoothed cross entropy, the given causal shift and ignore mask, a fixed vocabulary, and a fixed CPU float64 fixture. It does not cover class weights, label smoothing, packed sequences, mixed precision, dropout, gradient scaling/clipping, distributed reduction, optimizer updates or trainer-specific accumulation conventions. A real accumulation window must count its actual valid shifted targets and account for its framework's own reductions. The toy denominator ten must never be copied into a real trainer.

Native chat-template alignment, actual assistant label construction, image presentation and model forward behavior remain separate checks. This probe does not connect the synthetic labels to a native model batch or make a training-readiness claim.
