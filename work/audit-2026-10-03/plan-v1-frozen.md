# MMBU domain adaptation competition plan

Prepared October 3, 2026. Target: a first-place-caliber entry in Medical Domain Adaptation. This is an experiment and delivery plan; no model has been trained or evaluated by us yet.

**Recommendation:** spend the first two weeks establishing trustworthy measurements and comparing small adaptation runs, then concentrate on one base model and one coherent training recipe. Our proposed advantage is better biomedical visual supervision, including localization and unfamiliar imaging modalities, with targeted adaptation of the vision components. It is a hypothesis to test, not an established result.

**Planning assumptions:** GPU access, budget, team capacity, and access to the private Discord/dev release are unconfirmed. The default plan assumes 2–3 contributors, roughly 25–40 combined hours per week, and access to an 80 GB GPU for the main experiments. These are resource requests, not facts about the team. Smaller-compute alternatives appear below.

**Deadline:** the acceptance email states December 31, 2026, end of day Anywhere on Earth. This corresponds to January 1, 2027, 12:00 UTC / 06:00 America/Chicago. Set our internal final-upload deadline to **December 28, 17:00 Chicago time**, with a submission-ready checkpoint by December 20. The email is the source for the challenge deadline; confirm the eventual submission portal's exact cutoff.

**What winning requires**

The official objective is:

`S = (0.8 × T + 0.2 × C) × (T − T_base)`

The brief explicitly identifies adapted answer accuracy with T. C is the average of each image's mean score over its annotated metadata fields. Base and adapted models are evaluated under identical conditions. These details matter: metadata gains alone cannot create a positive score without task improvement. [Official brief, pages 6–9](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf)

Illustrative arithmetic, not predicted performance:

| Candidate | Base T | Adapted T | Adapted C | Adaptation score |
|---|---:|---:|---:|---:|
| A | 0.30 | 0.50 | 0.60 | 0.104 |
| B | 0.50 | 0.60 | 0.70 | 0.062 |

A stronger final model can lose if its adaptation adds little. Conversely, choosing a weak base is useful only if it can learn enough to reach a strong final result. Evaluate the real starting checkpoint fairly; preserve its revision, processor, native chat template, and outputs. Do not manufacture a low baseline.

For a fixed base, the score's sensitivity to task performance is `1.6T + 0.2C − 0.8T_base`; its sensitivity to context is `0.2(T − T_base)`. This motivates task-first investment while keeping a meaningful metadata training component. Training proportions need an experiment; they do not follow directly from the scoring weights.

**Three strategic options**

| Approach | Benefit | Limitation | Decision |
|---|---|---|---|
| Generic medical Q&A with language LoRA | Fast, useful control | May improve terminology without improving image perception | Build as the baseline |
| Diverse visual supervision plus vision/projector adaptation | Directly targets recognition, region understanding, localization, and context | Requires careful labels, image processing, and broader validation | Main research program |
| Large model plus extensive reinforcement learning | More capacity and potential to improve answer selection | Higher cost, slower iteration, more runtime risk | Optional after the main recipe works |

