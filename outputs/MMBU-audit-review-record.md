# MMBU audit review record

October 3, 2026. Historical reports followed by final adjudication. Their statuses refer to the artifact versions described within them. This record does not contain the unarchived full initial audit or verbatim specialist reviews; their findings are consolidated in MMBU-plan-audit.md.


---

## Full follow-up forensic review

SENTINEL_AUDIT_STATUS: REPAIR_REQUIRED
AUDIT_PASSES_COMPLETED: 16/16
UNKNOWN_UNKNOWN_FAILURE_MODES_CHECKED: 6
OPEN_CRITICAL_HIGH_DEFECTS: 0
OPEN_REPAIRABLE_DEFECTS: 1

DEFECT_LEDGER_JSONL_BEGIN
{"defect_key":"DEF-0001","severity":"HIGH","category":"conflicting-official-contracts","status":"CLOSED","blocking":"BLOCKING","evidence":"MMBU-domain-adaptation-plan-v2.md:11-24 pins the public revision, enumerates rationale, malformed-output, multilabel, and context-contract uncertainties, and explicitly refuses silent precedence. Lines 32,117,166-171 gate official-equivalence claims and request authoritative clarification.","root_cause":"The original plan omitted conflicts between official sources.","repair":"Completed at the planning level. Organizer precedence remains an explicitly gated external dependency; its resolution is not claimed."}
{"defect_key":"DEF-0002","severity":"MEDIUM","category":"selection-versus-confirmation","status":"CLOSED","blocking":"BLOCKING","evidence":"MMBU-domain-adaptation-plan-v2.md:70 and 75 require one checkpoint and seed selected before confirmation, prohibit finalist ranking on confirmation, retain disappointing results, and retire the set after result-informed changes. E05 at line 122 and calendar lines 158-159 follow the same ordering.","root_cause":"The original locked set served both final selection and claimed independent confirmation.","repair":"Completed: development selection and one-time confirmation now have consistent roles and failure rules."}
{"defect_key":"DEF-0003","severity":"LOW","category":"metric-definition","status":"CLOSED","blocking":"NONBLOCKING","evidence":"MMBU-domain-adaptation-plan-v2.md:28 defines C over evaluation examples with within-example field averaging and preserves repeated-image rows. Line 83 gives the correct C=0.9 unequal-multiplicity fixture and defers zero-field behavior to the authoritative contract. Independent Python recomputation agrees.","root_cause":"The original wording substituted images for the official example-level averaging unit.","repair":"Completed: the averaging unit, repeated-image fixture, and unresolved zero-field policy are explicit."}
{"defect_key":"DEF-0004","severity":"LOW","category":"precision-definition-regression","status":"OPEN","blocking":"NONBLOCKING","evidence":"MMBU-domain-adaptation-plan-v2.md:48,117,128 repeatedly requires 'full-precision' loading/export but never names BF16 or FP16. The brief p10 explicitly specifies BF16 or FP16, and the frozen original plan named them at lines 101 and 152. A terminology search confirmed both dtype names are absent from v2.","root_cause":"Compression of the original release requirements replaced a concrete inference dtype requirement with an ambiguous phrase commonly associated with FP32.","repair":"Name BF16/FP16 explicitly in the inference/export gate. Describe QLoRA export as non-quantized BF16/FP16 rather than full-precision, and distinguish confirming future organizer changes from the already published dtype requirement."}
DEFECT_LEDGER_JSONL_END

## PASS-BY-PASS FINDINGS

1. **Objective, scope, and drift —** Read the charter and all 177 lines of v2. The document remains a prospective competition plan, explicitly disclaims trained-model evidence and winning probability, and replaces calendar-driven commitment with resource and evidence gates. No narrowing of the declared planning objective was found.

2. **Input, schema, and identifier integrity —** Re-read the public card’s task formats and judge gates. Recomputed the public API inventory: 3,147 distinct image filenames; revision and gating match the discovery summary. V2 correctly distinguishes that inventory from inspecting gated rows. Separate model/judge builders and an inference allowlist appear at line 111.

