# Independent tooling review and documentation checks

**Verdict: no material blocking defect found within the reviewed scope.** Reviewer: the separate `team_docs` AI agent. This agent did not author or modify either helper or its tests. The tooling review is author-independent AI review, not human peer review or a full security audit. The agent authored the nine team documents, so their checks are not an independent authorship review; `DEVELOPMENT.md` and Qwen license evidence came from other agents.

## Scope and findings

Read `tools/team.py`, `tools/restore_workspace.py`, and their tests. The publication verifier correctly separates anchored original manifests/receipts from sanitized published objects. Only the four fixed transformations are accepted; the published package manifest may differ only in its sanitized source-expansion entry. The v0.3 ZIP members are checked against the published manifest, while original receipts retain their original archive identities. The reviewed failure paths and executed tamper cases return nonzero outcomes.

Restoration checks identity, bounded paths/members, ZIP/member hashes, destination conflicts, symlinks, and file-parent conflicts before publishing verified files individually. The documented operating scope is a quiescent, writable local filesystem with hard-link support. There is no whole-tree transaction or concurrent-modification protection. A late filesystem failure may leave some verified files restored; reruns accept identical files. Temporary space is required even for dry runs. These limits are explicit in onboarding.

Maintained docs distinguish AI-agent reviews from human/biomedical approval, pending data from approved model use, preprocessing from model results, and historical receipts from publication hashes. Qwen notices link supplied licenses/cards/receipts without presenting the canonical Apache text as a model-repository file. No tooling was changed; tamper probes used disposable copies. No new broad testing was performed to write this report.

## Executed commands and results

Working directory: `/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge/team-repo`. Interpreter: Python 3.14.7, `/opt/homebrew/opt/python@3.14/bin/python3.14`. These results were observed during the completed review, not rerun for this report.

| Command | Observed result |
| --- | --- |
| `PYTHONPATH=outputs/mmbu-precompute/src python3 -m mmbu_prep --workspace outputs/mmbu-precompute demo` | Exit 0; `ok: true`, `model_executed: false`, `official_evaluation: false`; synthetic fixtures only |
| `python3 tools/restore_workspace.py --help` | Exit 0; documented arguments match implementation |
| `python3 tools/team.py verify-links` | Final check exit 0; maintained local paths/anchors pass; external URLs not fetched |
| `python3 -m unittest discover -s tests -p test_restore_workspace.py -v` | Exit 0; 12 tests passed in 0.035 seconds, no skips |
| `python3 tools/restore_workspace.py --archive ../work/github-delivery/workspace-data.zip --dry-run` | Exit 0; 561 verified, 167 existing identical, 0 restored; `model_use_approved: false` |

Restore regressions cover successful/idempotent replay, dry run, archive/member corruption, existing-file preservation, symlinks, file-parent conflicts, extra members, unsafe/colliding paths, and malformed JSON/version values. `test_team_tools.py` was read; its complete suite was not separately executed by this reviewer. The historical 277-test package suite was not rerun here.

The actual asset dry-run checked 175,135,253 archive bytes and 561 members totaling 302,401,092 expanded bytes. ZIP SHA-256: `57be1f6894748047da8a03b30559ea87b1e298ea9efb69ff90d0f4f297eef5e3`. It verified the full real asset without publication; actual publication/idempotence was exercised on regression fixtures.

## Independent CLI tamper results

A `python3` heredoc copied the package, three ZIPs, three original receipts, publication record, original manifest, and sanitized work retrieval ledger to a `tempfile.TemporaryDirectory(prefix='mmbu-independent-check-')`. Each check called the actual CLI with this exact argument pattern: `[sys.executable, str(root/'tools/team.py'), '--root', str(temp), 'verify-evidence']`, capturing stdout/stderr and return code. Each mutation was restored before the next case. The outer script asserted the expected outcomes, exited 0, and removed all copies.

| Case | Mutation to temporary copy | CLI exit | `ERROR:` lines |
| --- | --- | ---: | ---: |
| Clean publication | None | 0 | 0 |
| Same-size changed published evidence | `source-expansion.json`: `write_bytes(b'X' + original_bytes[1:])` | 1 | 2 |
| Changed original receipt | `MMBU-precompute-v0.3-verification.json`: append `b' '` | 1 | 2 |
| Record cannot authorize a new hash | `publication-redactions.json`: set first transformation's `published_sha256` to `'0' * 64` | 1 | 1 |
| Changed published ZIP | `mmbu-precompute-v0.3.zip`: append `b'X'` | 1 | 2 |

## Limits and remaining operational check

Authenticated `--download` after private release publication and collaborators' accepted access were not tested. Hosted CI, other operating systems/filesystems, Python 3.11 runtime, and actual biomedical/model/GPU work are outside scope. The Qwen references were integrated from saved evidence; this is not independent legal clearance or upstream authentication. Fixed hashes are local trust anchors; changes to both code and anchors require new review. Byte integrity does not establish scientific validity, permissions, medical truth, or model quality.

## File identity snapshot

