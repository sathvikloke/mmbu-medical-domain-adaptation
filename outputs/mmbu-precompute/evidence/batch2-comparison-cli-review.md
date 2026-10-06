# Independent comparison and CLI review

Verdict: PASS for the inspected arithmetic and integration scope; no consequential defect found.

Reviewer authored images.py, not comparison.py, metrics.py, or __main__.py. Accordingly the image CLI checks below establish integration only, not an independent audit of the image implementation; that review is assigned separately. No production file was changed by this review.

The independent rational oracle uses two fixed sources, unequal group sizes, nonuniform weights, candidate-specific baselines, unequal context-field counts, and 257 shared resamples. It does not call metric/comparison arithmetic helpers. Literal point expectations are alpha S=71/360, beta S=73/1440 and alpha-minus-beta=211/1440. Per-source mass stays exactly one half in the rational oracle on every draw. The paired interval agrees within 1e-12; an identical third candidate has exactly zero paired difference. Candidate and row reordering is invariant. Metadata/record-set mismatches reject, and underpowered sources withhold intervals. No winner, ranking, significance decision, or multiplicity adjustment is inferred.

CLI review covers named-weight comparison, invalid iterations/confidence, record mismatch, duplicate JSON keys, nonfinite exponent input, actual decoding of all five shipped PGM fixtures, pixel-limit rejection, optional dependency absence, corrupt bytes, and missing BBBC039 archives. Invalid cases return exit 2 with structured JSON and no traceback.

Limits: grades, baseline identities, biomedical labels, and independent source/group provenance remain caller evidence. Percentile intervals are conditional fixed-source exploratory calculations; this review does not establish statistical coverage, unseen-source generalization, multiplicity control, or an official result. Image-inspection implementation safety is outside this independent review because this reviewer authored that module.

Executed from package root with bundled Python and `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src`; isolated CLI artifacts were created only in a temporary directory. Machine-readable execution receipt:

```json
{
  "status": "PASS",
  "python": "3.12.14 (main, Aug 25 2026, 13:50:33) [Clang 22.1.3 ]",
  "oracle": {
    "alpha_S": "71/360",
    "beta_S": "73/1440",
    "alpha_minus_beta": "211/1440",
    "expected_interval": [
      0.0359375,
      0.35833333333333334
    ],
    "actual_interval": [
      0.03593750000000001,
      0.35833333333333334
    ],
    "shared_identical_interval": [
      0.0,
      0.0
    ],
    "source_mass_per_draw": "A=1/2; B=1/2"
  },
  "alignment_rejections": [
    "source_id",
    "group_id",
    "task",
    "context_correct",
    "record_set"
  ],
  "cli_checks": [
    {
      "arguments": [
        "compare",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/candidates.json",
        "--weights",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/weights.json",
        "--bootstrap",
        "257",
        "--seed",
        "73",
        "--confidence",
        ".8"
      ],
      "without_site": false,
      "exit_code": 0,
      "payload_ok": null
    },
    {
      "arguments": [
        "compare",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/candidates.json",
        "--bootstrap",
        "0"
      ],
      "without_site": false,
      "exit_code": 2,
      "payload_ok": null
    },
    {
      "arguments": [
        "compare",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/candidates.json",
        "--confidence",
        "nan"
      ],
      "without_site": false,
      "exit_code": 2,
      "payload_ok": null
    },
    {
      "arguments": [
        "compare",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/candidates.json"
      ],
      "without_site": false,
      "exit_code": 2,
      "payload_ok": null
    },
    {
      "arguments": [
        "compare",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/candidates.json"
      ],
      "without_site": false,
      "exit_code": 2,
      "payload_ok": null
    },
    {
      "arguments": [
        "compare",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/candidates.json"
      ],
      "without_site": false,
      "exit_code": 2,
      "payload_ok": null
    },
    {
      "arguments": [
        "inspect-images",
        "/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/examples/engineering-manifest.jsonl",
        "--image-root",
        "/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/examples"
      ],
      "without_site": false,
      "exit_code": 0,
      "payload_ok": true
    },
    {
      "arguments": [
        "inspect-images",
        "/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/examples/engineering-manifest.jsonl",
        "--image-root",
        "/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/examples",
        "--max-pixels",
        "1"
      ],
      "without_site": false,
      "exit_code": 2,
      "payload_ok": false
    },
    {
      "arguments": [
        "inspect-images",
        "/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/examples/engineering-manifest.jsonl",
        "--image-root",
        "/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/outputs/mmbu-precompute/examples"
      ],
      "without_site": true,
      "exit_code": 2,
      "payload_ok": false
    },
    {
      "arguments": [
        "inspect-images",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/bad.json",
        "--image-root",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls"
      ],
      "without_site": false,
      "exit_code": 2,
      "payload_ok": false
    },
    {
      "arguments": [
        "prepare-bbbc039",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/missing",
        "--output",
        "/var/folders/cg/p3brbvp90c3gxplxsvs7xqf40000gn/T/tmp7j1ho_ls/quarantine"
      ],
      "without_site": false,
      "exit_code": 2,
      "payload_ok": null
    }
  ],
  "file_sha256": {
    "src/mmbu_prep/comparison.py": "4c9c1d1cdb3d9c227c9c23baebbec9f78ebac3da0d3249ee80d6790f24500dd4",
    "src/mmbu_prep/__main__.py": "5ce6775283308b6a8d0618860709cdd726dbb3fc5dcf462a2971cf8b1484c766"
  }
}
```
