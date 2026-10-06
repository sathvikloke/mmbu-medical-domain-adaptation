# MMBU plan audit

October 3, 2026. Scope: the first competition plan and the primary sources underlying it, followed by review of the revised plan. This report assesses a proposed research program, not a trained model.

**Initial verdict: substantive plan repairs required.** The scoring arithmetic and broad research direction survive review. The most consequential problems are conflicting official evaluation instructions, premature base selection, and a validation set assigned incompatible selection/confirmation roles. The first plan was useful strategic direction but did not yet justify binding model-selection or large training decisions.

**Current decision:** use [revision 2](/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/MMBU-domain-adaptation-plan-v2.md) for preparation and gated pilots. Organizer clarification and actual resource measurements remain prerequisites for definitive score comparisons and scaling. No audit establishes a probability of winning. Model performance, dataset cleanliness, GPU fit, and throughput remain unmeasured.

**Review process and evidence boundary**

Three separate reviewer agents received raw artifacts in isolated contexts: a 16-pass forensic auditor, a model/data reviewer, and a statistics/resources reviewer. The original author separately checked source availability and recomputed material quantities. The forensic reviewer was then asked to check repairs, and a further adversarial review challenges the audit conclusions. These are model-assisted reviews from the same underlying model family, not independent empirical replications or human biomedical review. Later reviews necessarily see the revised artifacts and prior findings.

The initial forensic audit returned `REPAIR_REQUIRED`, completed 16 named passes, and investigated six additional failure classes. It opened three stable ledger entries: DEF-0001 through DEF-0003. The specialist reviewers supplied five DATA findings, including one optional extension, and seven STAT findings. These overlap substantially; they are not fifteen independent defects. A second full forensic review closed the original three entries and found a precision-wording regression (DEF-0004). A focused check closed that correction. The fresh red-team reviewer then challenged incomplete regression coverage and identified DEF-0005, which was restored and checked. The consolidated findings below avoid counting the same root cause repeatedly.

The SENTINEL executable was absent: `sentinel verify` and `sentinel ledger --json` returned the equivalent of exit 127. Hashed local receipts and the reviewer’s structured ledger were used instead. No SENTINEL controller hash-chain integrity or parser-accepted certification is claimed.

| Evidence | What was inspected | Limit |
|---|---|---|
| Frozen original plan | Complete text, numbered lines, SHA-256 | Prospective proposals only |
| Official challenge brief | Full PDF text, compared with supplied extraction; independently refetched identical PDF | No organizer clarification of document precedence |
| Official public dataset card | Publicly visible HTML and public repository API metadata | Gated records/images not accessed; raw README returned 401 |
| Acceptance email excerpts | User-supplied deadline and resource statements | Sender authenticity not independently authenticated |
| MMBU paper and cited model/data/trainer sources | Relevant tables, methods, model cards, annotation and access descriptions | Published results not independently reproduced |
| Arithmetic and counterexamples | Independent calculations, date conversion, allocation sums, scoring fixtures | Synthetic illustrations are not model results |
| Revision 2 | Revised decision rules and dependencies | Their future implementation remains untested |

The frozen original-plan hash is `a2ee7b1dfe0882e1f4db3a6578733479aca74ffd86b04eb6d7aa0cbe5f1b23db`. The refetched brief hash is `72589a77da294da10e1e953b7bc93c62fc3d511685bdd290a0f046f67348d362`. The observed public-dataset revision is `069da7bbd6201a867039b548f3c02e103711ed4a`.

**Central claims and decisions**

| Claim | Evidence status | Decision |
|---|---|---|
| The challenge rewards task/context quality multiplied by task improvement over the actual base | Supported by the brief; formula and examples independently checked | Retain |
| Qwen2.5-VL-7B is the best base for this team | Not established; no team pilot exists | Retain only as an engineering starting point |
| Better visual supervision and vision-component adaptation are promising | Plausible hypothesis, supported indirectly by published failure patterns | Test against a simpler baseline; do not call the gain demonstrated |
| The first plan fixed the correct output/grading contract | Contradicted by unresolved differences between official sources | Obtain precedence and pin the executable protocol |
| A locked finalist-selection set also supplies independent confirmation | Not supported as specified | Separate those roles |
| The timetable and proposed dataset scale fit our resources | Not assessable without actual access, costs, throughput, and people | Replace unconditional milestones with measured gates |
| A successful audit validates model quality or a winning chance | Unsupported | Explicitly exclude this conclusion |

**Consolidated findings**

