# MMBU team working instructions

Read README.md and docs/team/START_HERE.md first. The executable package remains under outputs/mmbu-precompute; commands must use that source path or the root tools/team.py helper.

The private handoff removes response-cookie values and records original/export hashes in research/publication-redactions.json; original historical receipts remain preserved. Treat outputs/ as the historical handoff: do not rewrite published reports, release ZIPs, captured outcomes, source records or evidence to make new results look better. Evolve code deliberately with tests, keep earlier evidence tied to its original hashes, and issue new result files/releases. Existing manifest verification detects edits and must be versioned honestly when a new package is produced.

All real biomedical sources and records are currently pending for model use. Preserve source/figure/patient/plate lineage, original file hashes, exclusions and approval records. Keep official challenge examples out of training. Do not invent medical annotations, expert approval, license clearance, GPU measurements or performance results.

Use separate task/context inputs, preserve raw outputs, and compare each adapted model with its own unchanged base under matching conditions. Official evaluation details remain unresolved in the protocol register. Engineering and synthetic results are not leaderboard results.

Do not commit credentials, gated datasets, model weights, installed environments or newly generated raw data by accident. Private research inputs are available in the checksummed release asset and retain their upstream terms. Collaborator invitations grant repository access, not authorization to change source-use approvals.

Run python3 tools/team.py test, smoke, verify-evidence and verify-links as relevant before proposing changes. Optional native processor tests require the separately documented environment. Record command outcomes and failures; never discard disappointing experiments.
