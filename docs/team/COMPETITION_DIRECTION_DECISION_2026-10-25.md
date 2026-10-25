# Competition direction decision

**Decision date:** October 25, 2026

**Status:** binding design review; no additional model training is authorized by this memo

**Decision:** pursue **Track 2, Medical Domain Adaptation**, replace the Qwen-only assumption with a four-model
adaptation-response bake-off, and reject the Lane 1 context proxy as model-selection evidence.

## Plain-language answer

The project should not be discarded, but it does need a sharp reset. Its strongest idea is not a new learning
algorithm. It is a disciplined attempt to make a medical VLM improve over its own unchanged base while retaining real
visual dependence, producing valid machine-readable outputs, and recognizing the biomedical setting in a separate
pass. That is unusually well aligned with Track 2. The project can become competitive only through a replicated
base-relative improvement; more governance prose or a more complicated adapter cannot substitute for that result.

The completed Lane 1 shakedown proved that the training, save, offline reload, and prediction-reproduction path works on
real biomedical inputs. It did **not** select a recipe or a base model. In particular, the reported zero context score
was caused by a defective local proxy and is not evidence that all five arms lacked biomedical-context ability.

## Verified facts versus unknowns

### Verified

- The official Track 2 score is
  `S = (0.8T + 0.2C) * (T - T_base)`. A candidate must both finish strong and improve task accuracy over its disclosed
  base. A context gain cannot rescue a nonpositive task gain.
- The official context pass asks for applicable fields drawn from modality, submodality, specimen, body part, stain,
  and medical domain, using visual evidence only and returning machine-readable JSON with a concise rationale.
- The submission must be one end-to-end autoregressive VLM. Retrieval, tools, auxiliary inference models, repeated
  sampling, test-time adaptation, and weight modification during evaluation are prohibited.
- Models below 27B must be publicly downloadable from Hugging Face without gating or access restrictions.
- The five Lane 1 arms all completed, saved, reloaded offline, and reproduced predictions. Adapted arms executed 128
  optimizer updates. No MMBU public content was used.
- On the 64-row, one-seed answer proxy, language-LoRA task-only was descriptively highest at 53.125%, versus 43.75%
  for the unchanged base. Every BUS-BRA task result was tied, so the apparent gain came only from 32 PathMNIST rows.
  This is too small and narrow to promote anything.
- The current repositories for Qwen2.5-VL-7B, Qwen3-VL-8B, InternVL3.5-8B-HF, and OctoMed-8B are public, ungated,
  below 27B, and expose downloadable BF16 safetensors. Exact observed revisions are frozen below.

### Unknown or unresolved

- Which base produces the best **adapted** Track 2 result under one common recipe.
- Whether any gain survives three seeds, patient/source grouping, a second modality, and a held-out source family.
- The final organizer runtime, resource ceiling, loader command, dependency set, and submission-tree schema.
- Whether ordinary adapters may be submitted separately or must be merged into a complete checkpoint.
- Whether all shortlisted architectures can train, export, and reload under one frozen local runtime without custom
  unapproved code. This is an F0 gate, not an assumption.
- A sufficiently broad, legally reviewed data portfolio. BUS-BRA and PathMNIST were sufficient for a wiring shakedown,
  not for broad MMBU transfer or a decision-bearing model comparison.
- Clinical benefit. This is a benchmark adaptation project, not a clinical validation study; patient-impact claims
  remain out of scope unless clinicians and a real workflow endpoint are added later.

## Why the all-zero context result is invalid for model selection

The shakedown did not implement the official context task. It asked BUS-BRA models for `bbox_xywh`, `birads`,
`image_size`, and `side`. The official challenge instead scores applicable biomedical metadata fields in a separate
pass. A box, BI-RADS label, source image dimensions, and laterality are not substitutes for that contract.

Three independent defects forced or distorted the zero:

1. **Impossible coordinate-frame request.** The model saw a processor-resized image but was required to reproduce the
   original source pixel dimensions using only the displayed image. No arm matched `image_size` on any of 32 context
   rows.
2. **All-or-nothing scorer.** An image-size mismatch returned zero before BI-RADS, side, or IoU could receive partial
   credit. This erased useful differences.
