# MMBU CPU preparation — version 0.3

The useful CPU preparation identified by the research plan and independent coverage audit is implemented. This is an engineering milestone, not a trained entry or a competition result. The final base-model choice remains open: start with **Qwen2.5-VL-7B-Instruct**, test **Qwen3.5-9B** under matched conditions, and retain **Qwen3-VL-8B-Instruct** as fallback.

## Completed work

| Area | Verified outcome |
| --- | --- |
| Core software | 277 tests pass on Python 3.12/Pillow. Python 3.14 passes 233, with 44 explicit optional-image skips. Python 3.11 syntax checked; its runtime was unavailable. |
| Native processors | Exact cached revisions for three candidates; CPU template, image-grid and token checks. Real ROCO sample: 24 images × 3 models × 2 settings = 144 cases, each encoded twice. No weights, model forward, GPU or optimization. |
| Training-input checks | Explicit provisional task/context target serializers; assistant-prefix validation, prompt/image/padding masks and shifted-target guards. Synthetic loss accumulation agrees with combined-batch gradients; naive equal microbatch averaging does not. |
| Data preparation | 100 BBBC039 source-training fields with 198 pending count/box candidates; 24 ROCO source-training images from 24 articles across six modalities, with unchanged coordinate frames. |
| Source audit | Exact ROCO metadata joins and publisher checksums; 12,078 shared training PMCIDs with PMC-VQA. All 24 sampled articles have explicit CC BY version evidence; 22 captions link uniquely to figure IDs. Aggregate ROCO noncommercial terms remain a separate unresolved constraint. |
| Review and experiment controls | Exact/proposed perceptual duplicate checks; source/task mixture sensitivity; separate random/targeted judge calibration; pre-run artifacts; hash-bound confirmation lifecycle. |
| Einstein preparation | Read-only diagnostic and IT handoff. Local CPU dry runs never claim remote GPU readiness. |

All real records remain **pending** and all real sources have **zero allowed model-use purposes**. The ROCO training gate was executed and rejects all 24 rows. Article license metadata, structural QA and processor success are not legal clearance or medical-label approval.

## Findings that affect our approach

Qwen3.5's default thinking template does not share an exact token prefix with a plain-JSON assistant target. Explicitly disabling thinking resolves the tested prefix mismatch; the final generation policy still needs to match the official contract and paired baseline. All three native processors mishandle direct uint16 input in the tested paths, so raw microscopy data must pass through a reviewed explicit display mapping.

The loss probe confirms that averaging unequal microbatch means changes the intended token-weighted objective. Use the total shifted assistant-target token count across the accumulation window and verify the actual trainer once compute works. Preprocessor token counts are not GPU-memory measurements.

The data bottleneck is now clearer: usable annotations, figure lineage, display policy and permitted source use matter more than acquiring a larger unreviewed pile of images. ROCO images include visible arrows, acquisition text and other overlays that need deliberate review for shortcuts and identifiers. PMC-VQA metadata has malformed/conflicting answers and strong article overlap with ROCO; it should not be treated as an independent clean corpus.

Independent reviews closed concrete receipt, hashing, path-collision, response-framing, mask-shift, anchor and numeric-boundary defects. Reports retain the original counterexamples and the reviewed code hashes. Source revisions were rechecked October 4; the public material still does not resolve the official protocol conflicts.

## What now requires external evidence

1. **Einstein/IT:** actual allocated GPU, VRAM, driver/CUDA behavior, quotas and scheduler limits. Run `mmbu-precompute/tools/einstein_preflight.py` in that environment.
2. **Organizers:** authoritative task/context grading and formatting, public-development selection permissions, contributing-source policy and runtime constraints. The question draft is ready and has not been sent.
3. **Data review:** permitted-use/release decisions and suitable biomedical review of the pending examples. No automatic source approvals or invented clinical judgments were substituted.
4. **Actual experiments:** native BF16/FP16 load/forward/export, untouched baselines, matched pilots, repeat runs and an untouched confirmation result. These determine the winning candidate; software preparation cannot establish that ranking.

Start with [next actions](mmbu-precompute/docs/next-actions.md), [Einstein diagnostic instructions](mmbu-precompute/docs/einstein-preflight.md), and [organizer questions](mmbu-precompute/docs/organizer-questions.md). The original [audited strategy](MMBU-domain-adaptation-plan-v2.md) remains the research plan. Version 0.3 release verification binds the final portable archive and exact file manifest; earlier archives remain unchanged.

## Verified portable delivery

[Version 0.3 ZIP](mmbu-precompute-v0.3.zip) contains 276 files (275 individually hashed manifest entries plus the manifest). Clean extraction matched every file hash and passed seven command checks, including the eleven-test Einstein diagnostic suite. [Verification receipt](MMBU-precompute-v0.3-verification.json).

Archive SHA-256: `5c6b137f889ea3662fbe9a4934bad2884f67a3c5e51627f7cabdec40281398d4`. Archive size: 1,025,222 bytes. Earlier release ZIP hashes were rechecked and remain unchanged.
