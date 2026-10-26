from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[2]


class EvidenceDocumentationTests(unittest.TestCase):
    def test_external_trust_root_requirement_is_explicit_and_non_self_authorizing(self):
        requirement = (
            REPO / "docs/team/EXTERNAL_TRUST_ROOT_REQUIREMENT.md"
        ).read_text(encoding="utf-8")
        current = (REPO / "docs/team/CURRENT_VERIFICATION.md").read_text(
            encoding="utf-8"
        )

        for marker in (
            "**Current state:** protected BUSI-WHU and Stage A structural opening bound; remaining boundaries and external material blocked",
            "repository records are not a trust anchor",
            "detached signature",
            "out-of-band pinned public-key fingerprint",
            "no fallback",
            "Stage A",
            "BUSI-WHU",
        ):
            self.assertIn(marker, requirement)
        self.assertIn("EXTERNAL_TRUST_ROOT_REQUIREMENT.md", current)

    def test_remote_only_response_screen_is_explicitly_non_replayable(self):
        report = (
            REPO / "docs/team/REPLICATED_RESPONSE_SCREEN_2026-10-25.md"
        ).read_text(encoding="utf-8")

        self.assertIn("**Checkout replay status:** unavailable", report)
        self.assertIn("**Promotion authority:** none", report)
        self.assertIn("raw predictions", report)
        self.assertIn("result receipts", report)
        self.assertIn("must be imported and hash-verified", report)
        self.assertIn("cannot establish candidate priority", report)
        self.assertNotIn("makes the 9B Track 2 route the priority", report)
        self.assertNotIn("supports carrying Qwen3.5-9B", report)

    def test_current_verification_separates_current_and_historical_counts(self):
        report = (REPO / "docs/team/CURRENT_VERIFICATION.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("passed **636 Phase 1 CPU tests**", report)
        self.assertIn("| Current Phase 1 suite | **636 tests passed", report)
        self.assertNotIn("| Phase 1 suite | **623 tests passed", report)
        self.assertIn("**Status snapshot code revision (historical):**", report)
        self.assertNotIn("**Verified code revision:**", report)

        trust = (REPO / "docs/team/EXTERNAL_TRUST_ROOT_REQUIREMENT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("verify_external_authority", trust)
        self.assertIn("Acquisition authority,\ncompleted-review authentication, source admission, and confirmation are not yet bound", trust)
        self.assertIn("plain prose and hard-coded names are rejected", trust)
        self.assertIn("no protected opening or decision-bearing action is enabled", trust)

        confirmation = (
            REPO / "docs/team/BUSI_WHU_CONFIRMATION_READINESS_2026-10-25.md"
        ).read_text(encoding="utf-8")
        self.assertIn("selection_authority=none", confirmation)
        self.assertIn("No model or track is currently selected", confirmation)
        self.assertNotIn("development evidence still supports Qwen3.5-9B", confirmation)

        historical_audit = (
            REPO / "docs/team/INDEPENDENT_PROJECT_AUDIT_2026-10-26.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Historical snapshot, superseded for current decisions", historical_audit)
        self.assertIn("zero current model-selection or promotion authority", historical_audit)


if __name__ == "__main__":
    unittest.main()
