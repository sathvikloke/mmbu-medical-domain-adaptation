# MMBU domain adaptation plan — revision 2

October 3, 2026. Revised after independent review of the first plan and discovery of the official public dataset card. This is a prospective plan, not evidence of a trained model's performance or a winning probability.

**Decision:** retain the perception-focused hypothesis, but replace the early calendar-driven model commitment with evidence gates. First establish the evaluation contract, then compare two practical candidates under both language-only and limited visual adaptation. Build a small, reliable data pipeline before expanding it. Keep a recoverable submission baseline throughout.

**Current limits:** compute, spending ceiling, team hours, domain-review capacity, authenticated dataset access, and official harness availability remain unconfirmed. Planning can proceed; large training commitments cannot yet be costed. The acceptance email gives a December 31, 2026 end-of-day AoE deadline. Our internal target remains December 28, 17:00 Chicago, with a deliverable ready December 20. December 31 AoE ends January 1, 2027 at 06:00 Chicago.

**First resolve the actual interface**

The [official public dataset card](https://huggingface.co/datasets/mmbu/mmbu-public) is visible. It reports 3,147 image/question rows; the public API lists 3,147 image files. We have not downloaded or inspected the gated examples, accepted access terms, or executed the official evaluator. The observed repository revision was `069da7bbd6201a867039b548f3c02e103711ed4a`.

The card and the [challenge brief](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf) do not fully agree:

| Contract item | Brief | Public card | Action |
|---|---|---|---|
| Task rationale | Rationale and answer in JSON | Rationale before answer-only JSON | Obtain authoritative version; do not mix formats |
| Invalid JSON | Affected pass receives zero | Raw reply is scored as fallback | Treat scores as provisional until resolved |
| Segmentation-derived labels | Semantic equivalence description | Multiple labels allowed, but shown judge demands one concept | Ask for actual multi-label grading policy |
| Context pass | Independent metadata pass contributing C | Visible card describes task evaluation only | Obtain context prompts, masking, and scoring implementation |

Neither document silently overrides the other. Archive both, pin the eventual harness commit and organizer clarification, and version the contract. Until resolution, local engineering tests are useful, but expensive schema-specific training and score-based model elimination are premature.

The dataset's technical split name is `train`; that is **not authorization to train on challenge examples**. Keep challenge data out of training. Confirm permitted public-dev selection separately.

**Optimize the right quantity without overstating the proxy**

The brief defines `S = (0.8T + 0.2C)(T − T_base)`, with adapted task accuracy equal to T. For C, first average applicable fields within each evaluation example, then average the same example population used for T. Repeated images do not silently collapse into one row. Base and adapted predictions must use matching organizer conditions. [Scoring brief](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf)

Keep three labels on the dashboard:

- **Official-protocol local score:** only when the published/confirmed protocol and permitted data usage are reproduced. This is still not a hidden-set result.
- **External development proxy:** useful for selecting experiments, with source/task composition shown.
- **Engineering diagnostic:** format checks, image interventions, export tests, or surrogate grading; never presented as official accuracy.

For every candidate report T, C, task gain, S, source/task counts, output validity, truncation, and measured cost. Keep failed or missing responses in the denominator according to the confirmed contract. Report per-task and per-source results as well as the sample mean.

Compute each alternative mixture score by reweighting T, C, and T_base first and then applying the product; averaging source-level S values is generally a different quantity. Show a source-balanced view and a small prespecified range of task/modality weights as sensitivity analyses. These do not identify the hidden distribution. If reasonable reweighting reverses the ranking, retain the uncertainty rather than claiming a universal winner.

For the external proxy, predeclare equal weight for each of the four broad task groups, with equal source weights within task and equal example weights within source/task. Counting is reported separately but stays within global classification for this proposal. If a task group is absent, report partial-coverage diagnostics without ranking models on a nominal full-task proxy. Alongside the natural sample mixture, stress each task group at weight 0.4 with the other three at 0.2. These are transparent hypothetical mixtures, not inferred hidden weights; preserve them across candidates. Modality/source diagnostic weights must likewise be recorded before comparative scoring. A rank reversal, a paired interval spanning zero, or plausible grading errors that reverse the order makes superiority unresolved. A cost-driven engineering choice remains possible, but must be labeled as such.

The central claim we seek is a repeatable increase in adaptation score on permitted evaluation data. A separate perception claim requires evidence that image information helps. Neither establishes first-place probability before the hidden ranking exists.

**Base-model selection must test the intended training method**

Use [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) as the initial compatibility baseline and [Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) as the first alternative. [Qwen3-VL-8B-Instruct](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) is the fallback if Qwen3.5 has harness, export, memory, or runtime problems, or an inexpensive initial screen justifies it. These are candidate choices, not a demonstrated ranking.

1. Verify raw inference, native image handling, and non-quantized BF16/FP16 reload for each feasible base, as required by the published brief. Freeze its exact revision and fair baseline conditions.
2. Train the same small external pilot on the first two candidates using language adapters. Match examples and effective exposure, and record architecture-dependent tokens and GPU-hours.
3. Before eliminating either, run one bounded projector/late-vision adaptation probe on each. Include a second learning-rate setting only if the first run is visibly unstable or leaves a close ranking sensitive to that setting.
4. Compare learning curves at equal exposure and at comparable cost. A one-epoch winner is not evidence of a better eventual ceiling. Stop plainly infeasible configurations early; treat close or unstable rankings as unresolved.
5. Select a primary model using development validation after these probes, with one fallback retained. Target October 23, conditional on access and measured throughput. Do not force an under-evidenced decision solely to meet that date.

Current recommendation: begin implementation with Qwen2.5, but do not claim it is the best competition base. Disclose the actual starting checkpoint; initializing from a medically adapted model changes the starting point that must be declared. No larger-model or RL branch is part of the initial commitment.

**Show that improvements use the image**

On a separate external diagnostic subset, compare correct-image performance with no-image/blank-image and within-modality mismatched-image conditions. Keep the question, output rules, and scoring fixed, and interpret each intervention's limitations: blank images are out of distribution, while some questions are answerable from textual context. Include paired examples where a valid image change should change the answer. These diagnostics are outside official submission evaluation and add no extra inference to the submitted system.

Track the adapted-versus-base gain with real images separately from its gain without useful images. Add balanced question templates and label frequencies where possible. If gains persist unchanged when useful visual evidence is removed, describe them as answer/format/prior improvements; do not call them established perception gains.

This check is material: MMBU Table 8 reports OctoMed open ungrounded F1 of 0.070 with images and 0.077 without them. That descriptive difference is not proof of a statistically significant disadvantage, but it prevents treating its task gains as automatic evidence of visual improvement. [MMBU paper, Table 8](https://arxiv.org/html/2606.06696v1#S9)

**Separate development, selection, and confirmation**

| Partition | Allowed use | Rule |
|---|---|---|
| External training | Optimization, augmentation, training-error review | Cleared sources and recorded group lineage |
| External development validation | Hyperparameters, checkpoints, base selection, error analysis | Adaptive use is acknowledged; not independent confirmation |
| External confirmation | One frozen primary-versus-base comparison after all selection | No ranking finalists or choosing a seed on this set |
| Official public dev | Only uses organizers explicitly permit | Never assume its split name establishes permitted use |

Separate patients, studies, slides, acquisition batches, and derived images across partitions. Check exact hashes and near duplicates across sources; parent-child crops, relabeled copies, and alternate file encodings require more than exact-ID matching. Hold out entire sources for confirmation where feasible. If there are too few independent sources, narrow the transportability claim rather than relying on a large number of correlated patches.

Choose the primary checkpoint and seed on development data before opening confirmation. If the confirmation result is disappointing, retain it. Any model change informed by that result retires the set into development; a new independent set is required for a new confirmation claim. A fallback can be substituted for a mechanical loading failure only under a prewritten rule and without using confirmation scores to choose it; disclose the deviation.

For intervals on a fixed source mixture, bootstrap independent entities within source and keep all paired base/adapted outputs together. For transport across sources, additionally summarize source-level variation or use hierarchical resampling when the number of sources supports it. Recompute the nonlinear score within every replicate. Do not treat seeds, images, and sources as interchangeable units, or a bootstrap as evidence about an unknown hidden population.

Do not mandate 1,500–3,000 examples before knowing the independent-unit count and costs. Begin with an external diagnostic/development subset, then expand according to observed paired disagreement, clustering, and the smallest useful gain we can afford to distinguish. Select that practical gain threshold and resampling design before using them as promotion criteria. Repeat promising training runs on another seed; label small-set results exploratory.

If a surrogate judge is required, fix its prompt/version and validate it on a separate, blinded, stratified calibration sample. Include single labels, synonyms at different specificity, counting, multi-label answers, refusals, and malformed responses. Compare candidate rankings as well as per-answer agreement. If grading uncertainty could change the decision, defer elimination or obtain human adjudication; high judge agreement alone is not proof of correctness.

Include every contender's base and adapted outputs in that blinded review. Report random-sample grading disagreement separately from deliberately oversampled model-disagreement cases; do not interpret the latter as a population error rate. Recompute paired score differences under the adjudicated decisions and plausible unreviewed grading error. E00 includes unequal metadata-field counts, repeated-image examples, and zero annotated fields: for example, nine correct-context rows from one image and one incorrect row from another give C=0.9, not the image-deduplicated 0.5. Zero-field behavior must come from the authoritative contract, not an invented zero or perfect score.

**Build a small data program that can earn expansion**

Begin with 200–500 external records for loading/geometry/target-construction checks, then approximately 2,000–5,000 usable training records for the first comparison. These are staged workload targets, not assertions of statistical power or guaranteed clean data. Move to 20,000 only after data acceptance and throughput gates pass. The previous 100,000–300,000-record envelope is optional scaling, not a baseline requirement.

Maintain a source registry before ingestion: owner/version, upstream images, permitted use and release conditions, known MMBU overlap, independent grouping fields, accessible annotation types, conversion recipe, and review status. Unknown release compatibility leaves a source out of the initial run. No restricted source or synthetic generation service is necessary for the first baseline.

Candidate-source decisions:

- [ROCOv2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11208523/): screen for visually supported metadata and useful captions; it does not automatically supply all task labels or boxes.
- [PMC-VQA](https://arxiv.org/abs/2305.10415): consider permitted training records only; reject questions requiring missing choices, captions, or invisible clinical information.
- [BBBC](https://bbbc.broadinstitute.org/image_sets): inspect each source separately for label meaning, masks/counts, rights, and allowed overlap. A foreground mask is not a diagnostic label.
- [Chest ImaGenome](https://physionet.org/content/chest-imagenome/1.0.0/): optional after credential/access and public-model-release compatibility are settled. Its automated annotations require their own quality assessment.
- Add separately cleared sources from other imaging families based on the measured gap and available review expertise, rather than committing to every modality at once.

The initial baseline requires at least two independent cleared source families with useful labels; if only one is available, treat that run as an engineering pilot with narrow claims. Do not misrepresent synthetic variations of one image as independent biomedical coverage.

For every record retain image/parent hashes, source/group IDs, split, annotation origin, task/subtype, applicable metadata, transformation history, and target-generation version. Screen all records for image decoding, target schema, geometry, missing labels, duplicate lineage, and allowed split. Stratified human review checks conversion quality and visual support; it does not certify every unaudited record as correct.

Use a two-step QA gate: first inspect at least 20 records from every new source/conversion combination; any critical mismatch such as the wrong region, coordinate frame, diagnosis inferred from an unlabeled mask, or leaked reference answer quarantines that conversion until repaired. Then audit a random stratified batch and record the actual error counts by stratum. Set source-specific tolerance based on label risk and the pilot, and record it before bulk release. These review counts are operational starting points, not guarantees of population error rates.

Sample by training-record draws, while logging unique images, independent groups, visual tokens, and supervised target tokens. A starting mix can emphasize recognition, region understanding, localization, and context; it is a hypothesis, not an 80/20 consequence of the metric. The default objective is mean cross-entropy over unmasked assistant-target tokens, with prompt/image/padding positions masked; verify the trainer's accumulation normalization. Consequently, percentages of record draws are not percentages of loss contribution. Before each controlled run, record exact task/subtype draw weights, a source cap feasible for the accepted source count, and realized exposure. Do not let multiple questions per image or one large source dominate silently. Compare additions through replacement at matched exposure, or label the experiment as increased-data-plus-compute rather than a clean task-mix ablation.

Keep counting and multi-label segmentation explicit in the schema, even if counting is grouped under classification in the scoring brief. Preserve pre-drawn regions where that is the confirmed input convention. Only detection should generate coordinates. Test single/multiple boxes, pixel units, resizing, and exact output serialization against the authoritative contract.

If small-object errors persist after geometry checks, use a small external cohort to compare two permitted native image-token budgets, holding base/adapted processing identical within each condition. This optional diagnostic separates lost visual detail from a failure of the adaptation method; it does not add an auxiliary cropper or repeated generation to submission inference.

Use separate allowlisted input builders for task inference, context inference, and grading. Task inference receives only the image, permitted question and official task/system text. Context inference receives the image and official requested-field prompt, without the task question, task answer, predicted metadata from another pass, or carried conversation/cache state. Never pass reference answers, judge-only options, dataset label vocabulary, source metadata, or stored annotations into model inference unless explicitly included by the official harness.

**Submission requirements retained from the published brief**

These are explicit release checks, not optional experiments. Resolve the documented source conflicts above without silently changing the remaining published rules. [Official brief, pages 5–11](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf)

- Medical Domain Adaptation has no model-size ceiling. Count and disclose both total and active parameters across language, vision, projection, and inference-time adapters; more than 27B active parameters requires organizer evaluation through an API. The proposed smaller candidates use the publicly downloadable, ungated Hugging Face route. Disclose the actual base and make it available under the applicable rules.
- Submit one frozen checkpoint for this track. It must be a single end-to-end VLM: no ensemble, cascade, auxiliary model, external OCR, retrieval, learned pre/postprocessing, or other model orchestration. Evaluation cannot use web/API/database access, calculators, code execution, or other external information.
- Use the official harness and organizer inference settings, with independent task and context passes. Neither pass sees the other's output or state. Do not add repeated sampling, self-consistency, iterative prompting, test-time adaptation, or evaluation-time weight changes.
- Preserve raw outputs. Do not silently repair JSON, clamp coordinates, or add crop-and-retry inference outside the official harness. Test pixel xywh conversion, resizing/inverse transforms, single/multiple boxes, and IoU threshold behavior against confirmed fixtures; pin or disable trainer coordinate normalization that would silently convert pixels to 0–1000 units.
- In the context pass, return exactly the requested metadata keys and handle genuine visual uncertainty with the published unknown convention. Confirm missing-annotation and zero-field scoring before claiming equivalence. The visible brief provides a context prompt; its executable implementation and any later amendment still need confirmation.
- Evaluate the exported non-quantized BF16/FP16 artifact in a fresh environment. Include vision/projector/adapters, processor, chat template, generation settings, dependencies, revisions, and hardware requirements. Participant-side loading, memory, formatting, or runtime failures do not automatically qualify for organizer reruns.
- Disclose major pretraining, continued-pretraining, fine-tuning, and synthetic sources and known overlap. Do not intentionally optimize on prohibited MMBU evaluation material or its derivatives; public-dev permissions remain an explicit clarification item. No hidden-test discovery, judge/prompt manipulation, or metric exploitation is part of this program.
- Keep non-public challenge analysis and coordinated strategy within this registered team; follow the published membership and anti-collusion rules. Retain the final upload/submission receipt and verify ungated download and fresh loading when released. Hidden results arrive after submissions close; official ties use task score T.

**Minimum experiment sequence**

| Stage | Comparison | Advance only when |
|---|---|---|
| E00 | Contract fixtures and non-quantized BF16/FP16 load/export smoke check | Interface is pinned for score claims; engineering checks catch deliberately broken outputs |
| E01 | Two fair untouched bases and measured resource profiles | Both are viable within actual budget, or fallback replaces one |
| E02 | Matched language-adapter pilot plus bounded visual probe per base | Data QA passes; ranking is not solely a format, learning-rate, or short-horizon artifact |
| E03 | One data/vision improvement versus matched baseline | Development results justify repetition; major task/source losses are reviewed |
| E04 | Repeat and modestly scale the retained recipe | Gain survives another seed and remains useful per measured cost |
| E05 | Freeze choice, run confirmation once, reproduce exported artifact | Claims match the evidence; no hidden selection on confirmation |

Detectability, cost, and effect size determine whether an inconclusive run merits repetition; a calendar milestone does not turn it into a positive result. Stop after two unsuccessful attempts at the same unchanged hypothesis, document the reason, and revise the mechanism before trying again.

Do not add preference/RL, a much larger base, extensive teacher labeling, or multiple alternative frameworks until the core sequence works. If a later branch is funded, compare it with equal-cost additional SFT. The late-RL hypothesis is informed by [a controlled medical-VLM study](https://arxiv.org/abs/2603.01301), not established for this challenge.

Use a maintained multimodal trainer, verify the actual trainable modules and saved weights, and pin a working environment. LoRA rank and learning rate are pilot choices, not universal architecture-independent settings. QLoRA may reduce training memory, but every promoted candidate must be evaluated after export to non-quantized BF16/FP16, as the published brief requires. Record any later organizer amendment explicitly. Check that projector/vision weights, processor, and template survive. [ms-swift guidance](https://github.com/modelscope/ms-swift/blob/main/docs/source_en/BestPractices/Qwen3_8-Best-Practice.md)

**Resources and promotion gates**

Confirm actual GPU model/count/access windows, spend ceiling, weekly contributor hours, storage, and review availability. An 80 GB GPU is a planning preference, not an established requirement or fit guarantee. Constrained hardware reduces model size, resolution within allowed limits, and experiment count; it does not remove baseline evaluation, data review, or export testing.

Benchmark a representative short run including the high-resolution tail. Budget total system work: training, two inference passes, grader calls, preprocessing, export/reload, and human QA. Record GPU-hours by hardware, API charges, wall time, and human hours separately. The first plan's compute percentages are superseded by measured per-run costs and a protected 15% compute reserve. Do not purchase or book resources based on this document alone.

Before scaling, the run owner supplies an itemized estimate, a resource owner approves it within the team's agreed ceiling, and a finish-by time leaves enough evaluation/release buffer. If access is unresolved by October 9, execute only local data/contract work and reduce the October run queue. Once resources arrive, rerun the estimate against remaining calendar time instead of compressing all missed work into November.

**Seven-day first sprint, starting when access and compute are ready**

| Day | Deliverable | Stop or narrow condition |
|---|---|---|
| 1 | Contract register, dataset-access status, named owners and actual budget | Unresolved contract: engineering only, no final-score claims |
| 2 | 200–500 external engineering records and grouping/QA manifest | Bad geometry, label semantics, or rights: quarantine affected source |
| 3 | Native baseline predictions, image diagnostics, export/reload smoke check | Broken image path or export: repair before training |
| 4 | First short language-adapter pilot and measured end-to-end cost | Cost exceeds ceiling: reduce scope before extension |
| 5 | Second base pilot if viable | Otherwise test compatible fallback; record unequal exposure |
| 6 | Bounded visual adaptation probes and error review | No safe visual path: retain language baseline and narrow claim |
| 7 | Paired development comparison, uncertainty/cost ledger, next experiment decision | Inconclusive: retain two candidates; do not force a winner |

Days are work-order targets, not unmeasured runtime promises. The pass/fail outcomes and remaining time determine the next step.

**Calendar guardrails**

- October 3–9: obtain authoritative protocol/access, resource facts, and a reviewed engineering dataset.
- October 10–23: stage the candidate pilots and visual probes; choose a primary only when the evidence supports it.
- October 24–November 20: one base, one active improvement at a time; expand clean data and repeat useful results.
- November 21–December 4: retain only evidence-backed improvements; stop new model families and expensive branches.
- December 5–11: final training and development-set checkpoint selection; freeze before confirmation.
- December 12–18: one-time confirmation and clean-environment reproduction. A failed scientific confirmation is recorded, not tuned away on the same set.
- December 19–28: complete disclosure, model card, ungated release and organizer submission when the portal permits. Preserve December 29–31 for delivery contingencies.

Assign one named owner for model/evaluation, one for data, and one for review/release; roles may overlap. Weekly review chooses at most the next two experiments, records costs and negative results, and checks that all gates still hold. Software sponsor accounts assist challenge work but are not presumed to provide GPUs, API credits, automatic data-upload permission, or shared credentials.

**Priority organizer questions — draft, not sent**

1. We found `mmbu/mmbu-public` at revision `069da7bbd6201a867039b548f3c02e103711ed4a`. Which dataset/harness version and clarification govern final evaluation?
2. Does task rationale belong inside JSON or before answer-only JSON? Does invalid JSON receive zero or fallback grading? How are multi-label segmentation answers reconciled with the shown one-concept judge?
3. Where is the context-pass evaluator, including requested-field masking and unknown handling? Please confirm detection pixel units, multiple-box scoring, and counting handling in the final harness.
4. May public-dev data be used for model/hyperparameter/checkpoint selection? What is permitted for independent training splits of contributing datasets? We will not train on the public challenge split without explicit authorization.
5. May the declared intended base change after pilots, and how should previously medically adapted starting checkpoints be declared?
6. Beyond the published BF16/FP16 requirement, what memory, runtime, token, image-resolution, thinking-mode, preprocessing, and dependency limits apply? Are external-model-generated training examples permitted with disclosure?

Other logistics—submission procedure, GPU/API support, deadline display and workshop timezone—can be handled in the same office-hours conversation. No organizer message or access acceptance has been performed during this audit.

**Completion standard**

A useful final entry is a single reproducible, eligible model with honest paired baseline evidence and complete provenance. A strong result on our development proxy is grounds for a submission decision, not a guarantee about the hidden leaderboard. The next concrete milestone is E00–E02 with actual resource measurements and a resolved scoring contract.
