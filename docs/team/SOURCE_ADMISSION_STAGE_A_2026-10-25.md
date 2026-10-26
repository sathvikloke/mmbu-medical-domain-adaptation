# Stage A real-source acquisition evidence

**Local audit date:** October 25, 2026  
**Status:** acquisition complete; every source remains quarantined and unauthorized for model use  
**Evidence scope:** byte identity and transport custody only

## Result

All three frozen source acquisitions now have successful, independently validated execution receipts. The initial
PathMNIST attempt failed closed because its mapping file exceeded the packet's incorrect byte cap. That failed run
and its zero-byte partial remain preserved. A corrected packet froze the observed official mapping identity, passed
the full 547-test Phase 1 suite, and completed once in a new scratch root.

| Source | Version | Observed artifacts | Execution receipt | Result |
|---|---:|---|---|---|
| BUS-BRA | 1.0 | `BUSBRA.zip`: 133,917,740 bytes; SHA-256 `ba3e6ed19cc37c682d8d39e25435bbf8a555a12cb7e641b5f2117685c95580ff` | `e1db3ca9c40ad8d56d25cf4485feff2d1caddb4df668e78f6ab73353177be400` | acquired, quarantined, unopened |
| PathMNIST-224 / NCT-CRC | 3.0 | `pathmnist_224.npz`: 12,629,854,322 bytes; SHA-256 `f167745634a90a47cd04e55aa69186ff0d0c4d5d1898045261ee12f83e22dd3e`; `pathmnist_split_info.csv`: 2,785,821 bytes; SHA-256 `ba6f166b2deae125086ecb7ff84223daa90bf35a7c95053be4f030be1a4ac0bb` | `08d0ba17d42bfbd2ad867bc214f71a8ea0b1c317df3fc3bd29822905eaebc223` | acquired, quarantined, unopened |
| BUSI-WHU | 3 | `BUSI-WHU.zip`: 128,106,790 bytes; SHA-256 `5d10c0bb931666e9cff48db9161febc0ec0c74e4b611c2edcbb9726f6d9d74cc`; `Patient_infos_BUSI-WHU.xlsx`: 92,017 bytes; SHA-256 `14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44` | `ab0d82999caaf9eb7412f8f35d37263dc3b8ca4d1f92c2b259109423f6a7dbae` | acquired, quarantined, unopened |

## Custody roots

- BUS-BRA and BUSI-WHU: `/storage/scr/npl015/mmbu-admission/20261026T005840Z-7e2b0fe3-3151-4269-9256-8ef3f57d8c6c`
- Corrected PathMNIST: `/storage/scr/npl015/mmbu-admission/20261026T014504Z-c6219cfd-9aca-4d5e-beb1-bea17b6ab4a5`

The first root also preserves the failed PathMNIST transport status: `ValueError: artifact
pathmnist_split_info.csv exceeded its sealed byte cap`. No retry or overwrite occurred inside that root.

## What this establishes

- Each successful artifact matched its frozen byte count and SHA-256 identity.
- All observed transport hosts were within the corresponding sealed allowlist.
- The corrected PathMNIST packet and authority files matched their local and remote hashes.
- Every terminal status fixes `payload_opened=false` and `mmbu_public_content_used=false`.
- The final artifacts are read-only within their sealed scratch roots.

## What this does not establish

This evidence does **not** establish dataset rights, parent grouping, medical or label correctness, clinical validity,
training suitability, confirmation suitability, release compatibility, model performance, or competition
performance. It grants no model-use purpose. No model weights were loaded, no GPU was used, no training ran, and no
MMBU public example was accessed or evaluated.

## First blocking gate

The next executable step is a separately sealed protected-opening packet. Before any payload access, the repository
must close the remaining synthetic implementation gaps for BUSI-WHU inventory and PathMNIST mapping validation,
then bind the exact three acquisition receipts into source manifests, quarantine records, purpose authorization,
prospective inventory locks, and registered protected-opening receipts. Human acknowledgment of that exact packet
cannot grant later training, confirmation, release, or submission authority.

