import copy
from pathlib import Path
import tempfile
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.machine_local_evidence import (
    load_manifest,
    verify_machine_local_roots,
)


REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "config/phase1/machine-local-evidence-roots-2026-10-26.json"
CURRENT_VERIFICATION = REPO / "docs/team/CURRENT_VERIFICATION.md"


class MachineLocalEvidenceTests(unittest.TestCase):
    def test_checked_manifest_is_closed_and_local_roots_match_when_present(self):
        manifest = load_manifest(MANIFEST)
        statuses = verify_machine_local_roots(manifest, REPO)

        self.assertEqual(len(statuses), 6)
        expected_statuses = {
            row["path"]: "matched" if (REPO / row["path"]).exists() else "absent"
            for row in manifest["roots"]
        }
        self.assertEqual(
            {row["path"]: row["status"] for row in statuses},
            expected_statuses,
        )
        self.assertTrue(all(row["authority"] == "none" for row in statuses))
        verification = CURRENT_VERIFICATION.read_text(encoding="utf-8")
        normalized_verification = " ".join(verification.split())
        self.assertIn("../../config/phase1/machine-local-evidence-roots-2026-10-26.json", verification)
        self.assertIn("machine-local and unversioned", normalized_verification)
        self.assertIn("zero source-admission, model-selection, or promotion authority", normalized_verification)

    def test_drift_rejects_and_absence_never_becomes_evidence(self):
        manifest = load_manifest(MANIFEST)
        with tempfile.TemporaryDirectory() as folder:
            checkout = Path(folder)
            root = checkout / "local-evidence"
            root.mkdir()
            payload = b"machine-local evidence fixture"
            (root / "receipt.json").write_bytes(payload)
            fixture_manifest = canonical.seal({
                "schema_id": "mmbu.phase1.machine_local_evidence_roots",
                "schema_version": 1,
                "classification": "machine_local_unversioned",
                "excluded_patterns": ["**/__pycache__/**", "**/*.pyc"],
                "roots": [{
                    "path": "local-evidence",
                    "file_count": 1,
                    "total_bytes": len(payload),
                    "inventory_digest": canonical.value_digest([{
                        "path": "receipt.json",
                        "bytes": len(payload),
                        "sha256": canonical.raw_digest(payload),
                    }]),
                    "authority": "none",
                }],
            })
            statuses = verify_machine_local_roots(fixture_manifest, checkout)
            self.assertEqual({row["status"] for row in statuses}, {"matched"})

            changed = copy.deepcopy(fixture_manifest)
            changed["roots"][0]["file_count"] += 1
            changed = canonical.seal(
                {key: value for key, value in changed.items() if key != "record_digest"}
            )
            with self.assertRaises(ContractViolation):
                verify_machine_local_roots(changed, checkout)

        statuses = verify_machine_local_roots(manifest, REPO / "missing-checkout")
        self.assertEqual({row["status"] for row in statuses}, {"absent"})
        self.assertTrue(all(row["authority"] == "none" for row in statuses))


if __name__ == "__main__":
    unittest.main()
