# ChestMNIST label-blind development freeze

**Date:** October 26, 2026  
**Execution:** MOCS CPU job `86247`  
**Repository revision:** `a1cb2a5`  
**Remote evidence root:** `/storage/scr/npl015/mmbu-chestmnist-intake/2026-10-26-a1cb2a5`  
**Decision:** the NIH development population now has one immutable patient-level role allocation; ChestMNIST remains
unadmitted.

## Result

The job reacquired only the three already-audited public metadata files and required their exact saved byte counts and
SHA-256 hashes before execution. It did not download or open ChestMNIST labels or pixels.

| Role | Patients | Images |
| --- | ---: | ---: |
| Training | 25,207 | 77,786 |
| Adaptive development | 2,801 | 8,738 |
| NIH official test, excluded | 2,797 | 25,596 |

The allocation ranks the 28,008 official NIH train/validation patients by SHA-256 over a fixed domain, fixed namespace,
and patient ID. The lowest 2,801 hashes receive `adaptive_development`; all others receive `train`. The executable
exposes no seed, ratio, class, label, or threshold option. This makes the split reproducible and prevents future model
outcomes from changing patient roles.

## Portable evidence

The complete outputs are retained under
[`outputs/chestmnist-development-freeze-2026-10-26`](../../outputs/chestmnist-development-freeze-2026-10-26):

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `mapping-audit.json` | 821 | `a30d1b2165c7b2207f07989f7759a3d21a2da2f5c3b91a7b2e5684ea46f85c19` |
| `patient-roles.csv` | 462,151 | `a6c5eb102638c33fd6a88652394e36080e6cfb7ab70d2bd3952cbf0ea7e0613a` |
| `patient-role-freeze-receipt.json` | 1,014 | `12c8158ce216c64882391e1502dbfa70ecde1397bc7c8d36706f314432fc8177` |
| `development-manifest.json` | 9,848,640 | `eefd33a8fcdf8d22900efa1debeaeabd1be5b3296c770ced51e441a32d17343d` |

The role receipt's canonical record digest is
`3b93b84c773aa0aadeecfbebace6c10d5c95e65a856e2f98fd715ede0b855182`. The development manifest's canonical
record digest is `7929111c756e506f631ec5cd69dd56103e88c31a239d1b6fb500185a88d9dba0`.

Repository tests recompute every portable artifact hash and both canonical record digests; verify every patient-role
join; require 86,524 unique image identities, 86,524 unique wrapper array locations, and 28,008 unique patients; and
require the explicit non-admission and no-label/no-pixel boundary.

## What this changes

The earlier split-selection blocker is closed. Any later ChestMNIST label or pixel opening must use this exact role file
and manifest or create a new exploratory lineage that cannot inherit this freeze.

## What remains blocked

This result does **not** admit ChestMNIST, authorize model use, validate its text-mined positive labels, establish
negative labels, review 224-pixel image fidelity, clear trained-weight release rights, or provide a clinician-reviewed
endpoint. The next score-changing gate is a separately protected label/image opening and qualified positive-label QA
plan bound to this manifest. NIH test labels and pixels remain unopened and excluded.
