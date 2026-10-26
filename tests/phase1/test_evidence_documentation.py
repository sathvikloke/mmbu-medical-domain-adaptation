from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[2]


class EvidenceDocumentationTests(unittest.TestCase):
    def test_remote_only_response_screen_is_explicitly_non_replayable(self):
        report = (
            REPO / "docs/team/REPLICATED_RESPONSE_SCREEN_2026-10-25.md"
        ).read_text(encoding="utf-8")

        self.assertIn("**Checkout replay status:** unavailable", report)
        self.assertIn("**Promotion authority:** none", report)
        self.assertIn("raw predictions", report)
        self.assertIn("result receipts", report)
        self.assertIn("must be imported and hash-verified", report)

    def test_current_verification_separates_current_and_historical_counts(self):
        report = (REPO / "docs/team/CURRENT_VERIFICATION.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("passed **627 Phase 1 CPU tests**", report)
        self.assertIn("| Current Phase 1 suite | **627 tests passed", report)
        self.assertNotIn("| Phase 1 suite | **623 tests passed", report)
        self.assertIn("**Status snapshot code revision (historical):**", report)
        self.assertNotIn("**Verified code revision:**", report)


if __name__ == "__main__":
    unittest.main()