3. **Parser mismatch.** Arms 0, 1, and 3 emitted valid JSON inside Markdown fences on all 32 rows, but the strict parser
   rejected every fenced payload. Arms 2 and 4 emitted raw JSON. Output-format robustness matters, but it must not be
   confused with biomedical recognition.

After stripping only outer fences for diagnosis, every arm had all expected keys. Arms 2 and 4 also showed the best
partial biomedical/geometry signal: respectively 13 and 14 exact BI-RADS predictions, 14 and 7 exact side predictions,
and mean box IoU 0.225 and 0.306. These are diagnostic counts only; they do not repair the invalid proxy or make an arm
eligible.

**Binding consequence:** preserve the zero scores as historical results, but prohibit their use for model, recipe,
objective-weight, or checkpoint selection. The next comparison must use a dynamically requested subset of the official
metadata fields, source-authoritative labels, `unknown` where visual determination is not defensible, and strict raw
JSON validity reported separately from field correctness. Geometry belongs in task scoring when the task asks for it;
it does not belong in the official context proxy.

## Track decision

### Track 2 is the primary track

Track 2 matches what the team can actually contribute: adaptation of a disclosed open base. Its score directly rewards
replicated value added over that base. It also permits starting from a medically adapted checkpoint, although an
already-medical base may leave less measurable headroom.

### Why not Track 1

Track 1 uses `0.8T + 0.2C` directly and is attractive if the team owns or can submit a very strong frontier model.
However, its rule says the model must be pretrained, mid-trained, and post-trained by the same organization. Our plan
starts from third-party open weights and adds our post-training, which is at best an eligibility ambiguity and at worst
directly incompatible. An unchanged model built entirely by another organization would contribute little of our own
work and would not test the project hypothesis. Track 1 is therefore a fallback only after written organizer
clarification; it must not divert Track 2 compute.

### Scoring implication

For fixed adapted `T` and `C`, a lower `T_base` raises the Track 2 score. That does **not** mean a deliberately weak base
is optimal: the adapted ceiling depends on the base, and a low-quality base lowers the first factor through the final
`T`. Base selection must therefore measure the response to one common adaptation recipe. It may not rank untouched
bases, choose by name recognition, or cripple a base to manufacture delta.

## Ranked base-model shortlist

The ranking is a priority for a fair bake-off, not a winner declaration.

| Rank | Candidate and frozen observed revision | Why it belongs | Main risk | Disposition |
|---:|---|---|---|---|
| 1 | `Qwen/Qwen3-VL-8B-Instruct` @ `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b` | Current 8B general VLM, Apache-2.0, ungated, native Transformers path, strong likely final ceiling | A strong base may leave less Track 2 delta; its training/export path is untested here | Primary candidate, subject to F0 |
| 2 | `OpenGVLab/InternVL3_5-8B-HF` @ `741a7d03020411e666c6109218ab71e08151ef86` | Independent architecture family, Apache-2.0, ungated, standard HF-format checkpoint; protects against Qwen-family bias | Custom-code/processor behavior and adapter targeting may complicate reproducibility | Required family-diverse challenger |
| 3 | `Qwen/Qwen2.5-VL-7B-Instruct` @ `cc594898137f460bfe9f0759e9844b3ce807cfb5` | Only candidate with proven local load, LoRA/projector step, save, and offline reload; mature control | Older and potentially lower final ceiling; prior investment must not grant it a scoring advantage | Engineering control, not incumbent winner |
| 4 | `OctoMed/OctoMed-8B` @ `f5d8be54bd5170bf3824782a6f39f4dafe525d83` | Ungated Apache-2.0 medical Qwen3-VL checkpoint; tests whether a medical starting point raises the final ceiling | Already medically adapted, multiple-choice focused, long think traces, likely reduced delta and JSON risk | Diagnostic medical-start control; promote only on measured response |

`google/medgemma-4b-it` and `google/gemma-3-12b-it` are excluded from this bake-off because Hugging Face access is
gated, while the challenge requires sub-27B models to be downloadable without gating. InternVL3.5-4B and other small
models receive no Track 2 size bonus, so they are not included unless an 8B candidate fails the resource gate.

Official model-card evidence used for this screen:

- https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct
- https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct
- https://huggingface.co/OpenGVLab/InternVL3_5-8B-HF
- https://huggingface.co/OctoMed/OctoMed-8B
- https://huggingface.co/google/medgemma-4b-it

