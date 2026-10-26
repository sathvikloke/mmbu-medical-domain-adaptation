from pathlib import Path
import json
import unittest


REPO = Path(__file__).resolve().parents[2]


class EvidenceDocumentationTests(unittest.TestCase):
    def test_pathmnist_author_reply_is_retained_without_overclaiming(self):
        receipt_path = (
            REPO
            / "outputs/source-clarification-replies/pathmnist-medmnist-2026-10-26.json"
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        outreach = (REPO / "docs/team/SOURCE_CLARIFICATION_OUTREACH.md").read_text(
            encoding="utf-8"
        )
        limitation = (
            REPO / "docs/team/PATHMNIST_MAPPING_LIMITATION_2026-10-25.md"
        ).read_text(encoding="utf-8")
        decisions = (REPO / "docs/team/DECISIONS.md").read_text(encoding="utf-8")

        self.assertEqual(receipt["gmail_message_id"], "1a179e583ff85cd4")
        self.assertEqual(receipt["sender"], "Jiancheng Yang <jiancheng.yang@aalto.fi>")
        self.assertEqual(receipt["authentication"]["dkim"], "pass")
        self.assertEqual(receipt["authentication"]["dmarc"], "pass")
        self.assertIn("original patch ID", receipt["response_text"])
        self.assertIn("contact the original NCT-CRC-HE-100K authors", receipt["response_text"])
        self.assertFalse(receipt["decision_projection"]["slide_or_patient_mapping_supplied"])
        self.assertFalse(receipt["decision_projection"]["source_admitted"])

        self.assertIn("Reply received October 26, 2026", outreach)
        self.assertIn("does not supply slide/patient IDs", outreach)
        self.assertIn("author reply", limitation)
        self.assertIn("PathMNIST remains blocked", decisions)
        self.assertNotIn("PathMNIST/NCT-CRC questions were sent on October 23 and remain pending", decisions)

        route = json.loads(
            (
                REPO
                / "outputs/source-clarification-replies/nct-crc-corrected-route-2026-10-26.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(route["automatic_reply_message_id"], "1a16c3494ae67966")
        self.assertEqual(route["corrected_recipient"], "jakob.kather@med.uni-heidelberg.de")
        self.assertEqual(route["corrected_send_message_id"], "1a179efa3c999283")
        self.assertFalse(route["decision_projection"]["source_author_answer_received"])

        source_reply = json.loads(
            (
                REPO
                / "outputs/source-clarification-replies/nct-crc-author-2026-10-26.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(source_reply["gmail_message_id"], "1a179f213cbb6ab6")
        self.assertEqual(source_reply["authentication"], {"dkim": "pass", "dmarc": "pass", "spf": "pass"})
        self.assertEqual(source_reply["response_text"], "unfortuantley no...\n\nbest wishes\n\nJakob")
        self.assertFalse(source_reply["decision_projection"]["public_parent_mapping_available"])
        self.assertTrue(source_reply["decision_projection"]["pathmnist_decision_use_closed"])
        self.assertFalse(source_reply["decision_projection"]["source_admitted"])
        self.assertIn("Original source lead reply received October 26, 2026", outreach)
        self.assertIn("no public patch-to-slide/patient mapping is available", outreach)
        self.assertIn("original source lead", limitation)
        self.assertIn("closed negatively", limitation)

        chest_outreach = json.loads(
            (
                REPO
                / "outputs/source-clarification-replies/chestmnist-reviewer-outreach-2026-10-26.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(chest_outreach["gmail_message_id"], "1a17a2027a0fea00")
        self.assertEqual(chest_outreach["recipient"], "Conor Lowry, MD <conor.lowry@uky.edu>")
        self.assertFalse(chest_outreach["decision_projection"]["reviewer_agreement_received"])
        self.assertFalse(chest_outreach["decision_projection"]["source_admitted"])
        self.assertIn("ChestMNIST positive-label QA", outreach)
        self.assertIn("No agreement or review authority exists", outreach)

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

        self.assertIn("passed **654 Phase 1 CPU tests**", report)
        self.assertIn("| Current Phase 1 suite | **654 tests passed", report)
        self.assertIn("20,384 official NIH test images", report)
        self.assertIn("no public patch-to-slide/patient mapping", report)
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