| ID and reviewer mapping | Type / severity / confidence | Evidence and consequence | Repair and status |
|---|---|---|---|
| **AUD-01** — DEF-0001, DATA-04, part of STAT-04 | Verified source conflict / high / high | Original lines 101–111 prescribe task rationales inside JSON. The public card instead places rationale before committed answer JSON and differs on malformed-output grading. Its multi-label output instruction also conflicts with the shown one-concept judge. Exact final behavior is unknown. | Revision 2 records the conflicts, separates model/judge inputs, and prevents premature official-equivalence claims. **Plan handling repaired; governing protocol remains an external dependency.** |
| **AUD-02** — DEF-0002, STAT-01 | Conflicting prospective design roles / major / high | Original lines 79, 190 and 243 use locked validation for finalist choice and independent confirmation. Selection on that set invalidates a naïve independence claim even if no weights are retrained. No actual leakage occurred because no experiment occurred. | Revision 2 selects and freezes on development data, opens confirmation once, and retires it if its result influences further changes. **Design repaired; execution unverified.** |
| **AUD-03** — DATA-01, STAT-05 | Experimental sequencing gap / major / high | Original lines 50, 56, 142–143 and 181–182 choose a base after language-only SFT, before testing visual adaptation. This can select for the wrong training recipe; a short-run order also need not persist. | Retain two candidates through a bounded visual probe and compare exposure/cost learning curves. **Design repaired; model ranking still unknown.** |
| **AUD-04** — DATA-02 | Missing operational diagnostic / moderate / high | Original line 142 says verify images are present and used, but does not define a perceptual-use test. Scores can improve through text priors or response behavior. | Add external correct/mismatched/no-image and answer-changing-image diagnostics. **Specification repaired; no perception improvement demonstrated.** |
| **AUD-05** — DATA-03, STAT-06 | Data-feasibility and measurement gap / moderate / high | Original lines 120–136 set an ambitious record envelope and sampling mix without accepted source/task yields or a precise verification/weight denominator. Existing provenance safeguards are real and were not ignored. | Stage 200–500 engineering records, then 2,000–5,000 pilot records; define conversion QA, record-draw exposure, token loss, independent-group counts and source acceptance. **Plan repaired; source acceptance and label quality remain unverified.** |
| **AUD-06** — STAT-02 through STAT-04 | Decision/inference specification gap / major for close selection / high | Original lines 91–97 request robust diagnostics but do not fully define weighting, dependence hierarchy, or what happens when judge/mixture uncertainty reverses rankings. These are risks to future decisions, not measured bias in existing results. | Define task/source weights, pooled-score recomputation, paired entity/source analysis, blinded base-and-adapted judge review, and unresolved-ranking outcomes. **Design strengthened; calibration and precision require data.** |
| **AUD-07** — STAT-07 | Feasibility verification question / potentially major / high about missing facts | Original line 7 explicitly marks resource assumptions unknown. The first two weeks offer only 50–80 assumed person-hours. This is not proof the plan is infeasible, but it cannot support a committed run queue. | Measure training, both inference passes, grader, export and human QA cost; preserve reserve and reduce scope when gates fail. **Dependency now operational; feasibility still unverified.** |
| **AUD-08** — DEF-0003 | Metric wording ambiguity / minor / high | Original line 17 averages C over images; the brief averages over examples. Repeated-image external datasets can differ. No discrepancy was demonstrated on the public release’s stated one-row-per-image structure. | Revision 2 uses the example population and includes unequal-multiplicity and unequal-field fixtures. **Definition repaired.** |
| **AUD-09** — DEF-0004 | Revision regression / minor / high | The first revision-2 draft replaced explicit BF16/FP16 requirements with ambiguous “full-precision” terminology. | Published non-quantized BF16/FP16 requirements restored at load/export gates and separated from future amendments. **Focused closure verified.** |
| **AUD-10** — DEF-0005 | Revision and audit-coverage gap / moderate / high | The red team found the revised plan had compressed away explicit full-component parameter counts, separate context inputs, no carried state, no auxiliary systems/tools, and raw-output preservation. The first follow-up audit missed these omissions. | Restored a submission-requirements checklist and separate task/context/judge builders. **Challenge upheld; repair inspected by the red-team reviewer and recorded in the final ledger.** No actual submission violation was established. |

**Optional extension, not a blocker:** DATA-05 recommends a small, allowed-resolution comparison when tiny-object errors persist. The old plan already checked geometry, memory, and native processing; the reviewer did not establish resolution failure. Revision 2 includes this targeted diagnostic without adding a broad search or a submission-time cropper.