3. **Arithmetic, logic, and invariants —** Python verified both proposed task-weight vectors sum to 1, the repeated-image fixture gives C=0.9, and the AoE conversion remains correct. A nonlinear-mixture fixture produced S=0.075 from pooled T/C/base values versus 0.060 from averaging source scores, supporting line 38’s warning.

4. **Execution path actually taken —** Verified v2’s size and hash against its pre-audit receipt: 25,243 bytes; SHA-256 `f88eaf11eb59114333f6928dbe2083c9f165641e5c4b3f2f2bbda5491c540147`. The plan claims no completed execution. No training, evaluation, or access acceptance was performed during this audit.

5. **Test and verification strength —** Inspected E00–E05 and ran counterexamples for weighting, repeated images, token-length effects, QA sampling, and grading-sample bias. The proposed checks target plausible failures rather than merely successful parsing. Their future implementation is not certified by this review.

6. **Regression and stale descendants —** Compared v2 with the frozen original and traced each original defect into its dependent sections. All three repairs propagated into operational instructions and milestones. The comparison exposed DEF-0004: the explicit BF16/FP16 requirement became ambiguous “full-precision” wording.

7. **Data, state, and provenance —** Independently recomputed all five additional receipt hashes and sizes; all matched. The original plan remains at SHA-256 `a2ee7b1dfe0882e1f4db3a6578733479aca74ffd86b04eb6d7aa0cbe5f1b23db`. Reinvoking `sentinel verify` confirmed the executable remains unavailable, equivalent to exit 127. No parser acceptance or hash-chain integrity is claimed.

8. **Leakage, circularity, and false independence —** Checked lines 64–83, 101, and 111. The confirmation rule now prohibits selecting checkpoints or seeds using confirmation results. Group lineage, near duplicates, crops, alternate encodings, and judge-only input separation are explicit. Surrogate agreement is not presented as independent correctness.

9. **Security, safety, and permissions —** Searched v2 for credentials, destructive commands, hidden-set actions, uploads, purchases, and access acceptance. No secrets or executed unauthorized actions were found. Source eligibility is screened before ingestion; the document explicitly says it does not authorize resource purchases.

10. **Resource reality —** Read the revised cost gates and sprint. Costs include training, both inference passes, grading, preprocessing, export, and human review. The 15% compute reserve is explicit; elapsed dates cannot manufacture evidence or compress missed work. Actual costs, hardware, staffing, and review capacity remain unresolved dependencies.

11. **Failure and edge cases —** Checked absent task groups, zero metadata fields, candidate incompatibility, failed confirmation, malformed responses, missing labels, and source quarantine. V2 provides conservative behavior for these cases without inventing unknown official scoring rules. Mechanical fallback use requires a prewritten, score-independent rule.

