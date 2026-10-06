# Version 0.2 release notes

This release adds deterministic real-source conversion inspection, paired model comparison arithmetic and optional image decoding to the original CPU preparation package. No model was run, no training source was approved and no leaderboard result was produced.

New commands: `compare`, `inspect-images`, and `prepare-bbbc039`. The image commands use the optional Pillow dependency. The core remains usable without installed third-party packages. New detailed docs explain the exact input contracts, unsupported transformations and interpretation limits.

The single-candidate bootstrap fixes numerical underflow from multiplying very small source and row weights before normalization. A hand-calculated regression demonstrates the previous failure and verifies the repair. The prior archive `mmbu-precompute.zip` is retained as historical version 0.1; use `mmbu-precompute-v0.2.zip` for new work.

The source quarantine is outside the archive. Portable evidence contains raw archive hashes, aggregate conversion results, a 100-field pending-review queue, decoder and geometry oracle results, and original defect dispositions. All fields in the actual source training partition remain represented in the pending count inventory. Empty-mask detection targets remain uncreated until their contract is decided.

Separate reviewers checked the converter against an independently written run-union oracle, the joint comparison against rational arithmetic and shared-draw reconstruction, image precision/safety using adversarial files, and model metadata using independent arithmetic. Final source hashes and verification logs distinguish the reviewed code from the earlier historical reports. Passing software tests does not replace biomedical annotation review, source eligibility review, organizer protocol confirmation or GPU runtime validation.