**The most important new source finding**

The [public dataset card](https://huggingface.co/datasets/mmbu/mmbu-public) states 3,147 rows, and its API lists 3,147 image files. The card is readable while the examples require access acceptance. The container’s `train` split name does not settle permitted challenge use. The [brief](https://akiranishii.github.io/mmbu-challenge/MMBU_challenge_update.pdf) remains byte-identical to the version used for the original plan; therefore its disagreement with the card is a current source conflict, not a silently corrected old download.

We should clarify rationale placement, invalid-output handling, multi-label grading, and the context-pass implementation before training to a final serialization target. This does not prevent source screening, independent external-data work, native model loading, or reversible engineering diagnostics.

**Why the perception hypothesis needs a control**

MMBU Table 8 reports OctoMed open ungrounded F1 of 0.070 with images and 0.077 without them. This is descriptive evidence; without a paired uncertainty analysis it does not prove that removing images improves the model. It does show why earlier adaptation scores alone cannot establish that the image is being used effectively. [MMBU Table 8](https://arxiv.org/html/2606.06696v1#S9)

The corrective experiment should preserve the question while changing relevant visual evidence on reviewed external fixtures. A successful pipeline loading images is necessary, but not sufficient, for a perception claim. These controls supplement honest task-performance reporting; a format improvement can be useful without being mislabeled a visual breakthrough.

**Source screening findings worth carrying forward**

- [ROCOv2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11208523/) supports modality supervision and selected context labels; captions/concepts are not a general source of pixel-level lesion annotations.
- [Chest ImaGenome](https://physionet.org/content/chest-imagenome/1.0.0/) has anatomical boxes and many automatically derived relations. An anatomical region box attached to an observation is not automatically a lesion-localization label. Access and release compatibility must be checked; no violation has been demonstrated.
- [BBBC039](https://bbbc.broadinstitute.org/BBBC039) is a concrete small microscopy source with instance nuclei masks and parent-collection overlap. [BBBC041](https://bbbc.broadinstitute.org/BBBC041) has labeled cell boxes but a different license and strong class imbalance. Neither is automatically cleared for this challenge; they illustrate why source-specific screening beats a generic “use BBBC” instruction.
- [The cited RL study](https://arxiv.org/abs/2603.01301) supports testing SFT before RL, but its experimental setting is not proof of benefit on open-ended MMBU localization.

**Independent arithmetic checks**

All values below are recomputations or synthetic examples, not team performance estimates.

| Check | Result | Interpretation |
|---|---|---|
| Original score examples | 0.104 and 0.062 | Correct |
| Score derivatives | Finite differences agree with 1.6T + 0.2C − 0.8T_base and 0.2(T − T_base) | Correct |
| Original allocation lists | Both total 100% | Correct; training-draw semantics still needed clarification |
| Deadline conversion | Jan 1, 2027, 12:00 UTC / 06:00 Chicago | Correct given the user-provided AoE deadline |
| Example-versus-image C | Nine positive rows on image A and one negative row on image B: 0.9 versus 0.5 | The unit matters |
| Example mean versus field pooling | One perfect single-field example and one six-field all-wrong example: 0.5 versus 1/7 | Pooling annotated fields changes the metric |
| Pooled nonlinear score versus mean source scores | 0.12 versus 0.09 in the same two-source toy | Reweight aggregates before computing the product |

The last row uses equal source weights, T=C=(0.9, 0.3), and base T=(0.8, 0.0): pooled T=C=0.6 and base T=0.4 give S=0.12; the individual source scores are 0.09 and 0.09. These explicit inputs are also preserved in the final evidence receipt. The forensic report's separate 0.075/0.060 illustration is not this fixture and is not needed to support the conclusion.

A source-mixture counterexample illustrates ranking uncertainty:

| Synthetic source-1 weight | Candidate A score | Candidate B score |
|---|---:|---:|
| 80% | 0.20592 | 0.15088 |
| 20% | 0.08352 | 0.18688 |

The underlying source-level performances do not change. Candidate A uses source-level base/adapted T pairs (0.20, 0.60) and (0.70, 0.75); B uses (0.50, 0.70) and (0.20, 0.55). Both have C=0.60. This proves only that a mixture shift can reverse a ranking, not that these models or the hidden set will do so.

A judge-bias counterexample uses a common base T=0.4 and C=0.6. True adapted T=0.600 gives S=0.12000; T=0.605 gives S=0.12382. If only the first candidate receives an optimistic 0.01 error in graded T, its apparent S becomes 0.12768, reversing the order. Review must therefore include the base as well as every adapted contender. A common judge does not guarantee cancellation.

Even zero observed errors among 200 independent identically distributed grading checks gives a one-sided 95% binomial upper error bound of about 1.49%. That is an illustrative precision calculation, not the actual error rate or a valid interval for our unobserved clustered audit sample.

**Coverage of the 16 forensic passes**

| Pass | Actually checked | Coverage / remaining limit |
|---|---|---|
| 1. Objective/scope | Plan against charter, claims versus proposed work | Checked; no claimed training result |
| 2. Inputs/schema | Brief, public card, routing, coordinates, output contract | Finding AUD-01; gated records/harness unavailable |
| 3. Arithmetic/invariants | Scores, derivatives, allocations, dates, averaging fixtures | Selected quantities reproduced |
| 4. Executed path | Hashes, artifact times, original versus frozen plan | Plan provenance checked; no model path exists |
| 5. Verification strength | Parser/averaging/selection counterexamples and E00 design | Design weaknesses found; no production tests claimed |
| 6. Stale descendants | Affected split, calendar, output and release sections | Initial follow-up missed submission constraints; red team caught AUD-10 and checked restoration |
| 7. Provenance | Input hashes, refetched PDF, dataset revision, email provenance | Checked; source text is not empirical replication |
| 8. Leakage/independence | Grouping rules, training/selection/confirmation flow | AUD-02; no actual leakage demonstrated |
| 9. Permissions | Proposed versus executed account, data and communication actions | No purchases, sends, account acceptance, or gated download |
| 10. Resources | Assumptions, percentage budgets, proposed profiling | Feasibility not assessable until measured |
| 11. Edge cases | Invalid/missing output, field counts, repeated images, zero fields, task suffixes | Design checks; actual harness unresolved |
| 12. Claims/evidence | Primary model/data/trainer/paper assertions | Material claims checked; performance not reproduced |
| 13. Reproduction | Proposed clean environment, revisions, manifests, exports | Described, not executed for a model |
| 14. Domain checks | Paired adaptation, visual annotation semantics, source shift, precision, component counts | Precision caught in follow-up; parameter-accounting restoration required the red-team challenge |
| 15. Additional failure classes | Split-name permission confusion, judge-only option leakage, multi-label conflict, zero fields, literature-metric substitution, source updates | Six investigated; no hidden-data access |
| 16. Closure | Stable DEF ledger and revision consistency | See post-repair disposition below |

**What to do differently now**

The first investment is protocol certainty and a functioning training/evaluation/export loop. Start with hundreds of engineering examples and a few thousand pilot records, not a presumed clean 20,000-record corpus. Keep two models through the visual-adaptation probe. Spend subsequent effort on the specific visual errors and sources that survive quality review. Preserve one-time confirmation and a non-quantized BF16/FP16 deliverable from early in the project.

**Post-repair disposition**

The full follow-up audit closed DEF-0001–0003 and opened DEF-0004. A precision-only closure returned a scoped PASS at plan hash `5b08aa049724426d48d1885a44f5496ed22b0637dac5d282a6e9889e877a62ac`, carrying forward the prior 16-pass coverage; it was not another full audit. The red team then returned CHALLENGE on incomplete regression coverage. That challenge is upheld against the original plan and the brief, recorded as DEF-0005, and repaired. The red-team reviewer directly inspected the restoration at final plan hash `7e4997da8fef7614ad057bbd910c15a585d354e7f2036cc6be8bd659f5afbe64`. The historical PASS does not certify this later file; the later restoration has its own focused review and adjudication.

The final manual ledger retains all five DEF keys and closes their document repairs. This means the identified planning defects were addressed, not that the competition entry is validated. External protocol, public-dev permissions, access, budget, reviewer capacity, calibration, and performance questions remain open. The appropriate next step is preparation and bounded engineering pilots, followed by comparison only when the required evidence and permissions exist.

Traceability limits remain explicit: the full initial forensic prose report was not archived, although its three stable ledger entries were retained; later complete reports and their hashes are archived. Separate synthetic illustrations were not interchangeable, and the report's principal nonlinear-score fixture now has explicit inputs. Eight historical source/artifact receipts matched on final recomputation. No gated example contents or trained-model results were verified. [Final evidence and defect ledger](/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/MMBU-audit-evidence.json)