MMBU reports weak localization and inconsistent transfer from established medical benchmarks. That supports testing a perception-focused recipe, but does not prove it will win. [MMBU paper](https://arxiv.org/html/2606.06696v1)

**Model decision: choose by October 16**

My earlier Qwen2.5 recommendation was provisional. It should enter a controlled comparison rather than become a commitment for the whole competition.

| Candidate | Role | What would justify selecting it |
|---|---|---|
| [Qwen/Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) | Initial engineering baseline; direct connection to earlier biomedical adaptation work | Best validated adaptation score after our pilot |
| [Qwen/Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) | Comparable-size alternative with different visual architecture | Better adaptation results or substantially better robustness |
| [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | Newer multimodal candidate | Better score within the allowed output/runtime conditions |

Run untouched baselines first, then one short SFT run on the same training manifest for each feasible candidate. Match data exposure and evaluation conditions; record tokens, GPU-hours, and peak memory because architectures differ. Before rejecting a close contender, allow a bounded learning-rate check so a poorly chosen training setting does not decide the competition.

Evaluate [OctoMed-7B](https://huggingface.co/OctoMed/OctoMed-7B) as an optional medical reference if resources permit. If we ever initialize from it, disclose that actual initialization and obtain organizer guidance on the base used for scoring. Do not claim its inherited medical adaptation as work we added.

With substantial compute, one larger-model scouting run using [Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) is reasonable after the small-model recipe shows gains. Count the entire VLM: the model card's language-model count does not establish eligibility under a threshold that includes vision and projection parameters. Resolve hosting and evaluation requirements before investing in this route.

After October 16, keep one active base and one recorded fallback. Reopen base selection only for a compatibility blocker or a credible gain large enough to justify repeating validation. Avoid spending November comparing a growing list of checkpoints.

**First 72 hours: October 3–6**

- [ ] Designate an evaluation/model owner, a data owner, and a review/release owner. One person can own multiple roles; write down the actual names.
- [ ] Join the organizers' Discord through the actual invitation in the original email. Collect pinned rules, office-hour information, the official dev release, and harness links. The pasted message does not contain the Discord URL.
- [ ] Send the organizer questions at the end of this document. This plan includes a draft; no message has been sent.
- [ ] Confirm GPU access and storage, the team's maximum spend, and weekly availability. Do not treat sponsor software accounts as a GPU allocation.
- [ ] Activate the team's Paperclip offer when ready for an intensive month. Check for the separate Claude selection/activation email; acceptance alone does not establish that this team received one of the 80 accounts. Use both only for challenge work, as the email requires.
- [ ] Establish a private experiment repository and a team-accessible artifact store. Keep private challenge analysis within the registered team.
- [ ] Build the data manifest and validation split policy before downloading large collections.
- [ ] Load the first base and run a small external-data smoke evaluation through the official harness if available. If unavailable, test only local model loading, JSON parsing, and geometry; label the provisional evaluator accordingly.

The October 7 GXL workshop is worth attending or watching. The email says 9 a.m. PST: October 7 normally observes PDT in California, so verify the Discord event time. It would be 11 a.m. Chicago if they mean Pacific local time, or noon if they mean literal UTC−8.

**Evaluation is the first deliverable**

Use three distinct sets:

| Set | Purpose | Separation rule |
|---|---|---|
| External training data | Optimization and training-only error mining | Documented sources and permitted splits |
| External development validation | Routine model and recipe decisions | Group by patient/study/slide/experiment; keep related images together |
| External locked validation | Confirmation of a short finalist list | Hold out entire sources where possible; no iterative tuning against it |

Treat the official development set according to explicit organizer guidance. The brief allows local evaluation but uses broad wording against selecting checkpoints with MMBU evaluation examples. Until clarified, use external validation for selection and keep official-dev use to the explicitly permitted evaluation scope. Keep all official dev examples and derivatives out of training under our default policy.

Build an initial external validation set of approximately 1,500–3,000 examples if suitable independent data can be obtained. Cover all four tasks and several imaging families; do not inflate sample size with correlated patches from a few slides. Establish a separate locked set large enough to represent those families. Size follows available independent sources and review capacity, not a quota that justifies weak labels.

The dashboard must report:

- T, C, T minus the same base's T, and S, with raw predictions retained.
- Task scores for whole-image classification, box-grounded classification, mask-grounded classification, and detection.
- Context scores by requested field, and results by modality and source.
- JSON validity, answer omissions, refusals, truncations, invalid boxes, peak memory, and runtime.
- A source-balanced robustness view alongside the overall sample mean. The former is diagnostic; it is not the official metric.

Use paired bootstrap resampling that respects patient/slide/source groups. Recompute base and adapted scores on the same resampled groups, including the nonlinear product S. Report uncertainty for the difference between candidate recipes. A confidence interval spanning zero is inconclusive; do not portray it as proof of equivalence. Repeated experimentation still creates selection bias, which is why the locked set and fresh training seeds matter.

Do not plan around repeated hidden-leaderboard feedback: the brief says hidden scores arrive after submissions close. Public-dev performance is a proxy, not a forecast of our rank. Use source-held-out validation and sensitivity checks across task/modality mixtures to reduce dependence on the particular data available locally. No current evidence establishes a numerical score that would win.

If the official local judge is unavailable, use an explicitly labeled surrogate and audit approximately 200 stratified examples for grading errors. Fix obvious evaluator defects on separate calibration data, not in response to whichever model is currently losing. No surrogate establishes the hidden leaderboard result.

**Output and geometry requirements belong in week one**

The brief specifies independent task/context passes, JSON outputs with rationales, detection boxes in `[x, y, width, height]`, and IoU ≥ 0.5 for detection correctness. It specifies BF16/FP16 final inference. [Official brief, pages 3 and 6–10](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf)

Our engineering actions:

- Import the exact task/context schemas from the official release. Do not guess task-pass key names.
- Train context questions as independent image-only records, without the task answer or task-question metadata carried over.
- Match requested metadata keys exactly and handle missing annotations separately from genuine visual uncertainty.
- Use concise, visible-evidence rationales inside the required JSON. Do not train long speculative explanations or judge-directed language.
- Verify native processor resizing, aspect ratio, overlays, box coordinate units, and inverse transforms. Test xyxy-to-xywh conversion and out-of-bounds boxes.
- Check the training framework for automatic coordinate conversion. Qwen3.5 tooling may normalize coordinates to a 0–1000 convention; that must not silently override the challenge's prompt. [ms-swift documentation](https://github.com/modelscope/ms-swift/blob/main/docs/source_en/BestPractices/Qwen3_8-Best-Practice.md)
- Preserve raw outputs. Do not add JSON repair, coordinate clamping, extra cropping calls, or repeated generation to official scoring unless the official harness explicitly provides it.
- For thinking-capable models, verify organizer handling of thinking mode and the token limit. Measure truncation and schema behavior in the allowed configuration.

Target at least 99.5% raw JSON validity on a large external validation run before expensive scaling. This is our engineering target, not an organizer threshold.

**Data program: build reliable visual supervision**

Every training record should carry source URL/version, original item ID, patient/slide/experiment group where available, split, image hash, modality, task, annotation origin, transformations, and the basis for permission to use it. Store license and overlap review at source level. Maintain known overlaps with MMBU contributors for disclosure; do not try to discover the hidden test set.

Candidate sources to inspect, not an approved ingestion list:

| Source family | Potential contribution | Screening decision |
|---|---|---|
| [ROCOv2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11208523/) | Radiology image/caption/concept examples; some metadata supervision | Retain only relevant, image-supported targets; inspect article-level rights and split separation |
| [PMC-VQA](https://arxiv.org/abs/2305.10415) training split | Broad medical image questions | Remove questions dependent on omitted choices, captions, or invisible clinical context; inspect panel alignment |
| [Broad Bioimage Benchmark Collection](https://bbbc.broadinstitute.org/image_sets) | Microscopy, object locations, masks, counts | Screen individual sets and annotations; check permitted overlap with MMBU sources before use |
| [Chest ImaGenome](https://physionet.org/content/chest-imagenome/1.0.0/) | Anatomical boxes and region-linked observations | Optional; credentialed access and DUA apply. Establish compatibility with the intended model release first |
| Separately sourced pathology, ultrasound, endoscopy, dermatology, and fundus training sets | Cover gaps in modalities and tasks | Data owner identifies primary sources with reliable labels and clear use conditions; include only cleared sources |

Convert existing human annotations into visual questions where possible. For segmentation, a class-labeled region supports a region-identification question; an unlabeled foreground mask does not establish a disease diagnosis. For detection, use genuinely annotated target boxes. Captions may provide useful context but must not become fabricated pixel-level labels.

Pilot scope: approximately 20,000 verified training records from multiple independent sources. Count unique images and sources as well as question records. Scale toward 100,000–300,000 records only if validation and review show the added sources are useful. These are workload envelopes, not claims about available clean data.

Initial sampling proposal: 35% whole-image questions, 20% region classification split between box and mask inputs, 20% localization, 20% context identification, and 5% permitted general visual instruction replay. This is an ablation starting point. Cap any one source's dominance and compare metadata sampling rates while holding overall exposure approximately fixed.

Have a domain reviewer inspect a stratified sample of at least 200 pilot records, including every new conversion type. Review more heavily wherever disagreement or ambiguity appears. Do not assign specimen, stain, or body-part labels solely from a folder name when the visual task cannot support them.

Synthetic augmentation is secondary. If permitted, use a teacher to rephrase valid questions and produce short rationales grounded in established annotations; filter unsupported claims. Confirm provider terms and API access separately. Claude Max is not assumed to include API credits or authorize an automated labeling pipeline. Do not send restricted dataset images to a service without the requisite data permission.

**Training sequence**

1. **Reproducible language-adapter baseline.** Freeze vision initially; run SFT with verified targets and the required response structure. A reasonable pilot starts with LoRA rank 32, learning rate 1e-4, one data pass, assistant-target-only loss, gradient checkpointing, and a short warmup. These are starting settings, not optimized hyperparameters. Adapt module selection to each architecture; verify the image inputs are present and used.
2. **Controlled component adaptation.** Compare language-only adapters with language plus multimodal projector/merger adaptation, then with adapters in selected late vision blocks. Keep data and effective exposure matched. Check gradients and saved parameter names. Use conservative rates for directly unfrozen pretrained weights, and preserve their values in the exported model.
3. **Data and task improvements.** Add better localization records, context identification, and undercovered modalities one intervention at a time. Use reviewed training errors to prioritize additions; do not mine labels from the locked validation set.
4. **Scale the winning recipe.** Increase unique data coverage and training duration separately so we can identify what helped. Rebalance dominant sources. Track regressions in the untouched general-vision set and every major biomedical family.
5. **Optional preference/RL stage.** Attempt only if SFT works and independent training-data diagnostics show useful answers are already within the model's capabilities. Prefer verifiable localization/label feedback. Compare against equal-budget additional SFT and keep the SFT checkpoint if improvement is inconclusive. Multiple samples may be used for permitted training experiments, never as a submission-time strategy.

The rationale for putting RL late is supported by a controlled medical-VLM study finding that RL is most useful when the model already has useful answer support; it is not a guarantee about MMBU. [When Does RL Help Medical VLMs?](https://arxiv.org/abs/2603.01301)

Use a maintained multimodal trainer with a thin dataset adapter, not a new training framework. ms-swift supports the current Qwen multimodal families; Unsloth is a possible constrained-memory alternative. Pin the tested environment after the smoke run and verify all intended visual components survive export. [ms-swift](https://github.com/modelscope/ms-swift/blob/main/docs/source_en/BestPractices/Qwen3_8-Best-Practice.md), [Unsloth vision tuning](https://unsloth.ai/docs/models/qwen3.5/fine-tune)

QLoRA is a training-memory option. Final evaluation must use the exported BF16/FP16 artifact. Reload the exact original base and learned adapters/components, export the supported full model, and score that artifact afresh; do not assume a quantized training checkpoint behaves identically after export.

**Experiment queue and decision rules**

| ID | Question | Controlled comparison | Evidence needed to proceed |
|---|---|---|---|
| E00 | Is inference faithful? | Raw model outputs versus harness parsing on checked examples | Correct schemas, geometry, two-pass isolation, and precision |
| E01 | Which starting models are viable? | Three untouched bases, same external validation | Complete T/C/runtime/error reports |
| E02 | Which base adapts best? | Same pilot records, one short SFT run per feasible base | Best score improvement with acceptable runtime; repeat close finalists |
| E03 | Does visual adaptation matter? | Language-only versus added projector/vision updates | Repeated improvement beyond the baseline, without broad regressions |
| E04 | Does explicit localization supervision help? | With versus without extra verified box/mask-derived tasks | Detection/region gains that transfer across sources |
| E05 | What context mix helps? | Two or three metadata sampling rates | Improved S, not merely higher C at the expense of T |
| E06 | Does diversity outperform volume? | New-source records versus more records from existing sources | Better external source-held-out results at similar exposure |
| E07 | Is synthetic augmentation worth its cost? | Reviewed augmentation versus human-label-only control | Validation gains plus acceptable audited label quality |
| E08 | Does the recipe scale? | More unique records, then longer training | Continued gain per GPU-hour rather than accumulating overfit |
| E09 | Does preference/RL improve on SFT? | Short post-training stage versus equal-budget extra SFT | Repeated positive gain; otherwise discard this branch |
| E10 | Does the deliverable reproduce? | Training checkpoint versus fresh exported/reloaded model | Matching behavior within expected numerical variation and no deployment failure |

Run cheap pilots first. Repeat promising results on a second seed before making them a central claim. Use up to three seeds for the final recipe when budget permits. Bootstrap uncertainty measures evaluation uncertainty; repeated seeds address training variability. They are not substitutes for one another.

After two failed or inconclusive attempts at the same idea, return to error analysis and write a revised hypothesis. Stop that branch until the revision identifies a different mechanism or better evidence. Avoid full-factorial sweeps. A larger learning rate, longer training, and a new dataset in the same run cannot explain which change caused the result.

No new model families or expensive research branches after December 4 without a compelling measured reason. Keep the best validated checkpoint recoverable throughout.

**Calendar and acceptance milestones**

| Dates | Priority | Required deliverable |
|---|---|---|
| Oct 3–9 | Access, rules, evaluator, clean data pilot | Written decisions on unclear rules; baseline predictions; throughput measurement; source manifest |
| Oct 10–16 | Three-base pilot and early error review | Paired adaptation results; one chosen base and one fallback |
| Oct 17–23 | Language/projector/vision ablation | First repeatable evidence about which components to train |
| Oct 24–30 | Grounding and context supervision | Verified box transforms; task/context mixture comparison |
| Oct 31–Nov 6 | Broader modality/source coverage | Data release v1; evidence on source-held-out generalization |
| Nov 7–13 | Scale the best recipe | Medium-scale checkpoint and cost/benefit report |
| Nov 14–20 | Target remaining visual failures | One focused improvement with a matched control |
| Nov 21–27 | Optional synthetic or preference/RL branch | Retain only improvements exceeding a simple SFT continuation |
| Nov 28–Dec 4 | Final method selection | Freeze base, source list, and main recipe; retain fallback |
| Dec 5–11 | Final training and seed confirmation | Short finalist list; complete run provenance |
| Dec 12–18 | Locked validation and export rehearsal | Final checkpoint choice; fresh-machine reproduction |
| Dec 19–23 | Release and submission preparation | Submission-ready model by Dec 20; model card, data disclosure, dependencies |
| Dec 24–28 | Final delivery | Ungated HF artifact and organizer submission by internal cutoff, when the official portal permits |
| Dec 29–31 | Contingency | Resolve upload or organizer-confirmed compatibility issues; no speculative retraining |

If dev/harness access is delayed, advance data provenance, external validation, and native model smoke tests. Do not claim official scores from a substitute evaluator. If GPU access is delayed, reduce the model/experiment scope rather than eliminating evaluation or the release buffer.

**Compute and team operating plan**

| Available resources | Adaptation plan |
|---|---|
| One 24 GB GPU | Profile 7–9B QLoRA at conservative image-token budgets; use a 4B candidate if memory or iteration speed is inadequate. Arrange access to a machine that can evaluate the final full-precision artifact. Skip large-model and RL branches. |
| One 48 GB GPU | Profile LoRA/QLoRA for 7–9B candidates; run models sequentially and limit vision updates to the useful subset. Preserve time for export validation. |
| One 80 GB GPU | Preferred planning target for repeated 7–9B experiments; measure high-resolution memory before committing. Occasional extra GPUs help finalist repeats. |
| Several 80 GB GPUs | Parallelize independent trials or scale supported training. Permit a larger-base scout only if it will not displace data review and robust validation. |

These are planning options, not guaranteed fits. Resolution, visual-token count, sequence length, trainable modules, optimizer state, and implementation determine memory and speed.

Before reserving a large block of compute, benchmark 200–500 representative batches including the high-resolution tail. Estimate wall time as `training records × epochs / measured records per second`, then add evaluation, checkpointing, and restart overhead. Compare architectures using measured GPU-hours and effective exposure. Get actual pricing and an agreed spending ceiling at execution time.

Proposed allocation of the available GPU-hour budget: 10% evaluation/integration, 15% base selection, 45% data-and-adaptation experiments, 15% final training/reproduction, and 15% reserve. These add to 100%; change them explicitly if the measured bottleneck changes.

| Responsibility | Weekly obligation | Success measure |
|---|---|---|
| Model/evaluation owner | Maintain paired baselines, run queue, metric implementation, environment | Every result is reproducible and comparable |
| Data owner | Add cleared sources, review conversions, de-duplicate, maintain splits | More useful diversity without unreliable labels or leakage |
| Review/release owner | Audit examples/results, record organizer answers, rehearse exports | Problems found before the final submission |

Arrange periodic review by someone familiar with the relevant biomedical images if the team lacks that expertise. A domain reviewer should assess label validity and visible evidence, not merely whether text sounds medically plausible.

Hold a 30-minute weekly decision meeting: strongest current result, evidence for the last change, top error categories, cost spent, next one or two experiments, and explicit stop decisions. Maintain a private experiment ledger containing hypothesis, base SHA, dataset manifest hash, code commit, environment lock, seed, trainable modules, cost, scores, and keep/drop rationale.

Use Paperclip and any granted Claude account for literature synthesis, code review, data-conversion review, and experiment documentation. Do not assume either provides training GPUs, batch APIs, or model-training rights beyond its actual terms.

**Organizer clarification draft — prepared, not sent**

Hello MMBU organizers,

Our team has been accepted for Medical Domain Adaptation and is setting up experiments. Could you clarify the following?

1. Where are the official development dataset and evaluation harness, and which versions should teams use?
2. The brief provides dev data for local evaluation but rule 6 broadly prohibits checkpoint selection using MMBU evaluation examples. May we use the public development set for validation, model selection, and hyperparameter selection? May any part be used for training? We will keep it out of training unless explicitly allowed.
3. What is the policy on independent training splits of datasets that also contribute to MMBU? Is there an approved exclusion or overlap-check procedure that does not reveal hidden examples?
4. May we revise our application’s intended base after initial experiments, and how should we disclose an already adapted starting checkpoint or later changes to vision components?
5. Please confirm the exact task/context JSON schemas, bbox coordinate units, handling of multiple/absent targets, and how unknown metadata is graded. What code implements the local judge and context averaging?
6. What hardware, memory, image-resolution, token, runtime, dependency, and thinking-mode constraints will the official harness enforce? Are model-native resolution handling and standard preprocessing used unchanged?
7. Are external-model-generated training questions/rationales permitted with source disclosure? Does the challenge supply any API or GPU credits in addition to the listed software subscriptions?
8. Please confirm the submission procedure, base-checkpoint availability requirements, and December 31 end-of-day AoE cutoff. For the October 7 workshop, does 9 a.m. PST mean 9 a.m. local Pacific time?

Thank you.

**Release criteria**

- [ ] Final selection is supported by repeated external-validation gains in S and an independent locked-set check; limitations are reported honestly.
- [ ] Actual initialization and all subsequently trained components are documented; base and final checkpoints can both be evaluated fairly.
- [ ] The frozen model loads from a fresh environment in the required precision; its processor, chat template, and generation configuration are complete.
- [ ] Both independent passes work, requested keys match, and raw-output validity and runtime meet our targets and the organizer limits.
- [ ] Coordinate transformations have been checked on known examples, including small and boundary-touching boxes.
- [ ] Full active/total parameter counts include vision, language, projection, and inference-time adapters.
- [ ] Training sources, synthetic generation, known overlap, and use conditions are recorded, with no intentional optimization on prohibited evaluation material.
- [ ] One frozen end-to-end checkpoint is prepared for this track; the deployment needs no extra model, tool, retrieval, or repeated sampling. [Official restrictions](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf)
- [ ] The release has a model card, exact revisions/hashes, environment, evaluation report, and data disclosure; ungated downloading and fresh loading are verified when published.
- [ ] Submission receipt is retained. The local fallback remains archived even though only one final checkpoint is designated.

**Immediate decision:** establish resources and official access, then complete E00–E02. A working evaluator, a clean pilot dataset, and measured adaptation gains will tell us where to invest the remaining ten weeks.
