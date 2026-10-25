# Biomedical Lane 1 five-arm shakedown trace

**Run date:** October 25, 2026  
**Evidence class:** bounded external-biomedical wiring shakedown; not candidate selection, novelty evidence, or an MMBU score  
**Remote run root:** `/storage/home/npl015/mmbu-lane1/2026-10-24-6db7779`  
**Scheduler:** source preparation `85670`, base arm `85682`, adapted-arm array `85685`  

## Bound inputs and checks

- BUS-BRA and PathMNIST passed their pinned archive checksums.
- Recompiling the 109,051-row portfolio produced a byte-identical manifest.
- Compiled portfolio raw SHA-256: `32b13741b25a3a8e1a7bcc9eab62327d2cc3ae8f151a917858a5d088d93cf152`.
- Frozen run-config digest: `e542437a34d12dccdc01d473a5a5c57c245a34f7d8b4e03399871b6f246a3c9e`.
- Seed: `20261024`.
- All arms used training-order digest `1c5e8ac10ea187c4eda53a5beedeb64c341af5d8e1652b7bfe9d4833d685e00f`.
- All arms used the same 64 development rows in the same order; row-order digest
  `215964bb56d344a3cb0fe9664c1b4193fec6c419addb9cf136ff1394062ab5a3`.
- Every result is canonical JSON, reports `status=passed`, has an exact offline reload/prediction match, records no MMBU
  public content use, and records no scientific-selection output. Each adapted arm completed 128 optimizer updates; the
  unchanged base completed zero.

## Descriptive result

The table reports exact frozen-proxy metrics. Percentages are shown only to make the fractions readable.

| Arm | Architecture / objective | Answer macro | BUS-BRA answer | PathMNIST answer | Context macro | Result SHA-256 |
|---:|---|---:|---:|---:|---:|---|
| 0 | unchanged base | 7/16 (43.75%) | 9/16 (56.25%) | 5/16 (31.25%) | 0/1 | `040b94d93533b668b0d6fd8488861dbda175a5ca79a0be8398d2378b3e37d04f` |
| 1 | language LoRA, task only | 17/32 (53.125%) | 9/16 (56.25%) | 1/2 (50%) | 0/1 | `410917a03da1974bb278652ca8abfaa62c1711a640b2a47b8fc234265c064275` |
| 2 | language LoRA, task + context | 1/2 (50%) | 9/16 (56.25%) | 7/16 (43.75%) | 0/1 | `0b1b118b817c46482d9ecb1c1d14d02753091d65cf58dbda258bdd34fcbed02a` |
| 3 | language LoRA + projector, task only | 31/64 (48.4375%) | 9/16 (56.25%) | 13/32 (40.625%) | 0/1 | `fffd32103ae5eebe79f5d0ce3a5174e62c998d1cef7e228f94108957c5125ff1` |
| 4 | language LoRA + projector, task + context | 15/32 (46.875%) | 9/16 (56.25%) | 3/8 (37.5%) | 0/1 | `4dccfbfbcc31f55f503aee17cccc5e430af05695a6dc46399596b8cef724addd` |

## Honest interpretation

Arm 1 is descriptively highest on the 64-row answer proxy, 9.375 percentage points above the unchanged base. That
difference comes entirely from PathMNIST; every arm is tied on BUS-BRA at 9/16. Both dual-objective arms score below
their task-only architecture controls, both projector arms score below their language-only controls, and every arm has
zero context credit.

These observations are useful failure-localization evidence: the training/export/reload path works, the present context
target/scorer supplies no positive signal, and projector updates have not earned the cost of a larger run. They do not
identify a winner. This is one seed, one short epoch, 128 selected training units, 64 development units, exact-string
proxy scoring, and no independent confirmation. No arm may be promoted, no project score may increase, and no novelty or
human-impact claim follows from this shakedown.

## Next gate

Before spending on a larger run, diagnose the zero-context result and freeze a replicated comparison with uncertainty,
an untouched eligible confirmation cohort, and a predeclared decision rule. Keep Arm 1 as a control worth retesting—not
as a selected candidate. Do not evaluate MMBU Public, upload, or submit from this evidence.
