# Competition-first Track 2 recipe

**Specified:** October 17, 2026  
**Status:** prospective, no model/data/result claim  
**Role:** primary execution path unless a gated research branch earns promotion

The immutable field/state contract is specified in
[COMPETITION_MANIFEST_SPEC.md](COMPETITION_MANIFEST_SPEC.md).
The binding safety/selection corrections are recorded in
[COMPETITION_RECIPE_REDTEAM.md](COMPETITION_RECIPE_REDTEAM.md).

## Decision

The submission should not depend on a high-novelty mechanism. Under the current single-model, single-pass,
offline-loadable, limited-compute constraints, the adverse search did not find a defensible 9/10-novel method. QUILT
was demoted after direct antecedents and an identifiability defect were found. MOSAIC remains blocked by source-factor
identifiability and loader/compute risk.

The primary path is therefore one ordinary shared LoRA trained with **co-primary answer-task and authoritative
biomedical-context objectives** on a task-balanced, context-balanced, source-balanced admitted mixture, with exact
geometry/serialization contracts, held-out-source and held-out-template development, base-relative regression reporting,
and visual-dependence checkpoint rejection. Curriculum order is an ablation, not the flagship idea. This is a
score-and-reliability design, not a method-novelty claim. The independent decision record is
[the idea arbitration](INDEPENDENT_IDEA_ARBITRATION.md).

Here `co-primary` means that both endpoints receive supervised training, separate reporting, and regression gates. It
does **not** mean equal loss weight or equal leaderboard importance: the documented score makes task performance
structurally primary, while the useful context weight depends on positive task gain over the frozen base.

## Frozen candidate family

After one base is selected under the prospective
[adaptation-frontier screen](BASE_SELECTION_FRONTIER.md), the minimum within-base candidate set is:

1. **B0:** untouched pinned base.
2. **B1-L:** language-side shared LoRA only.
3. **B2-P:** projector plus late-language shared LoRA.
4. **B2-F:** the prospectively fixed larger shared-LoRA profile only if native memory permits it.

All candidates use the same selected immutable base, admitted independent units, task views, prompts, target serializers, optimizer budget,
seeds, and evaluator. No MMBU public example, answer, model output, frequency table, or embedding may influence the
candidate set or any choice.

## Data and sampling

- Before any B1-L/B2-P selection, kill, or practical-effect decision, admit BUS-BRA plus at least two independently
  admitted semantic-breadth source families with prospectively assigned development and held-out-family roles.
  BUS-BRA alone is non-promotable engineering evidence. BBBC039 may be used only for capped non-promotable
  geometry/count wiring smoke. BBBC038 is a post-selection heterogeneous stress source and cannot satisfy the semantic-
  family minimum.
- Split duplicate/patient/study/specimen/source-parent groups before view expansion.
- Hold out complete sources and complete prompt-template lineage families for development.
- Generate only deterministic views authorized by [the annotation lattice](ANNOTATION_TASK_LATTICE.md).
- Attach context targets only under the [context objective contract](CONTEXT_OBJECTIVE_CONTRACT.md): the exact field
  must belong to the run's versioned requested-field registry and have a source-authoritative value. Missing or
  non-requested fields remain masked unknowns; never infer them from source names, paths, prompts, or benchmark taxonomy.
- Normalize total optimizer loss mass per independent unit before source/task/context balancing. A unit with a mask,
  boxes, counts, and several derived views may not outweigh a global-label unit merely because it emits more views.
- Sample sources and task forms with prospectively fixed macro-balancing so a large source or easy classification route
  cannot define the optimizer.
- Count both views and independent units; promotion statistics resample independent groups.
- Treat closed-option views as secondary robustness data until an authoritative input contract says options reach the
  model.

## Geometry and output contract

Before any training run:

1. Prove every source geometry transform against golden corner, edge, single-pixel, multi-box, and inverse-round-trip
   fixtures.
2. Keep the final localization target in original-image pixel `xywh`, matching the observed task card.
3. Bind the model-visible image dimensions and processor resize/pad transform so the target frame cannot silently drift.
4. Use the exact card system/user suffix in the protocol-proxy condition, while clearly labeling it non-official until
   raw prompt bytes and runtime are available.
5. Train and validate the terminal JSON serializer; malformed committed JSON is locally incorrect and is never repaired.
6. Keep rationale handling explicit. Do not silently train answer-only targets and claim protocol equivalence when the
   visible card requests a concise rationale before the terminal object.

The default rationale policy is fail-closed: never generate a medical rationale from a class label, box, mask, or
metadata field. Records without an independently source-supported rationale use an explicitly named
`answer_only_training` target and cannot support a rationale-quality claim. A separate rationale-bearing condition is
eligible only when the exact source text, derivation authority, rights, and answer consistency pass admission;
model-generated rationales and label-to-template explanations are ineligible. Prompt-format robustness must be measured
at development time, but the lack of a final context prompt does not block a task-independent native
load/forward/export preflight.

