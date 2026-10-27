# BUS-BRA real review packet evidence — 2026-10-26

## Outcome

A real, frozen BUS-BRA reviewer packet now exists for the exact version 1.0 archive. It contains two nested evidence
surfaces:

- the complete 244-record medical/provenance/rights review population; and
- the narrower 108-record train-only visual/annotation QA population.

This is material execution evidence, not an admission result. No human review has been completed. BUS-BRA remains
unadmitted, and training, model use, release, upload, submission, and MMBU-public content use remain false.

A receipt-bound offline browser workspace now packages the narrower population for efficient accountable review. It
is a review aid only and does not change any of those boundaries.

## Frozen identities

| Item | Value |
| --- | --- |
| Repository commit | `c08c2cf7322928d4d213503f23e462964b8ea8e9` |
| BUS-BRA archive bytes | `133917740` |
| BUS-BRA archive MD5 | `1f8b2be6476d58fc97bfb5e5a1ea9bab` |
| Stratified plan digest | `71281236f41d658b1985906c872896647f773f6598947b526221509d34a5b912` |
| Full packet receipt digest | `0b47a05962c3e1eb12391c01362d4ccb66e6d2ef572e2e293c6480892a137d2e` |
| Train-only packet receipt digest | `7a54bfc6a3dac0f13b0a4633b47da0711b20d467706f041f8121bc71833e3937` |
| Evidence tar SHA-256 | `06d5a69094deb6a673954649769e837127dde27db51678aa84a7b678619c364f` |
| Validation record digest | `c85877377cfdc049d422881c74a45e070d3e4593e9a196eaf288d50369b7796b` |
| Offline reviewer repository commit | `5fa1bd9f58b4ca0eabd619539c67b0bec2dac79c` |
| Offline reviewer HTML bytes | `8010709` |
| Offline reviewer HTML SHA-256 | `8a05bb6c6e101b92679bd927847baff80a1475c13b7799f98ad95acec506f270` |
| Offline reviewer generation-receipt digest | `064075a8379d1b8c39fa16d2913f7cc17b67141fc5b8e15a6dc0c7e93fa2a623` |

## Durable location

The evidence is stored under the new, non-overwriting MOCS scratch root:

```text
/storage/scr/npl015/mmbu-train-qa/2026-10-26-c08c2cf-replacement1
```

The immutable payload is `evidence.tar`; `validation.json` is the independently emitted validation record. Earlier
run roots and logs were preserved.

The separate generated reviewer workspace and its generation receipt are stored at:

```text
/storage/scr/npl015/mmbu-train-review-ui/2026-10-26-5fa1bd9
```

Both files are read-only and were published without replacing the packet or any earlier evidence.

## Execution history

1. Job `86221` reproduced the exact 199-record stratified plan, then failed closed before packet publication because
   GPFS returned `EINVAL` for Linux `RENAME_NOREPLACE`.
2. Job `86223` built both packets on node-local storage and atomically published the 21,555,200-byte tar artifact to
   scratch. Slurm recorded the job as failed only because the post-publication cleanup trap attempted to delete
   intentionally read-only temporary files. The published artifact was not changed or retried.
3. Independent read-only validation job `86224` completed with exit code `0`. It checked the tar digest, rejected
   unsafe archive member types and paths, rehashed every receipt-bound packet member, recomputed both receipt and
   manifest digests, confirmed the 244/108 record counts, and verified that every authority and MMBU-public-use flag
   remained false.
4. CPU job `86233` reverified the train packet receipt and every member before generating the offline reviewer. It
   completed with exit code `0`. A separate post-job check recomputed the HTML and canonical receipt digests, counted
   exactly 108 records and 216 embedded PNG data URLs, found no `http://` or `https://` URL, and reconfirmed every
   authority flag as false.

The passing validation record, not the Slurm state of build job `86223`, is the controlling evidence for the published
artifact. The failed job state and cleanup error remain part of the provenance and must not be erased.

## What this establishes

- The real source archive matches its frozen size and checksum.
- The 199-record stratified plan reproduces the preregistered digest exactly.
- The complete review union is exactly 244 records.
- The deterministic train-only projection is exactly 108 records.
- Every included asset is bound through immutable packet receipts and independently reverified after publication.
- The 108-record population can now be reviewed in one dependency-free offline page that exports the validator's
  exact CSV schema and rejects incomplete, noncanonical, or foreign-draft state.
- No MMBU public content was used.

## What this does not establish

- reviewer identity, qualifications, independence, or completed judgments;
- visual, annotation, clinical, provenance, rights, or purpose approval;
- source admission or train-purpose authorization;
- model quality, improvement, novelty, competition readiness, or permission to train; or
- permission to access the MMBU public set, upload, or submit.

The offline workspace also does not validate reviewer identity, qualifications, independence, rights, or the truth of
entered judgments. Browser export is not source admission; the separate Python validator and external trust chain
remain mandatory.

## Exact next gate

Create a digest-bound opening record for train packet
`7a54bfc6a3dac0f13b0a4633b47da0711b20d467706f041f8121bc71833e3937`, then have accountable human reviewers
complete copied versions of `visual-review-template.csv` and `rights-purpose-template.json`. The existing validator
must pass before the generic Phase 1 candidate-admission and train-purpose authorization chain begins. Training is not
the next action.
