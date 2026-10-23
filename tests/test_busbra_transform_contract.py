import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path


def seal(value):
    unsigned = copy.deepcopy(value)
    unsigned.pop("receipt_digest", None)
    value["receipt_digest"] = hashlib.sha256(json.dumps(
        unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("ascii")).hexdigest()
    return value


def corpus():
    return seal({
        "schema": "mmbu.busbra.quarantine_corpus_audit_receipt.v1",
        "source_id": "busbra", "source_version": "1.0",
        "archive_bytes": 133917740, "archive_md5": "1f8b2be6476d58fc97bfb5e5a1ea9bab",
        "metadata_sha256": "f218d0f10b0aeeb14ff4b2cfed8631b2f4a7cf608e564548b35bddd55f3aafb3",
        "record_count": 2, "case_count": 2, "ok": True,
        "image_mode_counts": {"L": 2}, "mask_mode_counts": {"1": 2},
        "exact_image_duplicate_clearance": True, "exact_image_duplicate_groups": [],
        "exact_mask_duplicate_clearance": True, "exact_mask_duplicate_groups": [],
        "metadata_dimension_clearance": False,
        "metadata_dimension_mismatches": [{"record_id": "bus_0001-l", "declared_width": 20,
            "declared_height": 30, "actual_width": 20, "actual_height": 29}],
        "bbox_iou_below_0_95": 1, "bbox_iou_below_0_95_records": [{
            "record_id": "bus_0002-r", "metadata_bbox_xywh": [1, 1, 5, 5],
            "mask_bbox_xywh": [2, 2, 3, 3], "bbox_iou": 0.36}],
        "bbox_iou_min": 0.36, "bbox_iou_max": 1.0,
        "pathology_counts": {"benign": 2}, "birads_counts": {"2": 2},
        "near_duplicate_clearance": False, "medical_correctness_reviewed": False,
        "source_proximity_reviewed": False, "structural_clearance": False,
        "training_ready": False, "model_executed": False, "model_use_authorized": False,
        "limitations": ["fixture"],
    })


def triage():
    return seal({
        "schema": "mmbu.busbra.near_duplicate_triage_receipt.v1",
        "source_id": "busbra", "source_version": "1.0",
        "archive_bytes": 133917740, "archive_md5": "1f8b2be6476d58fc97bfb5e5a1ea9bab",
        "metadata_sha256": "f218d0f10b0aeeb14ff4b2cfed8631b2f4a7cf608e564548b35bddd55f3aafb3",
        "algorithm": "fixture-dhash", "fingerprint_count": 2,
        "fingerprints_sha256": "0" * 64, "max_distance": 4,
        "max_aspect_ratio_difference": 0.05, "low_information_fingerprint_count": 0,
        "candidate_count": 1, "cross_case_candidate_count": 1,
        "cross_pathology_candidate_count": 0,
        "candidates": [{"case_ids": ["1", "2"], "record_ids": ["bus_0001-l", "bus_0002-r"],
            "pathologies": ["benign", "benign"], "cross_case": True,
            "cross_pathology": False, "exact_decoded_match": False,
            "exact_raw_match": False, "hamming_distance": 4,
            "relative_aspect_difference": 0.01,
            "reason": "perceptual_candidate_requires_review"}],
        "automatic_merge_or_exclusion": False,
        "absence_of_near_duplicates_certified": False,
        "training_ready": False, "model_executed": False, "model_use_authorized": False,
        "limitations": ["fixture"],
    })


class BusbraTransformContractTests(unittest.TestCase):
    def test_receipt_loader_rejects_duplicate_keys_and_nonfinite_numbers(self):
        from tools.busbra_transform_contract import _load_json
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            for payload in ('{"schema":"a","schema":"b"}', '{"value":NaN}'):
                path.write_text(payload, encoding="utf-8")
                with self.subTest(payload=payload), self.assertRaises(ValueError):
                    _load_json(path)

    def test_uses_decoded_geometry_and_conservatively_links_candidate_cases(self):
        from tools.busbra_transform_contract import build_contract
        contract = build_contract(corpus(), triage())
        self.assertEqual(contract["canonical_dimensions"], "decoded_image_dimensions")
        self.assertEqual(contract["localization_target"],
                         "tight_half_open_xywh_from_binary_mask_foreground")
        self.assertEqual(contract["qa_only_metadata_fields"], ["BBOX", "Height", "Width"])
        self.assertEqual(contract["linked_case_groups"], [["1", "2"]])
        self.assertTrue(contract["structural_transform_clearance"])
        self.assertFalse(contract["medical_correctness_reviewed"])
        self.assertFalse(contract["training_ready"])
        self.assertFalse(contract["model_use_authorized"])

    def test_rejects_tampering_duplicates_or_authority_escalation(self):
        from tools.busbra_transform_contract import build_contract
        cases = []
        bad = corpus(); bad["record_count"] = 3; cases.append((bad, triage()))
        bad = corpus(); bad["exact_image_duplicate_clearance"] = False; seal(bad); cases.append((bad, triage()))
        bad = triage(); bad["automatic_merge_or_exclusion"] = True; seal(bad); cases.append((corpus(), bad))
        bad = triage(); bad["model_use_authorized"] = True; seal(bad); cases.append((corpus(), bad))
        for left, right in cases:
            with self.subTest(left=left, right=right), self.assertRaises(ValueError):
                build_contract(left, right)

    def test_rejects_unordered_or_overlapping_linkage_claims(self):
        from tools.busbra_transform_contract import build_contract
        bad = triage()
        bad["candidates"].append(copy.deepcopy(bad["candidates"][0]))
        bad["candidate_count"] = 2
        bad["cross_case_candidate_count"] = 2
        seal(bad)
        with self.assertRaises(ValueError):
            build_contract(corpus(), bad)

    def test_rejects_incomplete_exception_or_candidate_populations(self):
        from tools.busbra_transform_contract import build_contract
        cases = []
        bad = corpus()
        bad["bbox_iou_below_0_95"] = 2
        seal(bad)
        cases.append((bad, triage()))
        bad = corpus()
        bad["metadata_dimension_mismatches"].append(
            copy.deepcopy(bad["metadata_dimension_mismatches"][0]))
        seal(bad)
        cases.append((bad, triage()))
        bad = triage()
        bad["cross_case_candidate_count"] = 0
        seal(bad)
        cases.append((corpus(), bad))
        bad = corpus()
        bad["record_count"] = True
        bad["case_count"] = True
        bad["image_mode_counts"] = {"L": True}
        bad["mask_mode_counts"] = {"1": True}
        seal(bad)
        bad_triage = triage()
        bad_triage["fingerprint_count"] = True
        bad_triage["candidate_count"] = True
        bad_triage["cross_case_candidate_count"] = True
        seal(bad_triage)
        cases.append((bad, bad_triage))
        for left, right in cases:
            with self.subTest(left=left, right=right), self.assertRaises(ValueError):
                build_contract(left, right)


if __name__ == "__main__":
    unittest.main()