SHA-256 values below were recomputed when saving the report after review; tooling was reread at this snapshot. Documentation/reference hashes identify context, not a claim of full substantive audit of every upstream artifact. The report itself is excluded. Future edits require a new review or explicit delta review.

Snapshot UTC: 2026-10-06T01:24:23.799068+00:00

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/team.py` | 18628 | `ca5f8d24e02f10a97fadb89e9bfa382e6770caed8f6deb849cd8ea8e01e185d0` |
| `tools/restore_workspace.py` | 8009 | `ec9570d22e8b943cb3ea55b7bd67a4a3e4cb92187af400e777087a0e68fc373c` |
| `tests/test_team_tools.py` | 9209 | `ea9a62603a469bb7877bebded2b8c09a1dbe0b1ba5b4b36ce5e614906be20208` |
| `tests/test_restore_workspace.py` | 6584 | `c783479cbd9a8e80d63f6daaad60a4de57d6757053af0ecc5347bfcb2c542aa9` |
| `README.md` | 5015 | `7b64b75023be61cd36819cdff89e93c9e5b36927e6b4eafd5219459bef52316f` |
| `CONTRIBUTING.md` | 5647 | `f4099a43adc0b5aba56b823cf3be389e846cf78a480883c6a3ccdf8bd3699c96` |
| `THIRD_PARTY_NOTICES.md` | 5630 | `ac11ea546e37cc46ab4bed5cb01ae7f257a4153d2ed5d01722e5da53d5718c6f` |
| `research/publication-redactions.json` | 2215 | `b578f5198ff7a07145d594455f913acd5bf8d4ac39f783047a60731a294c7234` |
| `research/original-bundle-manifest-v0.3.json` | 42572 | `51db3f2af0177df49a42fda0a942d9e68e5807b8a1d8d61ed2bd0805f1c93f5d` |
| `research/workspace-data-manifest.json` | 114705 | `e69b2733b7282e6df6bfe0f9274c99148b54927fcce914976011e15587c44307` |
| `research/workspace-inventory.json` | 414392 | `6cdf6f8f5691ec72c03a6ea22c98d69767126963d694636f11960047c50ee45d` |
| `outputs/mmbu-precompute/evidence/bundle-manifest.json` | 42572 | `c5761ff316edc0ff9dc43017d42ef38f0b619cdead53f7c2e13a1ed1b38c51e8` |
| `outputs/MMBU-precompute-v0.3-verification.json` | 4242 | `12c1bbd383951bd1dc3ac710ab2357d77d66e5307273eeb6c6da9674fff91170` |
| `outputs/mmbu-precompute-v0.3.zip` | 1042151 | `ab872f5908287e8b37f74c35673165273469101881a2f98cb37a80e262db75ba` |
| `docs/team/DATA_AND_MODELS.md` | 7855 | `dea129e82f351fa75c42fcf5093b6e1e67110e36ad19be89effa9cc316efb979` |
| `docs/team/DECISIONS.md` | 6019 | `19b6bfe458f3f1dc5c19560e10ae5e8fa1b12c3e8c9e7b29bf4ed93ab3b59e1b` |
| `docs/team/DEVELOPMENT.md` | 6031 | `7e186842e9f31dd756a6384a9e2bece53fbcd4eb7af7ef1007b7c38ed2a91076` |
| `docs/team/EXPERIMENT_WORKFLOW.md` | 7642 | `2c757c1f17bd64ae6664ae2087adfd8a8eddd6d4ab03feda517cbb0ec0ef80e8` |
| `docs/team/REPOSITORY_MAP.md` | 7634 | `d2d7f97b58949370d2f2c5ef930eec88573ba8e4ee6beac432822310d44bf446` |
| `docs/team/RESULTS.md` | 9752 | `b72189da1243d9a686599e62ae786c1836c3177b57c3da4a3d65f64b068e83df` |
| `docs/team/START_HERE.md` | 4875 | `b49d33c2df970feaf6c02ecb3b41af43889c9ef476c9989af151c4b36d18335b` |
| `third_party/qwen/Apache-2.0.txt` | 11358 | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| `third_party/qwen/Qwen2.5-VL-7B-Instruct--README.md` | 18574 | `1fa65dbb08bc9ffe0b020409c8686f08b23008c5a68554353305fd2de6f2b81e` |
| `third_party/qwen/Qwen3-VL-8B-Instruct--README.md` | 7133 | `6d5d06e0c3f069097002445d30dce9ee107db3afaf15563f09e6df49b8dcb4d7` |
| `third_party/qwen/Qwen3.5-9B--LICENSE` | 11544 | `bbedc3fda3305820b977265f01b8619d87570a6739de3a5582c3464840f1e57a` |
| `third_party/qwen/Qwen3.5-9B--README.md` | 77643 | `c5f5a8c2dddab69cfbf05279235aa5fddb137939a06539c4c7637aa900fef6d0` |
| `third_party/qwen/README.md` | 1843 | `a786e849228aac96d90c6e30ca364161db06094e874fc04f4c8b3b79c69c88ee` |
| `third_party/qwen/retrievals.json` | 3332 | `e3bc221c3565fe6eb82cb3733a7e0cb86db31e4246b3569fdcaea055af537233` |
