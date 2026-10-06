# Data review checklist

This checklist separates software checks from biomedical review and permission decisions. It does not certify any present medical record: real BBBC039 and ROCO samples have only undergone quarantined engineering inspection. Use `docs/data-contract.md` for the implemented validator's exact schema and limits. Eligible records use `review_status="approved"`, or `"engineering_reviewed"` only when both purpose and split are engineering. Other review states remain ineligible; source approval is a separate gate.

## 1. Source decision — before ingestion

- [ ] Source ID, family and version match the registry; evidence identifies the actual selected release/files.
- [ ] A named reviewer records the intended use, rights basis, downstream public-model conditions and allowed purposes. Candidate or quarantined entries remain ineligible.
- [ ] Credentialed access, data-use restrictions and service-sharing limits are resolved where relevant. Public documentation or a technical `train` split is not permission.
- [ ] Original split policy and MMBU-contributor overlap disposition are documented without inspecting or trying to identify hidden examples.
- [ ] Upstream collection, article/figure, patient/study, slide, field and experiment relationships are retained when available. Unknown grouping is explicit rather than a fabricated independent ID.

## 2. Mechanical checks — reproducible, not clinical certification

- [ ] Required IDs, versions, paths, SHA-256 values, split and permitted purpose pass validation; unsafe paths and duplicate IDs fail.
- [ ] Exact image, parent-image and group lineage cannot cross training, development and confirmation boundaries. Maintain transitive links and cross-source aliases.
- [ ] After legitimate acquisition, image decoding, channel/bit-depth conversion and displayed dimensions are checked by an appropriate image tool. A manifest validator alone does not establish image quality or visibility.
- [ ] Target serialization follows a versioned profile; nonfinite coordinates, out-of-frame boxes, wrong units and lossy transforms are rejected or quarantined without silently repairing predictions.
- [ ] Keep task, context and judge inputs separate. Reference answers, source metadata and judge-only choices do not leak to model inputs.
- [ ] Preserve counting, single/multi-label cardinality, instance identity and single/multiple boxes. Preserve region overlays under the confirmed convention.
- [ ] Log unique images, independent groups, source families and question records separately. Byte hashes cannot establish absence of perceptual duplicates.

## 3. Sampled conversion review — record the actual evidence

- [ ] Review at least 20 records from each new source/conversion combination initially, following the audited plan; log selected IDs and selection method.
- [ ] A critical mismatch (wrong image/region, wrong coordinate frame, answer leakage, or diagnosis inferred from an unlabeled mask) stops that conversion until repaired and rereviewed.
- [ ] Then review a random stratified batch, separating random-sample error rates from deliberately oversampled difficult cases. Record denominators, error classes, exclusions and disagreements.
- [ ] Set source/conversion-specific acceptance tolerances before bulk release. Sample review does not mean every unaudited item was individually verified.
- [ ] Retain automation results, sampled-review findings and biomedical sign-off separately. Use the implemented `review_status` vocabulary; put review detail in a linked review record.

## 4. Biomedical judgment — needs suitable expertise

- [ ] The answer is supported by the shown image and permitted question; no omitted caption, choices, history, laboratory values or article knowledge is needed.
- [ ] Mask classes mean what the question claims. An instance/foreground mask cannot justify a disease or phenotype label absent additional valid annotation.
- [ ] Anatomical-region boxes are not relabeled as lesion extents. Confirm complete versus partial instance annotation before deriving counts or negatives.
- [ ] Metadata has explicit annotation origin. Separate source-provenance facts from what can actually be inferred visually; preserve unknown and missing-annotation distinctions.
- [ ] Review laterality, specificity, negation, multi-label completeness, ambiguous/difficult labels, panel alignment and domain-relevant image preprocessing.
- [ ] Where expertise is unavailable, retain pending review status and exclude from medical optimization; fluent text is not expert validation.

## 5. Release and experimental use

- [ ] Freeze the accepted source/record manifest, conversion versions and review evidence before controlled comparisons. Record exclusions and realized task/source exposure.
- [ ] Protect locked confirmation examples from iterative tuning and training error mining; keep model baselines paired on the same allowed examples.
- [ ] Synthetic geometric fixtures remain `synthetic=true`, `engineering_reviewed`, split `engineering`, source `synthetic-fixtures`, purpose `engineering`. They never become medical training/evaluation records or evidence of perception gains.
- [ ] Resolve the protocol register before claiming official-score equivalence or committing schema-specific production training. Offline checks may continue under explicit diagnostic labels.
