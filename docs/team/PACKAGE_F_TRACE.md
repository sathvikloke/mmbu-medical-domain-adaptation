# Package F synthetic implementation trace

**Observed:** October 22, 2026 23:14 CDT
**Scope:** authorized Package F CPU-only synthetic work
**Verdict:** `schema_ready` for the bounded synthetic slice; not scientifically frozen or execution-ready

This receipt maps the Package F handoff clauses to implementation and negative-test evidence. It does not choose a
scientific value, admit or open biomedical/MMBU data, grant a source model-use purpose, load weights, use a GPU or MOCS,
train, evaluate the MMBU public set, upload, submit, or execute Packages C, D, E, G, H, or I.

## File receipt

| Path | Bytes | SHA-256 | Role |
|---|---:|---|---|
| `src/mmbu_phase1/competition_manifest.py` | 23,949 | `3eeff93daa93f16dda32edf6191dfadf5318ca7ed45ae071a1fb368b1ee4d92e` | Closed manifest, state machine, and promotion decision |
| `src/mmbu_phase1/research_registry.py` | 20,813 | `3a072f14ac801a1636fbe7f2bb3d43b1a73e2f55d2b26529bd76f889bfcab667` | Disabled v1 registry and H1 validators |
| `src/mmbu_phase1/track2_score.py` | 1,015 | `68e53d84ee0adf2f9a8e887ada10fce9ac6dfe4f441b2699ab53a5040bf3860b` | Exact rational score proxy |
| `src/mmbu_phase1/scope.py` | 16,788 | `8f867eb801ab8c118e0751c11f3b24fc00a69b751063b83e567dcc7834c45f98` | Fail-closed required-test inventory |
| `tests/phase1/test_package_f.py` | 27,454 | `e66c141cb1c04be17be830d3bd5a4f4849070c43ca869a4bd3304b32852d5a89` | Synthetic positive and negative fixtures |
| `docs/team/PACKAGE_F_MATRIX.md` | 3,565 | `f694ca10d01cc2316bd4b3ff66b7f6513b30f9da3cf865e941a9572899181230` | Prospective implementation/fixture matrix |

## Contract trace

| Package F obligation | Implementation and test evidence | Result |
|---|---|---|
| Closed canonical manifest and forward-only state machine | `competition_manifest.validate_manifest`, `manifest_digest`, `validate_transition`; manifest/state tests | Passed |
| Exact B0/B1-L/B2-P/B2-F universe with B2-F, A1, and A2 disabled | Candidate/profile validation and mutation fixtures | Passed |
| Original-pixel half-open `xywh`, fail-closed serializer, answer-only synthetic rationale policy | Geometry/serializer/rationale mutation fixtures | Passed |
| Unknown values block freeze-or-later states | Freeze-blocker fixture | Passed |
| Exact Track 2 proxy and named conjunctive promotion with no runner-up rescue | `track2_score.score_proxy`, `evaluate_promotion`; rational, gate, and candidate-identity fixtures | Passed |
| Permanently disabled research registry with no execution/Lane 1 bridge | `research_registry.validate_registry`; status, enablement, public-ancestry, execution, and Lane 1 fixtures | Passed |
| Exact SYS-A0–SYS-A3 factorial identity | Closed arm bindings for objective, context, unit normalization, base, serializer, optimizer, seeds, checkpoint policy/slot, prompts, and units; arm mutation fixtures | Passed |
| Fixed total supervised-token estimand | Exact rational per-unit vectors plus matched tokens, loss mass, updates, FLOPs, compute, and displaced-answer schedule; exposure mutation fixtures | Passed |
| Separate task/context estimands, minimum effects, and eight mandatory gates | Keyed maps and missing/collapsed-field fixtures | Passed |
| Equalization and duplication mechanism checks | Within-context pairs, complete exposure quantities, null prediction, and no-new-unit/target matched-exposure fixtures | Passed |
| Role and replication isolation | Four-dimensional unit/duplicate/source/prompt disjointness plus two unique governed confirmation parents and no train/development reuse | Passed |
| Package F suite cannot silently disappear | `scope.REQUIRED_PHASE1_TEST_MODULES`; root orchestration inventory test | Passed |

## Exact results

```text
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests/phase1 -p 'test_package_f.py' -v
Ran 13 tests in 0.037s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -B tools/team.py test
Historical preparation suite: 277 passed, 44 optional-Pillow skips
Root repository/tool suite: 42 passed
Phase 1 suite: 302 passed
OK
```

## Deliberate limits

- Passing fixtures prove representability and rejection behavior only. They do not show that H1 is true, that any model
  improves, that the context proxy matches organizer scoring, or that any biomedical source is admissible.
- The v1 registry has no executable transition. H2 remains Package G work; composite resolution remains Package I work.
- All scientific values, real artifact bindings, model/data/runtime facts, confirmation openings, and release receipts
  remain unknown and therefore blocking.
- Package F completion does not authorize MOCS, GPU, model, data, training, public-set evaluation, upload, or submission.
