Describe the problem, the resulting behavior, and any limits a reviewer needs to assess.

## Validation

Record commands and actual exit codes. Mark anything not run and explain why.

- [ ] `python3 tools/team.py test`
- [ ] `python3 tools/team.py smoke`
- [ ] `python3 tools/team.py verify-evidence`
- [ ] `python3 tools/team.py verify-links`
- [ ] `python3 tools/team.py test --images` when image behavior is affected

## Evidence and scope

- [ ] Historical artifacts match their fixed original or reviewed publication anchors; all original receipts remain unchanged. No new redaction exception was added to bypass an integrity failure.
- [ ] New claims distinguish toy/synthetic software checks from model, scientific, or clinical results.
- [ ] No credentials, patient data, unapproved source assets, caches, model weights, or machine-specific environments are added.

Link the relevant issue, experiment declaration, or reviewer decision when applicable.
