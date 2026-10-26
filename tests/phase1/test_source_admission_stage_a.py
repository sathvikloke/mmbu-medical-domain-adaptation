"""Closed synthetic tests for the real-source Stage A declaration."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from mmbu_phase1 import canonical
from mmbu_phase1.source_admission_stage_a import (
    build_acquisition_packet,
    load_stage_a_config,
    validate_acquisition_packet,
    validate_stage_a_config,
    verify_inventory_opening,
)
from tests.phase1.admission_fixtures import AdmissionWorld


REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config/phase1/source-admission-stage-a.json"


class StageAConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def rejects(self, mutate) -> None:
        candidate = copy.deepcopy(self.config)
        mutate(candidate)
        with self.assertRaises(ValueError):
            validate_stage_a_config(candidate)

    def test_frozen_source_identities_and_roles(self):
        validated = load_stage_a_config(CONFIG)
        self.assertEqual(set(validated["sources"]), {"bus-bra", "pathmnist-224", "busi-whu"})
        self.assertEqual(
            validated["python_executable"],
            "/storage/groups/rrg_shared/hpc/Research/Code/mylibs/anaconda3/bin/python3",
        )
        self.assertEqual(validated["work_margin_bytes"], 20 * 1024**3)
        self.assertEqual(validated["sources"]["bus-bra"]["proposed_purposes"], ["release", "train"])
        self.assertEqual(validated["sources"]["pathmnist-224"]["proposed_purposes"], ["release", "train"])
        self.assertEqual(validated["sources"]["busi-whu"]["proposed_purposes"], ["confirmation", "release"])
        busi = {row["name"]: row for row in validated["sources"]["busi-whu"]["artifacts"]}
        self.assertEqual(busi["BUSI-WHU.zip"]["expected_bytes"], 128106790)
        self.assertEqual(
            busi["BUSI-WHU.zip"]["sha256"],
            "5d10c0bb931666e9cff48db9161febc0ec0c74e4b611c2edcbb9726f6d9d74cc",
        )
        self.assertEqual(busi["Patient_infos_BUSI-WHU.xlsx"]["expected_bytes"], 92017)
        self.assertEqual(
            busi["Patient_infos_BUSI-WHU.xlsx"]["sha256"],
            "14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44",
        )

    def test_duplicate_contract_is_exact(self):
        duplicate = validate_stage_a_config(self.config)["duplicate_method"]
        self.assertEqual(duplicate["perceptual_hash"], "dhash64")
        self.assertEqual(duplicate["maximum_hamming_distance"], 4)
        self.assertEqual(duplicate["maximum_aspect_ratio_delta"], 0.05)
        self.assertEqual(duplicate["missing_parent_policy"], "reject_record")

    def test_unknown_key_rejects(self):
        self.rejects(lambda value: value.update({"surprise": True}))

    def test_unmeasured_python_path_rejects(self):
        self.rejects(lambda value: value.update({"python_executable": "/usr/bin/python3"}))

    def test_glob_artifact_name_rejects(self):
        self.rejects(lambda value: value["sources"]["bus-bra"]["artifacts"][0].update({"name": "BUS*.zip"}))

    def test_duplicate_artifact_name_rejects(self):
        self.rejects(
            lambda value: value["sources"]["busi-whu"]["artifacts"].append(
                copy.deepcopy(value["sources"]["busi-whu"]["artifacts"][0])
            )
        )

    def test_unlisted_download_host_rejects(self):
        self.rejects(
            lambda value: value["sources"]["bus-bra"]["artifacts"][0].update(
                {"url": "https://unlisted.invalid/BUSBRA.zip"}
            )
        )

    def test_non_https_locator_rejects(self):
        self.rejects(lambda value: value["sources"]["bus-bra"]["canonical_locators"].__setitem__(0, "http://x.test"))

    def test_release_review_cannot_be_omitted(self):
        self.rejects(lambda value: value["sources"]["bus-bra"].update({"proposed_purposes": ["train"]}))

    def test_pathmnist_test_population_rejects(self):
        self.rejects(
            lambda value: value["sources"]["pathmnist-224"]["population"].update(
                {"allowed_splits": ["test", "train", "val"]}
            )
        )


class StageAPacketTests(unittest.TestCase):
    def setUp(self):
        self.config = load_stage_a_config(CONFIG)
        self.commit = "a" * 40
        self.launch_id = "20261025T183000Z-123e4567-e89b-42d3-a456-426614174000"
        self.run_root = f"/storage/scr/npl015/mmbu-admission/{self.launch_id}"
        self.created_at = "2026-10-25T18:30:00Z"
        self.packet = build_acquisition_packet(
            self.config, self.commit, self.launch_id, self.run_root, self.created_at
        )

    def changed_digest(self, mutate) -> None:
        candidate = copy.deepcopy(self.packet)
        mutate(candidate)
        candidate["record_digest"] = canonical.value_digest(
            {key: value for key, value in candidate.items() if key != "record_digest"}
        )
        self.assertNotEqual(candidate["record_digest"], self.packet["record_digest"])

    def test_packet_is_deterministic_and_binds_exact_launch(self):
        again = build_acquisition_packet(
            self.config, self.commit, self.launch_id, self.run_root, self.created_at
        )
        self.assertEqual(canonical.dumps(self.packet), canonical.dumps(again))
        self.assertEqual(self.packet["repository_commit"], self.commit)
        self.assertEqual(self.packet["launch_id"], self.launch_id)
        self.assertEqual(self.packet["run_root"], self.run_root)
        self.assertEqual(self.packet["config_digest"], canonical.value_digest(self.config))
        self.assertEqual(
            self.packet["forbidden_operations"],
            ["gpu_use", "mmbu_public_access", "model_loading", "retry_or_resume", "training", "upload_or_submit"],
        )
        validate_acquisition_packet(self.packet, self.config)

    def test_packet_binds_per_source_command_and_identity(self):
        for source_id, source in self.packet["sources"].items():
            command = source["retrieval_command"]
            self.assertEqual(
                command[0],
                "/storage/groups/rrg_shared/hpc/Research/Code/mylibs/anaconda3/bin/python3",
            )
            self.assertIn(f"{self.run_root}/repo/tools/source_admission_stage_a.py", command)
            self.assertEqual(command[-2:], ["--source-id", source_id])
            self.assertNotIn("--retry", command)
            self.assertNotIn("--continue-at", command)
            self.assertEqual(source["maximum_bytes"], self.config["sources"][source_id]["maximum_bytes"])
            self.assertEqual(
                [artifact["name"] for artifact in source["artifacts"]],
                [artifact["name"] for artifact in self.config["sources"][source_id]["artifacts"]],
            )

    def test_changed_command_rejects(self):
        self.changed_digest(lambda value: value["sources"]["bus-bra"]["retrieval_command"].append("--retry"))

    def test_changed_root_rejects(self):
        self.changed_digest(lambda value: value.update({"run_root": self.run_root + "-other"}))

    def test_changed_cap_rejects(self):
        self.changed_digest(lambda value: value["sources"]["bus-bra"].update({"maximum_bytes": 1}))

    def test_changed_purpose_rejects(self):
        self.changed_digest(lambda value: value["sources"]["bus-bra"].update({"proposed_purposes": ["train"]}))

    def test_changed_artifact_identity_rejects(self):
        self.changed_digest(lambda value: value["sources"]["busi-whu"]["artifacts"][0].update({"expected_bytes": 1}))

    def test_changed_repository_commit_rejects(self):
        self.changed_digest(lambda value: value.update({"repository_commit": "b" * 40}))

    def test_packet_file_has_distinct_full_file_sha256(self):
        payload = canonical.dumps(self.packet)
        self.assertEqual(len(hashlib.sha256(payload).hexdigest()), 64)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "packet.json"
            path.write_bytes(payload)
            self.assertEqual(path.read_bytes(), payload)


class StageACustodyTests(unittest.TestCase):
    def setUp(self):
        self.world = AdmissionWorld()
        self.records = list(self.world.records.values())

    def test_complete_chain_allows_only_inventory_opening(self):
        result = verify_inventory_opening(self.records, "syn-src", "2026-10-16T08:10:30Z")
        self.assertEqual(result["source"]["status"], "quarantined")
        self.assertEqual(result["split"]["role"], "quarantine")
        self.assertEqual(result["authorization"]["purpose"], "quarantine_inspection")
        self.assertEqual(result["opening"]["opening_kind"], "protected_access")
        self.assertEqual(result["manifest"]["source_id"], "syn-src")

    def test_missing_manifest_rejects(self):
        records = [row for row in self.records if row["schema_id"] != "mmbu.phase1.source_artifact_manifest"]
        with self.assertRaises(ValueError):
            verify_inventory_opening(records, "syn-src", "2026-10-16T08:10:30Z")

    def test_stale_opening_registry_rejects(self):
        records = [row for row in self.records if row.get("generation") != 1 or row["schema_id"] != "mmbu.phase1.opening_receipt_registry"]
        with self.assertRaises(ValueError):
            verify_inventory_opening(records, "syn-src", "2026-10-16T08:10:30Z")

    def test_wrong_source_rejects(self):
        with self.assertRaises(ValueError):
            verify_inventory_opening(self.records, "other-source", "2026-10-16T08:10:30Z")

    def test_opening_after_authorization_expiry_rejects(self):
        with self.assertRaises(ValueError):
            verify_inventory_opening(self.records, "syn-src", "2028-10-16T08:10:30Z")


if __name__ == "__main__":
    unittest.main()
