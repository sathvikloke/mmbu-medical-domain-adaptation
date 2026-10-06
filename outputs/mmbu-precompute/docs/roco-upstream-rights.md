# ROCO shortlist: upstream article rights and figure provenance

October 4, 2026. Public PMC JATS metadata supplied explicit article-license URI/version evidence for **all 24 shortlisted training articles**: four CC BY 2.0, ten CC BY 3.0 and ten CC BY 4.0. **Twenty-two source captions uniquely match an article figure under strict normalization; two remain unresolved.** These findings do not approve model use or replace ROCOv2's aggregate CC BY-NC 4.0 declaration. Article licensing and figure-specific permission remain distinct.

The exact article IDs, article revisions, license URIs and XML locators, figure IDs, graphic references, timestamps and retrieval hashes are in [roco-upstream-rights.json](../evidence/roco-upstream-rights.json). [The offline verification receipt](../evidence/roco-upstream-rights-verification.json) checks every result directly against the captured XML. Raw XML and scripts remain outside the package at project-root `work/roco-upstream-rights/`. Portable receipts retain only useful HTTP date/type/encoding/length/last-modified/ETag headers; anonymous tracking and cookie headers are omitted.

## Retrieval method and scope

The [legacy PMC OA Web Service](https://pmc.ncbi.nlm.nih.gov/tools/oa-service/) was retired on August 25, 2026. This audit instead used the current [official OAI-PMH API](https://pmc.ncbi.nlm.nih.gov/tools/oai/), whose documented full-text format is JATS via `metadataPrefix=pmc`. Each request targeted one selected PMCID with `GetRecord`. The API permits three requests per second and prohibits concurrent requests; this script ran serially with at least 0.6 seconds after each response. The minimum observed request-start gap was **0.848935 seconds**.

All 26 requests—24 articles and two API documentation snapshots—returned HTTP 200. Recorded transfer bodies totaled **330,583 bytes**; decoded documents totaled **1,485,466 bytes**, below the 60 MB task bound. No images, bulk archives, heldout source labels, gated content, credentials or terms were requested. No access denial occurred. The acquisition script stops on explicit access/rate denial and does not switch retrieval paths.

## License evidence

Sixteen articles identify the primary license in `article-meta/permissions/license/@xlink:href`. Eight supply the explicit URI through the ALI `license_ref` element, with its `specific-use="textmining"` attribute preserved; several also contain matching links in the article's license paragraph. These locators and their different scopes are retained rather than treated as interchangeable evidence of a blanket image permission. HTTP/HTTPS and trailing-slash differences are preserved in the raw URI; a separately parsed canonical URI records the same license code/version.

Three articles—PMC4898465, PMC5543582 and PMC8404122—also mention a **CC0 data waiver** in their licensing text. This audit does not apply that waiver to the ROCO image or replace those articles' CC BY 4.0 statements with CC0.

No matched figure contained a separate `permissions` element or `attrib` credit element, and the matched captions did not trigger the limited rights-credit text screen. This absence is not proof that all third-party exceptions have been ruled out. The evidence remains an article-level rights declaration plus caption-linked figure provenance, not independent legal clearance of each image or downstream model release.

## Exact caption linkage

Normalization resolves XML entities, concatenates caption text in document order, applies Unicode NFC, collapses Unicode whitespace and trims the edges. It preserves case, punctuation, spelling, hyphens and words. It does not remove figure labels from arbitrary text, add punctuation at title/body boundaries, use fuzzy similarity, or interpret medical content. A source image receives a figure ID only when exactly one caption matches and that figure declares an ID. Graphic references are copied verbatim from the XML; their bytes were not retrieved or compared with the ROCO JPEG.

| ROCO training ID suffix | PMCID | Article license version | Caption-linked figure ID |
| --- | --- | --- | --- |
| 024386 | PMC7935576 | CC BY 4.0 | fig3 |
| 000571 | PMC3408669 | CC BY 3.0 | fig8 |
| 059923 | PMC8346277 | CC BY 3.0 | FIG2 |
| 047764 | PMC4312640 | CC BY 3.0 | fig6 |
| 040197 | PMC8336382 | CC BY 3.0 | FIG9 |
| 046920 | PMC4776813 | CC BY 3.0 | F4 |
| 003162 | PMC4783311 | CC BY 4.0 | Fig2 |
| 006911 | PMC6263494 | CC BY 3.0 | FIG6 |
| 045777 | PMC4912502 | CC BY 4.0 | Fig4 |
| 036012 | PMC2769440 | CC BY 3.0 | fig-003 |
| 011831 | PMC6478494 | CC BY 3.0 | Unresolved |
| 022485 | PMC4898465 | CC BY 4.0 | Fig1 |
| 049219 | PMC5543582 | CC BY 4.0 | Fig4 |
| 002716 | PMC7455822 | CC BY 4.0 | fig3 |
| 036451 | PMC1914059 | CC BY 2.0 | F1 |
| 005416 | PMC6093752 | CC BY 3.0 | Unresolved |
| 055358 | PMC8404122 | CC BY 4.0 | F9 |
| 001828 | PMC7884066 | CC BY 4.0 | Fig2 |
| 055240 | PMC2277428 | CC BY 2.0 | F1 |
| 055075 | PMC3017926 | CC BY 2.0 | F0002 |
| 007674 | PMC4564414 | CC BY 2.0 | F0003 |
| 056560 | PMC4391505 | CC BY 3.0 | fig2 |
| 023807 | PMC7786393 | CC BY 4.0 | F1 |
| 018974 | PMC4863867 | CC BY 4.0 | f1 |

Every suffix expands to `ROCOv2_2023_train_<suffix>`. For 011831 and 005416, the source caption differs from the article caption at title/body punctuation boundaries. Correcting those differences would exceed the declared normalization rule, so `original_figure_id` and graphic references remain null/empty. Those two findings are specific unresolved provenance, not failed article-license retrievals.

## Reproduction and remaining boundary

From the project root, `python3 work/roco-upstream-rights/analyze.py` regenerates the report, and `python3 work/roco-upstream-rights/verify.py` independently checks PMCID identity, explicit license URI presence, exact caption uniqueness, figure IDs, graphic references, input hashes, request intervals and scope flags. Both exited zero. Verification includes four normalization checks that preserve punctuation/case differences while accepting whitespace and canonical Unicode equivalence. `acquire.py` uses only the 24 frozen shortlist articles plus documentation and verifies cached bytes before skipping a retrieval.

The next consumer should retain these as separately versioned **article-license evidence** and **caption-linked figure provenance**. It should not overwrite the aggregate dataset license, erase old unresolved metadata snapshots, infer patient independence, claim an upstream-graphic byte match, or promote any pending image/manifest into an approved model-use source.