## Optimizer and preservation controls

- Use AdamW for the competition-strength shared-LoRA baseline; do not handicap the primary entrant to preserve a
  research-method invariant.
- Treat answer-task loss and available authoritative context-field losses as co-primary endpoints under the
  [context objective contract](CONTEXT_OBJECTIVE_CONTRACT.md). Mask unavailable
  fields, report each field separately, and freeze their aggregation before results; a gain in one endpoint may not
  conceal a material loss in the other.
- Freeze the vision tower initially. Adapt the projector and late language modules only in a prospectively fixed profile;
  unfreezing or vision-side adaptation requires a native feasibility result and a held-out-source gain.
- Ordinary `recipe_arch::B2-P` and `recipe_arch::B2-F` use **no KL or preservation loss**. This no-KL form is the
  primary B2 baseline. An unconditional frozen-coefficient KL/base-behavior-retention condition is a separate post-B2
  control on a prospectively eligible admitted non-public preservation pool; do not call unlabeled behavior retention
  correctness preservation. Base-conditional preservation is a second, separately identified post-B2 candidate under
  A4. Neither control may replace or retroactively redefine ordinary B2.
- Record base-relative negative flips, not only aggregate accuracy.
- Early stopping and checkpoint choice use only the frozen development populations and registered decision rule.

## Visual-dependence safety gate

For every applicable task and source, evaluate the same checkpoint under:

- normal image;
- deterministic blank/no-image control permitted by the model interface, as a descriptive shortcut alarm only;
- answer-preserving visual interventions whose target invariance is proven from the source contract;
- answer-changing paired images for which the identical generic prompt is valid and each image has its own authoritative
  source target; and
- separate answer-preserving overlay jitter and answer-changing source-annotated region pairs for grounded tasks.

Report normal competence, blank/no-image behavior, answer-preserving invariance, answer-changing target tracking, and
grounding sensitivity with independent-unit intervals. Never reward a larger normal-minus-blank gap: it can grow merely
because the blank input became more destructive. The gate is conjunctive—normal competence, invariance where the target
is preserved, and target tracking where source-authoritative evidence changes must each pass. An inapplicable probe is
reported, never imputed. These are development diagnostics, never relabeled biomedical examples.

## Optional ablations, not backbone claims

### A1: numeric-distance auxiliary loss

For counting and pixel-coordinate tokens, a tokenizer-aware ordinal/numeric auxiliary loss may be compared with ordinary
cross-entropy. It is rejected before training if the tokenizer cannot expose a stable numeric representation or if the
loss changes the official serialized target. This is adjacent to numeric-token regression and Pix2Seq-style coordinate
modeling; it is not claimed as novel.

### A2: text-prior-aware example weighting

Frozen-base normal-versus-blank target log-probability may define a preregistered training weight. This is a bias-model
reweighting ablation, not a new method. It is retained only if it improves held-out-source performance and visual
dependence without losing macro-task performance.

### A3: frozen specialist vision encoder

The rules permit multiple vision encoders inside one end-to-end VLM when all active parameters are counted. After B2
has native resource and package receipts, the exact [multi-encoder branch](MULTI_ENCODER_BRANCH.md) may compare B2
against a frozen native-plus-specialist pair. A duplicate-native-encoder control is mandatory. This is killed by an
unresolved loader, release, memory, latency, source-family, or state-dict closure result and is not method novelty.

### A4: base-conditional preservation

After ordinary no-KL B2 is frozen, compare the separately identified unconditional-KL control and then the exact
[base-conditional preservation ablation](BASE_CONDITIONAL_PRESERVATION.md) may preserve frozen-base behavior only on
admitted external records with deterministic correct-and-valid receipts, while learning authoritative targets on base
errors. A shuffled gate, token-exposure control, visual-dependence gate, and negative/positive-flip report are mandatory.
This is adjacent to S3FT, distillation, and margin-preserving negative-flip training; it is not method novelty.

### Grounding-preservation boundary