12. **Claim ↔ evidence consistency —** Checked the new numerical literature claim directly against [MMBU Table 8](https://arxiv.org/html/2606.06696v1#S9): OctoMed open ungrounded F1 is 0.070 with images and 0.077 without. V2 correctly avoids interpreting that difference as statistical significance or a challenge-score prediction. Dataset file-count wording matches the independently recomputed API inventory.

13. **Clean-room reproducibility —** Walked the proposed ordering: pin contract, freeze bases, build manifests, compare matched pilots, select, confirm, then reproduce the exported artifact. This is a coherent plan for generating reproducible evidence. No executable pipeline or environment was supplied, so operational reproducibility remains future work.

14. **Domain-specific pass —** Revisited all charter lenses. Baseline conditions, visual-component probes, source clustering, label validity, detection versus classification, independent context evaluation, and adaptation-score weighting are addressed. The precision lens found DEF-0004. Contract precedence and context implementation remain expressly unresolved rather than silently assumed.

15. **Unknown-unknown pass —** Checked six additional failure classes against the revised rules:

   - **Record mixtures mistaken for loss mixtures:** equal draws with target lengths 1 and 99 contribute 1% and 99% of token-weighted loss. Line 105 explicitly accounts for this.
   - **Small QA samples mistaken for certification:** under an illustrative 1% error rate, 20 reviews miss every error with probability about 81.8%. Line 103 explicitly calls these operational starting counts, not error-rate guarantees.
   - **Targeted grading review mistaken for population error estimation:** a fixture with 2/20 random errors and 10/10 targeted errors yields a misleading combined 40% versus the random sample’s 10%. Line 83 requires separate reporting.
   - **Missing tasks silently renormalized into a full-task ranking:** line 40 prohibits full-proxy ranking when one of four task groups is absent.
   - **Image interventions interpreted as definitive perception proof:** lines 58–60 acknowledge blank-image distribution shift and text-answerable questions, and require answer-changing image pairs.
   - **Equal epochs mistaken for equal practical opportunity:** lines 49–51 require exposure and cost comparisons and reject a one-epoch winner as proof of a superior eventual ceiling.

16. **Closure —** Every prior key is retained and closed with concrete revised-line evidence. One new, nonblocking terminology regression remains open. Repair requires a small document clarification, not experiments or organizer permission.

## WHAT THIS AUDIT DID NOT COVER

This audit covers prospective plan coherence, not empirical model readiness. It did not inspect gated examples, hidden data, checkpoints, model outputs, an executable harness, measured throughput, or actual team resources. Email authenticity, future rule changes, and the correctness of a future implementation remain outside this audit. SENTINEL recording and parser validation were unavailable.

## REMAINING EXTERNAL DEPENDENCIES

The authoritative task/context contract, permitted public-dev uses, dataset access, hardware limits, available compute, spending ceiling, contributor hours, review capacity, and submission portal remain unconfirmed. V2 identifies and gates these dependencies adequately; they are not open planning defects.

## REPAIR INSTRUCTION

Replace ambiguous “full-precision” inference/export terminology with explicit **non-quantized BF16/FP16 under the confirmed organizer settings** at the relevant load/export gates. Preserve the distinction between the published dtype rule and any later organizer amendment. Keep all three closed defects closed and leave the original frozen plan untouched.


---

## Focused precision closure

SENTINEL_AUDIT_STATUS: PASS
AUDIT_PASSES_COMPLETED: 16/16
UNKNOWN_UNKNOWN_FAILURE_MODES_CHECKED: 6
OPEN_CRITICAL_HIGH_DEFECTS: 0
OPEN_REPAIRABLE_DEFECTS: 0

DEFECT_LEDGER_JSONL_BEGIN
{"defect_key":"DEF-0001","severity":"HIGH","category":"conflicting-official-contracts","status":"CLOSED","blocking":"BLOCKING","evidence":"V2 lines 11-24,32,117,166-171 retain explicit source conflicts, versioning, clarification questions, and gates on official-equivalence claims. Closure carried forward from round 1; affected precision wording does not change these protections.","root_cause":"The original plan omitted conflicts between official sources.","repair":"Completed at the planning level; organizer precedence remains an explicitly gated external dependency."}
{"defect_key":"DEF-0002","severity":"MEDIUM","category":"selection-versus-confirmation","status":"CLOSED","blocking":"BLOCKING","evidence":"V2 lines 70,75,122,158-159 retain selection before confirmation, prohibit finalist/seed selection on confirmation, and specify result-informed reuse consequences. These lines are unchanged from audited round 1.","root_cause":"The original locked set served both selection and claimed independent confirmation.","repair":"Completed; development selection and confirmation retain distinct, consistent roles."}
{"defect_key":"DEF-0003","severity":"LOW","category":"metric-definition","status":"CLOSED","blocking":"NONBLOCKING","evidence":"V2 lines 28 and 83 retain example-level context averaging, repeated-image handling, C=0.9 fixture, and explicit zero-field dependency. These lines are unchanged from audited round 1.","root_cause":"The original wording substituted images for evaluation examples.","repair":"Completed; the averaging unit and edge-case requirements remain explicit."}
{"defect_key":"DEF-0004","severity":"LOW","category":"precision-definition-regression","status":"CLOSED","blocking":"NONBLOCKING","evidence":"V2 lines 48,117,128 now explicitly require non-quantized BF16/FP16 loading/export. Line 171 distinguishes the published dtype requirement from other organizer constraints; line 128 records later amendments separately. A case-insensitive search found zero remaining full-precision mentions.","root_cause":"The revision replaced a concrete dtype requirement with ambiguous full-precision terminology.","repair":"Completed through four localized wording changes; verified against the published BF16/FP16 requirement."}
DEFECT_LEDGER_JSONL_END

## PASS-BY-PASS FINDINGS

This is a **focused closure check**, not another full audit. The 16-pass coverage and six failure-class checks above are carried forward from `round1-forensic-report.md`.

Passes 1–15 retain their prior findings. For pass 16 closure, I verified the four changed lines and reconstructed their previous wording **in memory**. The reconstructed file exactly matched the audited round-1 SHA-256, proving there were no additional changes:

`f88eaf11eb59114333f6928dbe2083c9f165641e5c4b3f2f2bbda5491c540147`

The repaired file’s SHA-256 is:

`5b08aa049724426d48d1885a44f5496ed22b0637dac5d282a6e9889e877a62ac`

All four ledger items are closed. No files were edited during this check.

## WHAT THIS AUDIT DID NOT COVER

PASS applies only to the prospective plan, using the prior full audit plus this verified localized closure. It does not establish empirical model readiness, resolve organizer precedence, confirm resources, or imply SENTINEL parser acceptance.

Remaining external dependencies are unchanged: authoritative evaluation contract, permitted public-dev use, authenticated access, hardware constraints, compute and spending capacity, reviewer availability, and submission logistics.


---

## Adversarial review

SENTINEL_REDTEAM_STATUS: CHALLENGE
OPEN_DEFECTS: 1
UNKNOWN_UNKNOWN_FAILURE_MODES_CHECKED: 6

## CHALLENGES

**DEF-0005 — Submission constraints lost during revision. Severity: MEDIUM.** Attacks round1 passes **6, 8, 14, and 16**.

The regression pass found the missing BF16/FP16 wording but missed these additional omissions:

- Full-component total/active parameter accounting: frozen v1 line 248; brief lines 350–360.
- Single end-to-end model, prohibited orchestration/tools, and restricted inference: v1 line 250; brief lines 364–377.
- Image-only context inputs and no state carried between passes: v1 line 106; brief lines 214–242.
- Raw-output preservation without unauthorized JSON repair, coordinate clamping, or repeated generation: v1 line 111.

Before restoration, v2 line 111 supplied a generic image/question input allowlist without explicit task/context separation. References to the “official harness” did not fully preserve these operational requirements. This is a document regression, **not evidence that an actual submission violated the rules**.

**Resolution:** Restore the constraints and record DEF-0005 with a focused closure. The newly restored v2 lines **111–124** address the identified omissions. I inspected that repair at SHA-256:

`7e4997da8fef7614ad057bbd910c15a585d354e7f2036cc6be8bd659f5afbe64`

The remaining open item is its audit/ledger adjudication. No experiments or organizer permission are needed to close this planning defect. Preserve the original round1 report as historical evidence.

## UPHELD FROM THE ORIGINAL AUDIT

The audit was substantive, although its regression coverage was incomplete. I read all sixteen pass descriptions and checked raw artifacts rather than accepting the synthesis alone.

- **DEF-0001:** Closure is justified at the planning level. V2 explicitly records source conflicts and gates official-equivalence claims. Organizer precedence remains unresolved; neither document claims otherwise.
- **DEF-0002:** Closure is supported by development-only selection, checkpoint/seed freezing before confirmation, retention of disappointing results, and retirement of confirmation data after result-informed changes.
- **DEF-0003:** Example-level averaging is repaired. Independent calculation reproduced **0.9 versus 0.5** for repeated-image weighting and **0.5 versus 1/7** for unequal metadata-field counts.
- **DEF-0004:** The reported precision regression was real. Current load/export instructions explicitly restore non-quantized BF16/FP16.
- **Arithmetic:** Python recomputation reproduced both source-mixture reversals, all three judge-bias scores, the **1.4867%** illustrative one-sided error bound, and **January 1, 2027, 06:00 Chicago**.
- **Raw-source statistic:** Independently parsed the API inventory: **3,147 unique image paths among 3,151 files**. This does not independently verify gated row contents.
- **Provenance:** Recomputed all five additional receipts and three original artifact receipts; all matched. The refetched brief is byte-identical to the original.
- **Literature quotation:** Parsed archived paper HTML and located Table 8’s OctoMed open ungrounded values, **0.070 with images and 0.077 without**. The plan correctly limits their interpretation.
- **Status and independence:** Round0’s three stable keys remain in round1; its sole recorded open defect is DEF-0004. The synthesis expressly identifies same-family model review rather than independent empirical validation. Reinvoking both SENTINEL commands reproduced executable absence, equivalent to exit 127.

## NEW FAILURE MODES

1. **Concurrent edits invalidate the artifact an audit certified.** Checked recorded and current hashes. The precision repair and subsequent constraint restoration produce distinct states. Historical audit claims must remain tied to their respective hashes; the newest text now needs its focused closure.

2. **An empty bootstrap ledger masquerades as zero unresolved defects.** `open-ledger.jsonl` is empty, but round1’s embedded ledger explicitly records DEF-0004 as open. I used the embedded ledger. No misleading zero-defect claim was established.

3. **HTML evidence is incorrectly attributed to an API commit.** The archived card HTML does not embed the API revision SHA. Its own hash preserves the observed content; the plan says “observed repository revision” rather than asserting a commit-bound card snapshot. No material overclaim found.

4. **Different synthetic fixtures are silently treated as one reproducible calculation.** Round1 uses pooled/averaged scores **0.075/0.060**, while the synthesis receipt uses **0.12/0.09**. These fixtures lack archived input tuples. This limits exact replay, but does not refute the conclusion: I independently reproduced nonlinear aggregation differences using explicit alternative inputs and reproduced the fully specified ranking fixtures.

5. **Missing historical reports conceal dropped findings.** The full round0 report is not archived locally. Stable-key comparison found no dropped DEF entries, but cannot establish that every prior prose concern survived. This is an explicit review limitation.

6. **A focused repair check inherits broader certification.** The precision-only closure cannot establish that newly restored submission constraints were reviewed. Its scope must remain distinct from round1’s sixteen-pass coverage and DEF-0005’s closure.

The challenge concerns audit completeness. Nothing checked supports claims of measured model readiness, resource feasibility, dataset cleanliness, or winning probability; the documents appropriately leave those unestablished.


---

## Final manual adjudication

# Final audit adjudication

Scope: prospective plan repairs, not model effectiveness or submission readiness.

The red-team challenge DEF-0005 is upheld. Frozen v1 and the brief contain explicit requirements omitted by the initial v2; generic references to the official harness were insufficient to retain them. Root restored the requirements and separate task/context/judge input builders. The red-team reviewer inspected the repaired text at plan SHA-256 7e4997da8fef7614ad057bbd910c15a585d354e7f2036cc6be8bd659f5afbe64 and found the identified omissions addressed. The final manual ledger therefore closes DEF-0005 and retains all earlier keys. No challenge is rebutted by reviewer authority or consensus.

DEF-0001 closure concerns handling the conflict in the plan, not resolving the governing contract. Organizer precedence, public-dev permissions, official evaluator details and resource capacity remain external dependencies. Later empirical calibration, training, inference and export checks remain unperformed work.

The precision-only PASS refers to its own earlier artifact. It is not broadened into certification of later edits. The latest change has this focused adjudication plus direct red-team inspection. No formal SENTINEL controller or parser validation exists.

The original full round0 prose report was not archived; stable-key preservation is inspectable but full prose-history completeness is not certified. The principal pooled-product toy now includes explicit inputs in the synthesis and evidence receipt. Historical reports are preserved unchanged.

