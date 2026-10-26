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
            "**Current state:** every named production boundary is executable and fail-closed; real external material remains absent",
            "repository records are not a trust anchor",
            "detached signature",
            "out-of-band pinned public-key fingerprint",
            "no fallback",
            "Stage A",
            "BUSI-WHU",
        ):
            self.assertIn(marker, requirement)
        self.assertIn("EXTERNAL_TRUST_ROOT_REQUIREMENT.md", current)

    def test_response_screen_is_portable_but_explicitly_non_promotional(self):
        report = (
            REPO / "docs/team/REPLICATED_RESPONSE_SCREEN_2026-10-25.md"
        ).read_text(encoding="utf-8")

        self.assertIn("**Checkout replay status:** available from a sealed, payload-minimized portable bundle", report)
        self.assertIn("**Promotion authority:** none", report)
        self.assertIn("raw predictions", report)
        self.assertIn("result receipts", report)
        self.assertIn("recomputes all 14 metrics", report)
        self.assertIn("cd62e3a67169434f29a3d710603d11ccaf851e1dcc529b54326b5dd2c8bd0e56", report)
        self.assertIn("excludes source images and archives", report)
        self.assertIn("cannot establish candidate priority", report)
        self.assertNotIn("makes the 9B Track 2 route the priority", report)
        self.assertNotIn("supports carrying Qwen3.5-9B", report)

    def test_current_verification_separates_current_and_historical_counts(self):
        report = (REPO / "docs/team/CURRENT_VERIFICATION.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("passed **645 Phase 1 CPU tests**", report)
        self.assertIn("| Current Phase 1 suite | **645 tests passed", report)
        self.assertNotIn("| Phase 1 suite | **623 tests passed", report)
        self.assertIn("**Status snapshot code revision (historical):**", report)
        self.assertNotIn("**Verified code revision:**", report)

        trust = (REPO / "docs/team/EXTERNAL_TRUST_ROOT_REQUIREMENT.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("verify_external_authority", trust)
        self.assertIn("source-admission-authority", trust)
        self.assertIn("every named production boundary is executable and fail-closed", trust)
        self.assertIn("confirmation-authority", trust)
        self.assertIn("verification must precede real artifact creation", trust)
        self.assertIn("before any network use", trust)
        self.assertIn("review-board-authority", trust)
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
