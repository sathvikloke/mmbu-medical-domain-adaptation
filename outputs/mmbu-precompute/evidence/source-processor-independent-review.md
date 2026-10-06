# Pending-source processor report independent review

Verdict: PASS within the CPU input-encoding and engineering-summary scope for `source-processor-final-v2.json`. This is neither model execution nor permission to train, evaluate or release these pending records.

The reviewer read `tools/source_processor_probe.py`, its processor-only artifact/encoding helpers, and the task-input selector. Only the caller's synthetic system prompt and current question enter the rendered text; the actual hash-checked PNG supplies image content. The selector excludes answers, options, captions, article IDs, source provenance, history and previous predictions. Poisoning these excluded fields with structured sentinel values left each native prompt unchanged in the independent replay. File bytes are verified against inspection before decoding the same immutable buffer; PNG dimensions and RGB mode are reconfirmed. Cached artifacts are pinned, verified, loaded with local-files-only and remote code disabled. No model class is instantiated.

The independent driver checked all 24 actual PNG raw hashes and independently rebuilt all 24 versioned decoded-pixel digests. It checked all 144 report records (24 images × three candidates × two policies), native grid-derived visual-token counts, input lengths, identity links, prompt hashes and CPU/finite/determinism receipts. All 18 summaries were independently recomputed using exact rational type-7 quantile positions; totals, extrema, means and percentiles agree within floating-point representation tolerance. These statistics describe this selected sample only.

Six fresh direct processor calls—one actual image for each candidate and policy—reproduced every saved tensor's shape, dtype and byte SHA-256. This replay bypassed the report's `encode_case` wrapper. Qwen3.5's native generation prompt retains its default `<think>` prefix; this report observes input encoding and makes no assistant-supervision alignment claim. The separate supervision review covers that boundary.

The root reviewer had identified exponent overflow in strict JSON and length limits applied after unbounded reads. The initial exponent-overflow acceptance and original code hash are preserved in `source-processor-independent-initial.json`. Final independent probes reject duplicate keys, nonfinite constants and positive/negative exponent overflow. Four observed-stream fixtures confirm a single `limit + 1` read and inclusive acceptance at the limit. All five stated network entry points were deliberately exercised and rejected before connection; the subsequent native replay attempted zero network calls. The fresh native probes ran on CPU without model weights, forward passes or gradients.

Evidence: `source-processor-independent-probes.json` records seven passing groups and six replay results; the local driver `work/roco-upstream-rights/review_source_processor.py` returned exit code 0. The author's ten focused safeguard tests were also run independently; their command, output and exit code are recorded in `source-processor-independent-tests.json`. Production code and source data were not modified by this review. Smaller visual-token counts do not establish retained biomedical information, lower GPU memory, faster throughput, model fitness or a model ranking.

The first unit-test runner accidentally resolved the virtual-environment interpreter symlink to its base interpreter, which lacks Torch; three dependency errors from that invocation are preserved in `source-processor-independent-tests-initial.json`. The corrected invocation uses the virtual-environment executable path. This was a review-runner error, not a production defect. A separate preliminary driver invocation correctly stopped at its code-hash freshness check while the author's final report was still being regenerated; no stale result was accepted.

Final SHA-256 values:

- Reviewed report: `b7ece4644d4da1639877400de815cbc4f8c3e934cb2e54b187a039d17e14914e`
- Source processor script: `6aa20bb459d7993115c98fd8a2cd3d37adc74b9cbba759242dcdc30505db33dd`
- Pending manifest: `fa6e591fea3b1cec61c87e0eef87959028c88afb4f6904c144c5bee666fed327`
- Independent driver: `24e2c23a4f63ae977304e4632b0edcebff566df94545fe723f5101f4471dc107`