## Fair bake-off protocol

No candidate receives candidate-specific data, prompts, learning-rate search, update count, seed count, or rescue run.
Architecture-native preprocessing and module names may differ, but their functional scope, input images, supervision,
unit mass, optimizer-update exposure, decision population, and resource ceilings must be matched and disclosed.

### Gate D — data and metric freeze (zero GPU hours)

Before any comparative output exists:

1. Admit, version, and hash a minimum competition portfolio consisting of BUS-BRA plus two independently governed
   semantic-breadth families. PathMNIST/NCT-CRC is the first non-ultrasound candidate; BUS-UCLM is the preferred
   independent ultrasound replication family. If BUS-UCLM's license conflict or PathMNIST parent grouping cannot be
   resolved, replace the failed source rather than silently weakening the gate.
2. Freeze patient/study/slide grouping, source roles, train/development partitions, and one unopened source-family
   confirmation population. Collapse all views from one parent to one unit of exposure.
3. Cover at least two modality classes and both global-recognition and localization/grounded task forms. Report macro
   source and macro task results; no large source may dominate.
4. Build context targets only from source-authoritative applicable values for the official field vocabulary. Never
   infer metadata from dataset names, file paths, prompt wording, or a source's reputation. Use `unknown` where visual
   evidence or annotation authority is insufficient.
5. Freeze two local metrics before outputs: `T_proxy`, source/task-balanced task correctness; and `C_proxy`, the
   within-example mean of requested authoritative official metadata fields. Track malformed JSON separately and score
   the affected pass zero. Report the Track 2 proxy, raw `T`, raw `C`, and delta separately.
6. Freeze one simple adaptation profile: language LoRA over the same functional attention/MLP scope, rank 8, alpha 16,
   dropout 0, BF16, singleton accumulation, unit-normalized 3:1 task/context mass where context is applicable, full task
   mass otherwise. The initial learning rate is `1e-4`; it may be changed only by a global pre-output amendment applied
   to every candidate.

If Gate D cannot be completed, stop. Another two-source shakedown may debug code but cannot select a base or raise
competition readiness.

### Gate F0 — loader and package feasibility (maximum 4 A100-hours)

Run one isolated A100 job per candidate, each capped at one hour:

- fetch and hash the exact frozen revision into a candidate-specific cache;
- reload with network disabled;
- run the same synthetic image/text forward and backward pass;
- complete one optimizer step on the frozen LoRA scope;
- save the minimal artifact, start a fresh process, reload offline, and reproduce deterministic logits/predictions;
- record peak memory, visual-token count, trainable tensors, dependency versions, loader flags, artifact size, and any
  custom-code requirement.

Any gated download, license conflict, model-identity drift, OOM, unsupported training path, missing gradients, export
failure, or offline-reload mismatch eliminates the candidate. There is no candidate-specific repair beyond one
demonstrated implementation bug applied consistently where relevant.

### Gate S1 — common adaptation-response screen (maximum 28 A100-hours)

- Use exactly 2,048 parent-normalized training units and 512 frozen development units, balanced by source and task.
- Evaluate one unchanged deterministic base per candidate, then train the fixed profile with seeds `20261025`,
  `20261026`, and `20261027`.
- Cap each adapted job at two A100-hours and each unchanged-base evaluation at 30 minutes. Use up to four concurrent
  A100s, one candidate/seed per job.
- Open all base/adapted development outputs together only after every eligible job has sealed its artifact digest.
- Require valid task and context JSON rates of at least 99.5%, exact offline reload, no non-finite updates, and no
  source/task slice regression worse than 3 percentage points.
- A candidate survives only if task gain is positive in all three seeds, mean task gain is at least 1.5 points, and the
  paired parent-bootstrap 95% lower bound on task gain is above zero. Context is reported and must not fall by more than
  1 point, but it cannot compensate for a failed task gate.

If no candidate survives, stop at approximately 32 total A100-hours including F0. Do not add an exotic adapter.
Reconsider data breadth, target validity, or the entire Track 2 approach.

### Gate S2 — top-two confirmation (maximum 48 additional A100-hours)

- Advance at most two candidates using the deterministic ordering: strongest simultaneous lower bound on positive task
  gain and final composite; then worst-source/task performance; then lower measured resource use; then simpler loader.
