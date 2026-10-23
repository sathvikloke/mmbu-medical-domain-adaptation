# Label-emission gap: competition upgrade, not novelty theater

**Date:** October 23, 2026  
**Evidence class:** published task interface, established open-answer literature, external source-ontology needs, and
prospective design only
**Decision:** retain one low-priority external-only diagnostic and ablation after the ordinary B2 baseline; do not
replace or delay B2

## Plain-language thesis

The model must **see the right biomedical concept, say it in an accepted vocabulary, and point to it when the task is
spatial**. A model that recognizes the concept internally but emits an off-ontology phrase can lose an open-answer row;
a model that memorizes the vocabulary without using the image can also look better while remaining unsafe. The project
must measure and improve both sides.

This is a competition thesis, not a clinical deployment claim. It is deliberately understandable: correct perception,
correct words, and correct location should agree.

## Independent reason to retain this optional control

The published benchmark interface includes open free-generation classification, while eligible external biomedical
sources can encode the same concept under abbreviations, spelling variants, ontology identifiers, or institution-
specific names. That creates a general measurement question independent of any MMBU example or participant output:
does the adapted model fail to perceive the source concept, or perceive it but emit a string outside the prospectively
reviewed external ontology?

This distinction is established in open-answer VQA and multi-reference generation research; it is not inferred from a
public challenge result. The control remains post-B2 and optional because no local admitted-biomedical evidence shows
that emission is a material failure mode. It becomes eligible only when an admitted external source requires a reviewed
ontology mapping for its own labels. A public MMBU example, answer, option set, output, error pattern, score, or dataset
revision can never create or prioritize this comparison.

Sources:

- [MMBU benchmark paper](https://arxiv.org/abs/2606.06696), used only for the general task/interface definition
- [Teney et al., CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/papers/Teney_Tips_and_Tricks_CVPR_2018_paper.pdf)
- [Hu et al., CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/html/Hu_Learning_Answer_Embeddings_CVPR_2018_paper.html)

## Competition decision

Keep ordinary `recipe_arch::B2-P` dual-objective training as the primary lane. Add the following only after an admitted
external development population and its ontology are frozen:

1. **Free-generation endpoint:** exact current serializer, with no answer options shown to the model.
2. **Ontology readout diagnostic:** rank a source-authorized candidate set on the same external unit. This is a
   diagnostic only and can never be used at challenge inference.
3. **Emission-gap estimate:** paired concept-correct readout minus free-generation concept correctness, reported by
   source, task, and answer length with independent-unit intervals.
4. **Canonical-emission arm:** train the same admitted units using one reviewed canonical target per source concept,
   keeping units, task/context mass, supervised-token budget, updates, active parameters, and compute matched to the
   raw-source-label control.
5. **Equivalence-set research arm:** eligible only if a reviewed concept has multiple genuinely equivalent authorized
   labels and a prospective objective is frozen. Alias count may not increase unit mass or create extra independent
   examples. This arm cannot delay the canonical-emission comparison.

The canonical vocabulary must come from source-authoritative annotations and a reviewed external ontology mapping. It
may not be learned from MMBU public questions, options, answers, outputs, label frequencies, embeddings, or error
buckets. The benchmark paper can define the task class only where the rules and repository firewall permit; it cannot
supply terminology, target selection, ontology coverage, or an example-dependent design choice.

## Matched comparison

| Arm | Target representation | Purpose |
|---|---|---|
| `LEX-A0` | admitted source label | ordinary B2 control |
| `LEX-A1` | one prospectively reviewed canonical label for the same source concept | test whether vocabulary control repairs free generation |
| `LEX-A2` | authorized equivalence class with one unit-mass-preserving set objective | research arm; test robustness to source nomenclature |

`LEX-A2` is disabled until its exact set objective, length treatment, canonical-output anchor, and gradient accounting
pass synthetic tests. Duplicating a row once per alias is not an acceptable implementation because it changes exposure
and rewards concepts with more recorded synonyms.

### Prior-art collision

`LEX-A2` is not a learner-novelty path. [Multi-reference training for translation and generation](https://aclanthology.org/D18-1357/)
already studies multiple human references and lattice-derived pseudo-references; [multi-referenced dialogue
training](https://aclanthology.org/2021.sigdial-1.20/) explicitly formulates the one-to-many target-distribution problem.
VQA systems have long optimized multiple synonymous correct answers with soft targets
([Teney et al., CVPR 2018](https://openaccess.thecvf.com/content_cvpr_2018/papers/Teney_Tips_and_Tricks_CVPR_2018_paper.pdf)),
and [semantic answer embeddings](https://openaccess.thecvf.com/content_cvpr_2018/html/Hu_Learning_Answer_Embeddings_CVPR_2018_paper.html)
directly address open-answer transfer across answer vocabularies. An exact generative set loss can still be a useful
engineering comparison, but its novelty score cannot come from accepting several equivalent strings.

Every arm uses identical images, independent units, split groups, prompt families, task/context allocation, optimizer
steps, trainable modules, and decision roles. Token counts must either be matched prospectively or included in a
separate exposure-matched sensitivity analysis. The primary estimate is paired `LEX-A1 - LEX-A0` on free generation;
the ontology readout cannot be the promotion endpoint.

## Conjunctive success rule

Canonical-emission training is useful only if all applicable conditions hold on untouched external roles:

- free-generation task performance improves by the frozen practical margin with a positive paired lower bound;
- the improvement is not confined to the local judge or exact-string normalization;
- normal-image competence and answer-changing target tracking do not regress;
- blank/no-image behavior does not explain the gain;
- context, localization, malformed-output rate, and base-relative negative flips stay inside their frozen bounds; and
- gains survive a held-out source vocabulary and a lineage-disjoint prompt family.

Retire the claim if the readout/free-generation gap is small, `LEX-A1` does not beat the matched control, or the gain
disappears under source-held-out evaluation. If canonical labels improve formatting but not source-held-out concept
accuracy, report a formatting result only.

## Human-impact boundary

The human-facing value is auditability: a reviewer can trace a generated label to one source concept and see whether a
failure came from perception, vocabulary, or localization. That can make biomedical model evaluation less misleading.
It does not prove clinical safety, diagnostic usefulness, or patient benefit. Those claims require clinical populations,
expert review, and deployment evidence that this challenge does not provide.

## Honest rating

| Axis | Pre-result score / 10 | Reason |
|---|---:|---|
| Competition fit | **8.0** | Fits the open free-generation interface but remains optional until an admitted external source creates an ontology-mapping need |
| Human explainability | **9.0** | “See it, say it, point to it” is concrete and maps failures to observable stages |
| System novelty | **4.0** | The matched diagnostic package is specific, but vocabulary normalization and readout/free-generation comparisons are established ideas |
| Learner-method novelty | **2.0** | Canonical-label SFT, multi-reference generation, VQA soft targets, and semantic answer embeddings occupy the mechanism |
| Current evidence | **1.0** | Only the task interface, external-ontology need, and established literature motivate the optional test; this project has no admitted-biomedical result |

This upgrade can raise competition value if it works. It does not honestly turn the project into a 9/10 learning
method. The strongest story remains a rigorously isolated, score-aligned system that makes perception, language, and
grounding agree rather than a new optimizer with an acronym.
