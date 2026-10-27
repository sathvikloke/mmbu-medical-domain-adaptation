# BUS-BRA offline reviewer design

## Intent

Reduce the manual burden of completing the frozen 108-record BUS-BRA train-only visual/annotation review without
uploading biomedical images, changing the immutable packet, or turning interface state into scientific authority.

## Product

`tools/busbra_train_review_ui.py` accepts one immutable train-only packet directory plus its expected receipt digest and
creates one new self-contained HTML file. Generation first runs the repository's existing packet verification. The HTML
embeds receipt-bound PNGs as data URLs, freezes record identity fields, shows image and mask side by side, collects only
the existing `VISUAL_FIELDS`, shows completion progress, saves/loads a local JSON draft, and exports the exact CSV
accepted by `busbra_train_qa.py validate`.

The page uses no network, server, cookies, analytics, model, or external library. A restrictive content-security policy
permits only its embedded style, script, and image data. Output publication is no-overwrite and atomic at the file level.

## Required behavior

- Reject an invalid/tampered packet or wrong expected receipt digest before writing output.
- Reject symbolic-link or non-PNG review assets and bind every embedded asset to its frozen record.
- Render all 108 records in manifest order with immutable identity, selection role, and mandatory reasons.
- Collect the validator's closed vocabularies and pipe-delimited target set without inventing labels.
- Mark adverse, uncertain, excluded, or escalated rows as requiring notes.
- Refuse final CSV export until every row is complete and consistent.
- Export the exact `VISUAL_FIELDS` header and one row per frozen record.
- Save and load a versioned JSON draft containing only reviewer-entered fields and the packet receipt digest.
- Preserve `source_admission_authorized=false`, `training_ready=false`, and `model_use_authorized=false` in visible copy.

## Non-goals

- No medical, clinical, rights, provenance, admission, or purpose decision.
- No rights-review UI; the separate rights template remains controlling.
- No packet modification, source archive access, model execution, MMBU-public access, upload, or submission.
- No automatic image interpretation, suggestions, defaults, or completion.

## Security and evidence boundary

All source strings are escaped before entering HTML. The generated page performs no request. Draft JSON is convenience
state only and is not accepted by the admission validator. Only an exported CSV completed by an accountable human after
a digest-bound opening may enter the existing validator, which rechecks the immutable packet and timestamps.
