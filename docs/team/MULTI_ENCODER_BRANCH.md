# Multi-encoder competition branch

**Date:** October 17, 2026  
**Status:** optional post-B2 ablation; not approved for training  
**Claim class:** competition hypothesis, not method novelty

## Why this branch exists

The binding challenge contract permits multiple vision encoders only when they are components of one end-to-end VLM
and all active parameters are counted. MMBU reports that medical adaptation gains vary sharply by modality and that
all tested VLMs remain weak at object detection. A frozen biomedical specialist encoder could therefore complement the
native general encoder without requiring a router at inference.

This is not a new architecture family. [LEO](https://arxiv.org/abs/2501.06986) studies dual-branch vision encoders and
fusion; [MoVE-KD](https://openaccess.thecvf.com/content/CVPR2025/html/Cao_MoVE-KD_Knowledge_Distillation_for_VLMs_with_Mixture_of_Visual_Encoders_CVPR_2025_paper.html)
distills multiple visual encoders into one model; and
[METEOR](https://openaccess.thecvf.com/content/ICCV2025/html/Liu_METEOR_Multi-Encoder_Collaborative_Token_Pruning_for_Efficient_Vision_Language_Models_ICCV_2025_paper.html)
addresses multi-encoder token cost. Medical multi-scale and pixel-grounding systems such as
[Anatomy-VLM](https://openaccess.thecvf.com/content/WACV2026/html/Gu_Anatomy-VLM_A_Fine-grained_Vision-Language_Model_for_Medical_Interpretation_WACV_2026_paper.html)
and [MedPLIB](https://arxiv.org/abs/2412.09278) further remove any general claim that specialist/local visual features
are new.

## Candidate family

The branch may be instantiated only after one B2 profile has a native resource receipt.

- **V0:** promoted single-native-encoder B2 candidate.
- **V1-G:** two frozen copies of the native/general encoder with the same fusion path as V1. This controls for more
  visual tokens and parameters without specialist knowledge.
- **V1-S:** frozen native encoder plus one frozen biomedical specialist encoder. Train only one minimal fusion projector
  and the exact same language-side LoRA profile as V0.
- **V1-R:** native encoder plus a frozen randomly initialized shape-matched second branch, when technically feasible.
  This is a capacity/path control, never a competitive candidate.

No input-conditioned encoder selection, expert router, external service, cascade, crop tool, retrieval component, or
test-time adaptation is allowed in this branch. Both encoders receive the same submitted image in one forward pass.

## Fusion choices

Select exactly one before results:

1. **Token concatenation:** independently project both frozen token sequences to the language-model width, append fixed
   branch identifiers, concatenate in a fixed order, and expose the complete sequence to the native multimodal path.
2. **Grid-aligned residual fusion:** map specialist features onto the native patch grid using a fixed, documented
   geometry transform, project them to native width, and add a learned scalar-gated residual.

Token concatenation is the reference because it makes fewer unverified spatial-alignment assumptions. Residual fusion
is ineligible until corner/edge/single-pixel fixtures prove the token-grid map. A learned input router or dynamic pruning
would create a different candidate and is excluded.

## Admission gate for the specialist encoder

Before V1-S exists, record:

- immutable repository and weight revision, license, access status, and complete file hashes;
- pretraining sources and known overlap risks, without assuming an unavailable list is clean;
- accepted image modalities, resolution, normalization, patch size, output layers, token count, width, and dtype;
- total and active parameters under the challenge counting rule;
- exact wrapper/module ownership inside the one submitted model and a closed state-dict inventory;
- offline double-load with no network, remote code, auxiliary process, or hidden cache;
- native peak memory, load time, forward time, and visual-token count; and
- a modality-coverage rationale demonstrating that the branch is not a radiology-only shortcut presented as broad
  biomedical adaptation.

Any unknown field remains unknown. A model-card claim does not prove checkpoint closure or challenge compatibility.

## Matched experiment

V0, V1-G, V1-S, and V1-R must share admitted independent units, sampling, task views, prompts, targets, optimizer steps,
seeds, early-stop rule, language-side LoRA rank, and evaluation populations. Report two cost views:

- equal training examples and steps, showing the real cost of the extra encoder; and
- a compute-matched condition capped to V0's measured training FLOPs, showing whether gains survive equal budget.

The fusion projector's parameters are charged to V1. V1 cannot silently receive a larger language adapter, higher image
resolution, more augmented views, longer training, or additional source data. V1-G is mandatory: without it, a V1-S
gain cannot be attributed to biomedical specialization rather than duplicated capacity or tokens.

## Promotion and kill rule

V1-S is considered only after V0/B2 passes its own promotion and package gates. It is killed if any of the following is
true:

- the official loader/package contract does not accept the composite architecture;
- the specialist encoder lacks a redistributable, immutable, anonymously loadable release;
- V1-S fails fresh network-denied double-load or complete state-dict closure;
- peak memory, active parameters, artifact bytes, or latency exceed the official limit;
- it does not beat both V0 and V1-G by the frozen practical margin on macro-source performance;
- any gain is confined to the specialist encoder's source family or accompanied by a material task/modality regression;
- visual-dependence, malformed-output, base-preservation, or held-out-source gates fail; or
- the compute-matched advantage disappears.

There is no rescue search after the one-time untouched `recipe_confirmation` opening. A failure returns the project to
V0/B2 development and requires a new untouched population for any new promotion claim.

## Honest rating

| Axis | Score / 10 | Reason |
|---|---:|---|
| Competition upside | **7.4** | Complementary visual features could help spatial and long-tail modalities |
| Current competition readiness | **5.6** | No admitted encoder, module map, resource receipt, or loader confirmation |
| Method novelty | **2.6** | Multi-encoder VLMs, fusion, distillation, and medical multi-scale encoders already exist |
| Feasibility | **4.8** | Frozen encoders reduce training cost, but memory, token count, packaging, and redistribution are material risks |

The branch can improve the chance of winning only after the simple baseline is real. It cannot raise the project's
novelty score and may not delay B0/B1/B2.
