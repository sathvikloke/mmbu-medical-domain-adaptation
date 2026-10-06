# Final private-team export audit

**Verdict: PASS for the authorized private team handoff. No unresolved publication blocker was found.**

Reviewed October 5, 2026 America/Chicago (October 6 UTC). Scope: the final `team-repo/` export, its declared transport-only transformations, source-file completeness, third-party license evidence, and the private `workspace-data.zip` release asset. This review does not approve source/model use, clinical interpretation, competition eligibility, or public redistribution. It does not certify GitHub upload or repository permissions, which are separate delivery actions.

## Verified artifact

| Item | Independent result |
| --- | --- |
| Asset path | `work/github-delivery/workspace-data.zip` |
| Compressed bytes | 175,135,253 |
| SHA-256 | `57be1f6894748047da8a03b30559ea87b1e298ea9efb69ff90d0f4f297eef5e3` |
| Release members | 561; unique names; exact match to the release manifest |
| Original research inventory | 852 files; exact match to existing source files after the five declared exclusions |
| Original research files delivered in Git | 458 |
| Original research files delivered in release | 561 |
| Files delivered in both | 167 |
| Authored `work/**/*.py` scripts | All 12 present in both Git and release, with matching published hashes |

Every original source file's current bytes and SHA-256 matched its inventory `original` entry. Every research file delivered in Git matched its `published` entry. Every release member matched both its release-manifest entry and corresponding inventory `published` entry. All 852 original research files have at least one valid delivery location; there were no omitted or extra source-inventory paths. The original workspace remains consistent with the declared original hashes.

The excluded paths are publication staging (`work/github-delivery`), the installed processor environment (`work/processor-probe/.venv`), and the three original package `__pycache__` directories under tools, tests, and `src/mmbu_prep`. These exclusions do not remove original authored analysis, acquisition, review, or result files. Newly supplied team documentation/tools/licenses are separate Git additions rather than original-research inventory entries.

## Credential and session inspection

The independent scan covered 2,341 file/member instances, including 1,181 UTF-8 instances totaling 146,768,117 bytes. It recursively inspected all three portable output ZIPs, the 561-member workspace ZIP, and its three embedded BBBC archives. Generated runtime/cache directories and Git internals were excluded from the staged text scan. No archive members were executed.

- **None of the four original unexpired Zenodo session values occurs anywhere in the scanned repository or release bytes**, including nested archives. The check compared the actual source values internally and reported only presence/absence, never the values.
- No private-key, GitHub token, Hugging Face token, OpenAI token, AWS access-key, Slack token, or authenticated-URL pattern was found. This is a bounded scan result, not a universal proof that arbitrary secret formats cannot exist.
- All five source-expansion `Set-Cookie` values have been replaced with explicit redaction markers in the loose evidence JSON, raw retrieval ledger, archived v0.3 member, and the raw ledger's release copy.
- The retained three Hugging Face signed URLs are unchanged historical public-download receipts. They expired October 4, 2026 at 18:25:34 / 18:25:49 / 18:25:50 UTC and are nonblocking.
- The 26 `ncbi_sid` fields in the upstream-rights ledger remain, in both Git and release. They are documented NCBI tracking identifiers from the unauthenticated public acquisition reviewed earlier, not demonstrated account-access credentials. Their optional omission was not a publication requirement.
- Previously classified public CAPTCHA/Stripe configuration, Codecov badge configuration, tokenizer vocabulary and source hashes remain ordinary provenance, not user credentials.

## Transformation audit

The actual set of changed original research files exactly equals the four entries in `research/publication-redactions.json`. All original/exported lengths and SHA-256 values in that declaration matched independently recomputed values.

| Transformed file | Verified difference |
| --- | --- |
| `outputs/mmbu-precompute/evidence/source-expansion.json` | Exactly five changed JSON leaves: `retrievals[1,2,3,4,8].headers.set-cookie`. No other structured content changed. |
| `work/source-expansion/retrieval-ledger.json` | Exactly five changed JSON leaves: `[1,2,3,4,8].headers.set-cookie`. No other structured content changed. |
| `outputs/mmbu-precompute/evidence/bundle-manifest.json` | Only the `bytes` and `sha256` fields for `evidence/source-expansion.json` changed. |
| `outputs/mmbu-precompute-v0.3.zip` | Member order and names preserved. Exactly two changed member contents: `mmbu-precompute/evidence/source-expansion.json` and `mmbu-precompute/evidence/bundle-manifest.json`. All 276 exported members exactly match their loose exported counterparts. |

`research/original-bundle-manifest-v0.3.json` exactly matches the original local bundle manifest. The expired signed URLs and scientific/research content were not modified by the redaction operation. The original and v0.2 portable ZIPs remain byte-identical according to their inventory entries.

## License and handoff completeness

All seven files under `third_party/qwen/` match the independently retrieved license-research sources byte for byte: the three pinned README declarations, Qwen3.5's pinned LICENSE, canonical Apache-2.0 text, retrieval ledger, and explanatory README. The ledger preserves exact retrieval URLs, revisions, and hashes; the README distinguishes the two pinned repositories without a LICENSE file from the canonical Apache text supplied alongside their explicit Apache-2.0 declarations.

All twelve authored work scripts are preserved: the processor-probe test; ROCO sample acquisition and contact-sheet generation; upstream-rights acquisition, analysis, verification and three independent review drivers; and source-expansion analysis, protocol recheck and supervision/presentation review. The complete inventory/hash verification also covers historical audit records, prepared image/mask annotations, both ROCO prepared/replay trees, source captures, metadata tables, processor/tokenizer artifacts, and original source archives.

The earlier source-specific rights, quarantine and model-use caveats remain applicable. This final check deliberately did not reopen scientific rigor or clinical pixel review; it verified that the authorized export retained the corresponding original material and introduced only the declared transport sanitization. The reviewer made no export, source-data, repository, or GitHub mutation during this final review; this report is the sole written output.
