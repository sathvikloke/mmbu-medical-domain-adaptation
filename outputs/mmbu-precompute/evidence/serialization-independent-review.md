# Independent bounded target-serialization review

Verdict: **PASS for the stated local serialization scope; no actionable defect found.** Read-only review by the processor-probe worker, separate from the serializer author. No production changes were made. Review completed 2026-10-04.

| Reviewed artifact | SHA-256 |
| --- | --- |
| `src/mmbu_prep/serialization.py` | `547a9089fc518ad7a50ec95dcb931d284ce9966d690ababcf5f9990064cf6425` |
| `tests/test_serialization.py` | `e89371b5e0d503b6fbd4f588b780ea0c211e06cc8dde83616edea29f2db28ae5` |

The review traced task/profile validation, exact supplied-value preservation, JSON serialization, the existing strict output parser, geometry validation, independent input builders, and the local context wrapper. It also read `docs/target-serialization.md` for claim consistency. No network, installs, model execution, GPU work or biomedical annotation was used.

From the package directory, the independent replay command was:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src \
  ../../work/processor-probe/.venv/bin/python -m unittest discover \
  -s tests -p test_serialization.py -v
```

Result: exit 0, **20 tests passed**, reported elapsed 0.002 s.

An additional independent Python driver exercised **676 accepted cases and 14 rejected cases**, exit 0. It decoded generated JSON directly with the standard JSON reader and compared recursive type/value signatures rather than relying only on the production round-trip parser. Cases included both task profiles; ordinary, whitespace-bearing, control-character, Unicode-line-separator, emoji, JSON-looking and lone-surrogate strings; scalar versus one-element mask lists; 200-digit integer and 301-digit string counts; 486 single/multiple-box combinations; and signed zero/float/integer coordinate preservation. Inputs were checked for nonmutation and repeated outputs for equality. All 120 ordered triples of the six context fields retained requested ordering and exact values with an explicit empty rationale.

Additional rejection cases covered a coordinate just outside the boundary (`math.nextafter(1, math.inf)`), Boolean coordinates/extents, mixed box/object and box/Boolean lists, and JSON-bearing public-card rationale prefixes including exponent overflow and objects inside arrays/quoted prose. All were rejected without repair.

Findings within scope:

- Task names and profiles must be explicitly supported; no classification/count/box/rationale defaults are invented.
- Supplied scalar/list cardinality, string/integer/float values and list order are preserved. Counting rejects Boolean, negative, floating and noncanonical decimal representations. Mask duplicates are rejected, while duplicate detection boxes are retained as documented.
- Detection uses the existing exact rational boundary comparison with explicit image dimensions. No coordinate conversion, clipping or dimensional inference occurs.
- Public-card ambiguity is checked before return; the serializer neither selects another object nor rewrites the caller's rationale. ASCII escapes preserve Unicode string content while keeping the terminal JSON object on one line.
- Context has one explicitly local profile, exactly the requested supported keys, and no guessed missing values. It is not represented as an official context harness format.
- Reference-target serialization remains separate from the task/context input builders. No reference field is inserted into model inputs by these helpers.

This review does not validate biomedical labels, an official submission schema, tokenizer boundaries, assistant loss masks, training permission or model behavior. Those remain separate contracts and evidence. The additional driver was executed read-only in the existing environment; this note records its actual results without claiming a separately saved executable driver.
