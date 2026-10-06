# Development

Run the repository helper with Python 3.11 or newer. The core uses only the Python standard library and requires no package installation. Commands below start at the repository root; the helper also finds its repository when invoked from another working directory.

```sh
python3 -m venv .venv
.venv/bin/python tools/team.py test
.venv/bin/python tools/team.py smoke
.venv/bin/python tools/team.py verify-evidence
.venv/bin/python tools/team.py verify-links
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`. Keep each command's exit code; a failing helper must not be recorded as a successful check. `test` runs the historical package suite and then root tooling tests. Both use the same interpreter as the helper. The first failed child command stops the sequence and retains its exit code (a terminated Unix child is reported as `128 + signal`).

`smoke` executes `status`, `demo`, and the comparison and diagnostic commands on the supplied pregraded toy input with 25 bootstrap samples and seed 17. These checks run locally without downloads, model inference, training, or GPU use. They establish software behavior only.

## Optional image checks

Install Pillow explicitly in your virtual environment when testing image behavior:

```sh
.venv/bin/python -m pip install "Pillow==12.3.0"
.venv/bin/python tools/team.py test --images
```

`--images` requires an already installed Pillow version at least 12.3 and below 13, and fails if it is absent or outside that range. The helper never installs dependencies. Without Pillow, the historical suite skips its optional image tests; with Pillow, it exercises them. Processor and synthetic loss probes have separate dependencies described in the [historical processor documentation](../../outputs/mmbu-precompute/docs/processor-compatibility.md); they are outside the core CI scope.

## Historical integrity

`verify-evidence` checks the exact 275-file v0.3 inventory, every recorded file size and SHA-256, the original and published manifests, both unchanged older ZIPs, the sanitized v0.3 ZIP, and all three unchanged original verification receipts against fixed anchors. It also checks every v0.3 ZIP member against the published manifest and rejects missing, extra, or duplicate members, without extracting or executing the archive. Missing, changed, or extra bundle files fail the check. Generated regular `__pycache__/*.pyc` files are ignored; other additions are not.

The publication removed five transport `Set-Cookie` values from two retrieval records. The [publication record](../../research/publication-redactions.json) identifies exactly four allowed transformations: those two records, the package manifest, and the repacked v0.3 ZIP. Each original and published size/hash is fixed in the verifier; editing the record cannot authorize another file or hash. The [original v0.3 manifest](../../research/original-bundle-manifest-v0.3.json) retains its historical hash. The published manifest must be identical to that original object except for the one sanitized `evidence/source-expansion.json` entry. Original cookie-bearing records and the original v0.3 ZIP are not restored into the shared repository.

The [v0.3 receipt](../../outputs/MMBU-precompute-v0.3-verification.json) is historical evidence about the original archive, not a receipt for the sanitized ZIP. Its old machine paths and recorded test results are retained verbatim. Passing integrity checks proves the supplied artifact bytes match their original or explicitly published anchors; it does not validate paper claims, biomedical labels, dataset rights, training, or model quality. Do not regenerate anchors to hide a failure. Keep new development outside the preserved preparation bundle until the team deliberately creates a separately versioned successor.

## Maintained documentation links

`verify-links` scans root `*.md` files and `docs/team/**/*.md`. It checks relative file/directory targets and Markdown fragments against simple GitHub-style ATX headings (including duplicate headings) and explicit HTML `id`/`name` anchors. It supports inline and reference links, URL-encoded paths, and angle-bracket destinations. Use these forms in maintained documents; complex Markdown extensions and fragments in non-Markdown files are not validated.

Fenced and inline code examples are ignored. HTTP, HTTPS, mail links, and protocol-relative external URLs are not fetched; passing the check does not promise remote availability. Links leaving the checkout fail. Historical Markdown in `outputs/` is not scanned because those files retain original work references as evidence; a maintained link to a historical file still checks that file exists.

## Continuous integration

The [workflow](../../.github/workflows/ci.yml) runs isolated standard-library jobs on Python 3.11, 3.12, and 3.14, plus an image job on Python 3.12 with Pillow 12.3.0. Jobs have finite timeouts and repository contents read permission. They use no repository secrets or model downloads. GitHub downloads the actions/interpreters and the image job installs Pillow from the package index.

Official actions are pinned to full commits resolved through read-only GitHub API calls on 2026-10-05: [checkout v4](https://github.com/actions/checkout/commit/11d5960a326750d5838078e36cf38b85af677262) and [setup-python v5](https://github.com/actions/setup-python/commit/a26af69be951a213d495a4c3e4e4022e16d87065). Review upstream commits before updating those pins. Local checks do not establish that hosted CI has run; retain the actual CI run result after pushing.

## Review practice

Use the bug issue form for reproducible failures and the experiment form for proposed scientific work. Include commands, commit identity, actual logs and exit codes, and uncertainty. A proposal does not itself authorize data use or compute. Use the [pull request checklist](../../.github/pull_request_template.md) to state validation and preserve the boundary between engineering checks and research results.