- Train each on 8,192 parent-normalized units with the same three seeds, capped at 7.5 A100-hours per adapted job;
  reserve the remaining three A100-hours for the two unchanged-base evaluations on the new cohort.
- Evaluate on a new frozen development cohort not used in S1. Do not tune on the unopened source-family confirmation.
- Require the S1 promotion gates again, plus no rank reversal under macro-source versus natural-mixture weighting, no
  material loss under image-removal/answer-changing visual controls, and reproducible fresh-process export/reload.

Total pre-confirmation ceiling is **80 A100-hours**: 4 for F0, 28 for S1, and 48 for S2. Based on the completed
128-unit shakedown (roughly 5–7 minutes per adapted arm), this is deliberately conservative; F0 measurements replace
the estimate before S1. With four usable GPUs, the nominal wall-clock target is about 20–30 hours, but queue time and
architecture-specific visual tokenization remain unknown.

### One-time held-out confirmation and packaging

Only after a single candidate and recipe are frozen may the unopened source family be evaluated once for the unchanged
base and the selected adapted model. A failure does not promote the runner-up on the reused holdout. The final artifact
must then pass a network-denied load, both official-shaped passes, strict JSON parsing, deterministic save/reload,
dependency reconstruction, and an offline submission-tree rehearsal. No MMBU public result may alter the model,
recipe, prompt, checkpoint, or stop rule.

## Failure risks and explicit responses

| Risk | Response |
|---|---|
| No positive base-relative task gain | Stop Track 2 scale-up; do not hide the result with context gains or complexity |
| Gain confined to PathMNIST or one source | Reject promotion; require positive grouped uncertainty and source/task floors |
| Official-style context labels unavailable | Mask the field or source; never invent it; if coverage is inadequate, make context a reported uncertainty rather than a fake proxy |
| Strong base leaves little delta | Keep it only if final composite and robust delta jointly dominate; otherwise a lower-base candidate may win fairly |
| Weak base shows large delta but poor final performance | Reject through the final-composite and worst-slice ordering |
| JSON/thinking/fence failures | Train exact terminal raw JSON; report validity separately; malformed official output receives zero |
| Processor/image-budget inequality | Freeze each native processor and common source image bytes, record visual tokens and measured cost, and enforce the same A100-hour ceiling |
| Architecture-specific troubleshooting bias | One common repair budget; preserve failures; no private hyperparameter search |
| Data portfolio remains ultrasound/pathology-heavy | Do not claim broad MMBU readiness; add an admitted independent modality before confirmation or stop |
| Optional novelty branches consume schedule | Quarantine MOSAIC, QUILT, specialist encoders, preservation losses, and interpolation until S2 yields a credible simple baseline |

## Honest project assessment after this review

- **Competition alignment:** 9/10. The chosen track and decision objective match the official score.
- **Engineering execution:** 8/10. Real biomedical load/train/save/reload now works, but only in a tiny shakedown.
- **Empirical competition evidence:** 3/10. One seed and 64 development rows are informative debugging evidence, not a
  transferable result.
- **Data breadth/readiness:** 4/10. Two sources ran, but the minimum decision-bearing portfolio and held-out family are
  not yet closed.
- **Learner novelty:** 2/10. Shared LoRA and task/context co-training are established methods; do not market them as a
  new algorithm.
- **System/research contribution potential:** 6/10 if the controlled multi-family comparison reveals when adaptation
  helps or harms visual grounding; lower if it remains only infrastructure.
- **Current win readiness:** approximately **56/100**, up from the earlier 48/100 because the project now has a real
  end-to-end biomedical shakedown and exact failure evidence. A replicated positive S2 result plus held-out-family and
  package success could move it into the 75–85 range. No honest analysis can promise 95–100 before those results exist.

## Immediate stopping point

Do **not** launch another large job now. The next work is finite and CPU/read-only where possible:

1. repair the official-context target/scorer design and supersede the obsolete context uncertainty in current docs;
2. close Gate D's third-family admission and field-coverage table;
3. implement architecture-neutral F0 manifests for the four exact revisions; and
4. review the frozen packet once, then spend at most four A100-hours on F0.

The project should be judged next by whether it can pass those gates, not by another idea score or another long audit.
