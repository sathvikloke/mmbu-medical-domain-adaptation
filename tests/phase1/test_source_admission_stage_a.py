"""Closed synthetic tests for the real-source Stage A declaration."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from mmbu_phase1.source_admission_stage_a import load_stage_a_config, validate_stage_a_config


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


if __name__ == "__main__":
    unittest.main()