In one Qwen2.5-VL/data-mixture study, answer-only medical VQA adaptation destroyed box emission; shuffled-box format
rehearsal restored formatting without localization; and limited real grounding restored IoU while retaining the
authors' SLAKE answer gain, while their VQA-RAD open-recall result and limitations prevent universal generalization
([Chen et al., 2026](https://arxiv.org/abs/2604.27720)). Backbone/recipe-matched QLoRA VQA-only versus multitask
medical-VLM comparisons—not demonstrated fixed-record, fixed-token, or fixed-unit-mass matches—and joint
VQA/explanation/grounding LoRA also directly occupy the broad co-training claim
([Safwan et al., 2026](https://arxiv.org/abs/2607.27122), [Safwan et al., 2025](https://arxiv.org/abs/2511.04384)).
Therefore a prospectively matched grounding-preservation arm is motivated only where eligible source-authoritative
annotations exist; it does not redefine ordinary B2. Any such arm needs a full-image no-crop baseline and separate
answer/localization reporting. Oracle crops or box-format rehearsal cannot establish grounding.

### A5: fixed weight interpolation

After ordinary B2 is frozen, the [weight-interpolation branch](WEIGHT_INTERPOLATION_BRANCH.md) may compare only
`alpha = 0.60, 0.80, 1.00` for the effective learned delta. Coefficients are fixed before results, adapter-gauge and
export equivalence must be proven, and the final artifact remains one native model or organizer-approved adapter. This
is WiSE-FT-style competition engineering, not novelty.

### A6: canonical label-emission control

After ordinary B2 is frozen, the [label-emission-gap protocol](LABEL_EMISSION_GAP.md) may compare raw admitted source
labels with one prospectively reviewed canonical label for the same source concept. The comparison must keep images,
independent units, task/context mass, updates, active parameters, and compute matched. A source-authorized ontology
readout may diagnose whether the model recognizes a concept that free generation fails to express, but it is never an
inference component or a promotion endpoint. A synonym/equivalence-set objective remains disabled until its objective,
length treatment, canonical-output anchor, and unit-mass accounting are frozen and tested. No MMBU public example,
option, answer, output, frequency, embedding, or error bucket may define the vocabulary.

This optional control is motivated only by the open free-generation task interface, established open-answer research,
and ontology mapping that may be required by an admitted external source. No MMBU public example, output, score,
participant report, or metadata revision can create or prioritize it. Canonical-label SFT is competition engineering,
not a learner-method novelty claim.

### Rejected by default

- attention/attribution penalties, unless a frozen-base pretest shows that the chosen attribution actually predicts
  grounded correctness;
- source-erasure/null-space updates, unless within-modality source is linearly decodable and erasure preserves task
  information;
- custom inference routers, repeated test-time adaptation, and prompt ensembles;
- any selection based on public MMBU behavior.

## Promotion rule

Use shared paired group-bootstrap resamples across candidates. Development roles choose exactly one promotion candidate
and freeze its checkpoint plus the checkpoint of every member of its declared comparator closure. Open untouched
`recipe_confirmation` once for those exact artifacts and the deterministic promotion rule; a failed candidate does not
authorize trying the runner-up on the same population. The
promoted checkpoint must simultaneously:

1. first clear the frozen positive practical task-gain floor over the same immutable base, then clear its
   candidate-specific comparator set by the frozen practical margin on the preregistered macro-source
   `S_proxy = (0.8 T_proxy + 0.2 C_proxy)(T_proxy - T_base_proxy)` contrast: B1-L versus B0; B2-P versus B0 and B1-L;
   B2-F versus B0 and every enabled simpler shared-LoRA candidate. If an authoritative context proxy is unavailable,
   require robust dominance across the prospectively frozen admissible `C_proxy` range or return `no_selection`;
2. introduce no material task, source, context, open-answer, malformed-output, or base-preservation regression;
3. pass the visual-dependence lower-bound gate;
4. fresh-load twice from an immutable artifact in clean network-denied environments;
5. meet measured hardware, runtime, memory, token, and artifact limits; and
6. remain inside the exact allowed loader/package contract.

If the promotion candidate fails, return `no_eligible_candidate`; do not promote a different adapted model from the
same confirmation opening. B0 is a release fallback only if the rules permit it and it independently passes every
mechanical and release gate. Any adapted fallback requires a new untouched confirmation population. Complexity and
novelty do not receive challenge credit.

## Honest current rating

| Axis | Score / 10 | Ceiling under current evidence |
|---|---:|---|
| Competition design | **8.6** | Context semantics, literal scientific freeze packet, admitted data, full B2 run, and official loader are absent |
| Challenge alignment | **9.4** | Hidden distribution and unresolved context/evaluator/runtime |
| Learner-method novelty | **2.0** | Deliberately combines established best practices |
| Implementation readiness | **8.5** | B1/B2-P and the exact answer/context unit-mass objective execute natively; the verified reference uses singleton accumulation because heterogeneous concatenated-batch equivalence failed; source admission, scientific literals, full trainer, and official loader remain |
| Empirical evidence | **3.6** | Native synthetic answer/context optimizer behavior is measured, but no admitted-biomedical baseline, ablation, or competition result exists |

The route to 9.5 competition readiness is evidence, not another acronym: admit data, extend the verified B2-P mechanical
path into a complete singleton-reference answer/context trainer, repair or explicitly retain the failed heterogeneous-batch boundary, freeze literal scientific choices, run the B0/B1/B2 comparison, preserve
image reliance, package the winner, and rehearse the official load path.
