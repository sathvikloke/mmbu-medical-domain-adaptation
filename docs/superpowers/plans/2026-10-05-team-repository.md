# Team repository implementation plan

**Goal:** publish a private, comprehensive, usable MMBU Medical Domain Adaptation team repository and grant write access to adityaraut09, s1g6r, suhritb and nmovva-lab.

**Architecture:** preserve the verified `outputs/mmbu-precompute` layout so historical paths and hashes remain interpretable. Add a clear root entry point, team documentation, CI and evidence verification. Keep all original project code/results available, with large source inputs and processor artifacts in a private release asset that extracts into their original workspace-relative paths. Exclude installed environments and bytecode; record exclusions and any necessary publication redactions explicitly. Preserve originals locally. This shares the complete research handoff without treating pending biomedical data as approved training material.

**Stack:** Python stdlib, optional Pillow/native processor environment, Git, GitHub CLI, GitHub Actions. No model training or GPU jobs.

## Constraints

- Private repository owned by authenticated user sathvikloke; descriptive slug mmbu-medical-domain-adaptation unless already taken.
- Preserve all historical results, including negative tests, without claiming they represent model efficacy.
- All real source records remain pending; no automatic license/medical approval.
- No credentials, active access tokens or installed virtual environments in Git or release assets.
- User has explicitly authorized creating/pushing the repository and sharing it with the four named accounts; no additional approval gate is needed.
- Do not rewrite original outputs, archives or raw evidence; operate on staged copies.

## Task 1 — Complete team entry point

- [x] Add README, contribution instructions, repository map, evidence/results guide, onboarding, experiment workflow and open-decision register.
- [x] Separate actual verified results from future planned training and unknown resources.
- [x] Include source/model attribution and restrictions without inventing a blanket license over third-party assets.

## Task 2 — Reproducible developer experience

- [x] Add CI for Python stdlib tests and optional image tests, root command entry points, publication/evidence integrity verification, meaningful tests and issue/PR templates.
- [x] Verify historical package manifest and release ZIP checksums; list historical absolute-path provenance rather than rewriting it.

## Task 3 — Complete artifact handoff

- [x] Inventory every source workspace file outside installed environments/bytecode; classify repository, release asset, or documented exclusion.
- [x] Preserve all authored analysis/acquisition/review drivers and reports, plus source input/artifact snapshots for authorized teammates.
- [x] Scan staged content for secrets and review any candidates before upload; publish redacted copies only where required and record provenance.
- [x] Build a content-hashed private research asset and verify extraction/file hashes locally.

## Task 4 — Independent review and publication

- [x] Fresh unit/CLI/link/integrity checks and separate-author review of documentation/completeness/security boundaries.
- [ ] Initialize and commit repository, create private remote, push, upload release assets and verify remote identity/visibility/commit/content.
- [ ] Invite exactly the four requested accounts with push/write access and verify accepted versus pending status accurately.
- [ ] Report the repository URL, release access and each invitation status, with any genuine remaining blocker.
