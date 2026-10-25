"""Real biomedical source compilers tested with tiny synthetic containers."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from mmbu_phase1 import biomedical_lane1, biomedical_sources, canonical
from mmbu_phase1.fields import ContractViolation


REPO = Path(__file__).resolve().parents[2]


LICENSE = """Copyright (c) 2023

Permission is hereby granted, free of charge, to any person obtaining a copy of this dataset.
All documents and papers that uses the Dataset are required to cite the BUS-BRA article.
"""


def _csv_bytes(fieldnames, rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _build_archive(path: Path, *, missing_image=False, pathology="benign", conflicting_fold=False):
    metadata = [
        {"ID": "bus_0001-l", "Case": "1", "Histology": "fibroadenoma", "Pathology": pathology,
         "BIRADS": "4", "Device": "unit", "Width": "100", "Height": "80", "Side": "left",
         "BBOX": "[10,20,30,40]"},
        {"ID": "bus_0001-r", "Case": "1", "Histology": "fibroadenoma", "Pathology": pathology,
         "BIRADS": "4", "Device": "unit", "Width": "100", "Height": "80", "Side": "right",
         "BBOX": "[11,21,31,41]"},
        {"ID": "bus_0002-s", "Case": "2", "Histology": "carcinoma", "Pathology": "malignant",
         "BIRADS": "5", "Device": "unit", "Width": "120", "Height": "90", "Side": "single",
         "BBOX": "[12,22,32,42]"},
        {"ID": "bus_0110-l", "Case": "110", "Histology": "fibroadenoma", "Pathology": "benign",
         "BIRADS": "3", "Device": "unit", "Width": "90", "Height": "70", "Side": "left",
         "BBOX": "[1,2,3,4]"},
        {"ID": "bus_0536-r", "Case": "536", "Histology": "fibroadenoma", "Pathology": "benign",
         "BIRADS": "3", "Device": "unit", "Width": "90", "Height": "70", "Side": "right",
         "BBOX": "[1,2,3,4]"},
    ]
    folds = [
        {"ID": "bus_0001-l", "Pathology": pathology, "kFold": "1"},
        {"ID": "bus_0001-r", "Pathology": pathology, "kFold": "2" if conflicting_fold else "1"},
        {"ID": "bus_0002-s", "Pathology": "malignant", "kFold": "5"},
        {"ID": "bus_0110-l", "Pathology": "benign", "kFold": "3"},
        {"ID": "bus_0536-r", "Pathology": "benign", "kFold": "4"},
    ]
    for row in folds:
        for index in range(1, 6):
            row[f"valid_{index}"] = "NaN" if row["kFold"] == str(index) else "1"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("BUSBRA/LICENSE.txt", LICENSE)
        archive.writestr("BUSBRA/bus_data.csv", _csv_bytes(biomedical_sources.BUSBRA_METADATA_COLUMNS, metadata))
        archive.writestr("BUSBRA/5-fold-cv.csv", _csv_bytes(
            ("ID", "Pathology", "kFold", "valid_1", "valid_2", "valid_3", "valid_4", "valid_5"), folds,
        ))
        for row in metadata:
            if missing_image and row["ID"] == "bus_0002-s":
                continue
            archive.writestr(f"BUSBRA/Images/{row['ID']}.png", b"not-real-pixels")


def _declaration(path: Path):
    raw = path.read_bytes()
    return {
        "archive_bytes": len(raw),
        "archive_md5": hashlib.md5(raw).hexdigest(),  # nosec: published dataset checksum
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "citation": "BUS-BRA article",
        "excluded_case_ids": ["110", "536"],
        "fold_member": "BUSBRA/5-fold-cv.csv",
        "image_member_template": "BUSBRA/Images/{record_id}.png",
        "license_member": "BUSBRA/LICENSE.txt",
        "license_required_phrases": [
            "All documents and papers that uses the Dataset",
            "Permission is hereby granted, free of charge",
        ],
        "metadata_member": "BUSBRA/bus_data.csv",
        "source_id": "busbra",
        "source_version": "1.0",
        "split_by_fold": {"1": "train", "2": "train", "3": "train", "4": "development", "5": "confirmation"},
    }


class BusbraCompilerTests(unittest.TestCase):
    def test_compiles_patient_safe_rows_and_source_provided_targets(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "BUSBRA.zip"
            _build_archive(path)
            result = biomedical_sources.compile_busbra(path, _declaration(path))

        self.assertEqual([row["row_id"] for row in result["rows"]],
                         ["bus_0001-l", "bus_0001-r", "bus_0002-s"])
        self.assertEqual([row["split"] for row in result["rows"]],
                         ["train", "train", "confirmation"])
        self.assertEqual(result["receipt"]["excluded_case_ids"], ["110", "536"])
        self.assertEqual(result["receipt"]["split_unit_counts"],
                         {"confirmation": 1, "development": 0, "train": 1})
        row = result["rows"][0]
        self.assertEqual(row["task_target"], "benign")
        self.assertEqual(row["context_target"], {
            "bbox_xywh": [10, 20, 30, 40], "birads": "4", "image_size": [100, 80], "side": "left",
        })
        self.assertEqual(row["context_target_text"], canonical.dumps(row["context_target"]).decode("utf-8"))
        self.assertEqual(row["independent_unit_id"], "busbra::case::1")
        self.assertFalse(result["receipt"]["mmbu_content_used"])

    def test_checksum_size_and_license_are_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "BUSBRA.zip"
            _build_archive(path)
            base = _declaration(path)
            mutations = (
                ("md5", lambda value: value.__setitem__("archive_md5", "0" * 32)),
                ("sha256", lambda value: value.__setitem__("archive_sha256", "0" * 64)),
                ("bytes", lambda value: value.__setitem__("archive_bytes", value["archive_bytes"] + 1)),
                ("license", lambda value: value["license_required_phrases"].append("not present")),
            )
            for label, mutate in mutations:
                value = dict(base)
                value["license_required_phrases"] = list(base["license_required_phrases"])
                mutate(value)
                with self.subTest(label=label), self.assertRaises(ContractViolation):
                    biomedical_sources.compile_busbra(path, value)

    def test_rejects_patient_leakage_missing_members_and_label_drift(self):
        cases = (("fold", {"conflicting_fold": True}),
                 ("image", {"missing_image": True}),
                 ("label", {"pathology": "uncertain"}))
        for label, options in cases:
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "BUSBRA.zip"
                _build_archive(path, **options)
                with self.subTest(label=label), self.assertRaises(ContractViolation):
                    biomedical_sources.compile_busbra(path, _declaration(path))

    def test_declaration_is_closed_and_exclusions_are_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "BUSBRA.zip"
            _build_archive(path)
            value = _declaration(path)
            value["surprise"] = True
            with self.assertRaises(ContractViolation):
                biomedical_sources.compile_busbra(path, value)
            value = _declaration(path)
            value["excluded_case_ids"] = ["110"]
            with self.assertRaises(ContractViolation):
                biomedical_sources.compile_busbra(path, value)


def _npy(descr, shape, payload):
    header = repr({"descr": descr, "fortran_order": False, "shape": shape}).encode("ascii")
    padding = (16 - ((10 + len(header) + 1) % 16)) % 16
    header += b" " * padding + b"\n"
    return b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header)) + header + payload


def _build_pathmnist(path: Path, *, bad_label=False):
    counts = {"train": 3, "val": 2, "test": 1}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        for split, count in counts.items():
            archive.writestr(f"{split}_images.npy", _npy("|u1", (count, 2, 2, 3), bytes(count * 12)))
            labels = [0, 8, 3][:count]
            if split == "test":
                labels = [9 if bad_label else 1]
            elif split == "val":
                labels = [2, 7]
            payload = b"".join(struct.pack("<q", value) for value in labels)
            archive.writestr(f"{split}_labels.npy", _npy("<i8", (count, 1), payload))


def _pathmnist_declaration(path: Path):
    raw = path.read_bytes()
    return {
        "archive_bytes": len(raw),
        "archive_md5": hashlib.md5(raw).hexdigest(),  # nosec: published dataset checksum
        "citation": "MedMNIST article",
        "download_url": "https://example.invalid/pathmnist.npz",
        "image_shape": [2, 2, 3],
        "labels": [
            "adipose", "background", "debris", "lymphocytes", "mucus", "smooth muscle",
            "normal colon mucosa", "cancer-associated stroma", "colorectal adenocarcinoma epithelium",
        ],
        "license_id": "CC-BY-4.0",
        "sample_counts": {"test": 1, "train": 3, "val": 2},
        "source_id": "pathmnist",
        "source_version": "3",
        "split_roles": {"test": "confirmation", "train": "train", "val": "development"},
        "status": "acquisition_pending",
    }


class PathmnistCompilerTests(unittest.TestCase):
    def test_compiles_official_partitions_without_reading_image_payloads(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pathmnist_224.npz"
            _build_pathmnist(path)
            result = biomedical_sources.compile_pathmnist(path, _pathmnist_declaration(path))
        self.assertEqual(len(result["rows"]), 6)
        self.assertEqual(result["receipt"]["split_row_counts"],
                         {"confirmation": 1, "development": 2, "train": 3})
        self.assertEqual(result["rows"][0]["row_id"], "pathmnist::test::0")
        self.assertEqual(result["rows"][0]["task_target"], "background")
        self.assertIsNone(result["rows"][0]["context_target"])
        self.assertEqual(result["rows"][-1]["row_id"], "pathmnist::val::1")
        self.assertFalse(result["receipt"]["mmbu_content_used"])

    def test_rejects_checksum_shape_count_and_label_drift(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pathmnist_224.npz"
            _build_pathmnist(path)
            mutations = (
                ("checksum", lambda value: value.__setitem__("archive_md5", "0" * 32)),
                ("shape", lambda value: value.__setitem__("image_shape", [4, 4, 3])),
                ("count", lambda value: value["sample_counts"].__setitem__("train", 4)),
            )
            for label, mutate in mutations:
                value = _pathmnist_declaration(path)
                value["sample_counts"] = dict(value["sample_counts"])
                mutate(value)
                with self.subTest(label=label), self.assertRaises(ContractViolation):
                    biomedical_sources.compile_pathmnist(path, value)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pathmnist_224.npz"
            _build_pathmnist(path, bad_label=True)
            with self.assertRaises(ContractViolation):
                biomedical_sources.compile_pathmnist(path, _pathmnist_declaration(path))


class BiomedicalLaneTests(unittest.TestCase):
    def _rows(self):
        rows = []
        for source in ("busbra", "pathmnist"):
            for split, count in (("train", 5), ("development", 4), ("confirmation", 3)):
                for index in range(count):
                    context = ({"bbox_xywh": [0, 0, 5, 5], "birads": "4", "image_size": [10, 10],
                                "side": "left"} if source == "busbra" else None)
                    rows.append({
                        "context_prompt": "context" if context else None,
                        "context_target": context,
                        "context_target_text": canonical.dumps(context).decode() if context else None,
                        "independent_unit_id": f"{source}::{split}::{index}",
                        "row_id": f"{source}::{split}::{index}",
                        "source_id": source,
                        "split": split,
                        "task_prompt": "task",
                        "task_target": "benign" if source == "busbra" else "adipose",
                    })
        return rows

    def test_sampling_is_balanced_deterministic_and_confirmation_closed(self):
        left = biomedical_lane1.select_rows(self._rows(), split="train", per_source=3, seed=19)
        right = biomedical_lane1.select_rows(list(reversed(self._rows())), split="train", per_source=3, seed=19)
        self.assertEqual(left, right)
        self.assertEqual({source: sum(row["source_id"] == source for row in left)
                          for source in ("busbra", "pathmnist")}, {"busbra": 3, "pathmnist": 3})
        self.assertTrue(all(row["split"] == "train" for row in left))
        self.assertEqual(len({row["independent_unit_id"] for row in left}), len(left))
        with self.assertRaises(ContractViolation):
            biomedical_lane1.select_rows(self._rows(), split="confirmation", per_source=1, seed=19)

    def test_view_mass_is_one_and_missing_context_is_not_fabricated(self):
        busbra, path = self._rows()[0], next(row for row in self._rows() if row["source_id"] == "pathmnist")
        self.assertEqual(biomedical_lane1.training_views(busbra, "task"),
                         (("task", "task", "benign", {"denominator": 1, "numerator": 1}),))
        dual = biomedical_lane1.training_views(busbra, "dual")
        self.assertEqual([item[0] for item in dual], ["task", "context"])
        self.assertEqual([item[3] for item in dual],
                         [{"denominator": 4, "numerator": 3}, {"denominator": 4, "numerator": 1}])
        self.assertEqual(biomedical_lane1.training_views(path, "dual"),
                         (("task", "task", "adipose", {"denominator": 1, "numerator": 1}),))

    def test_metrics_are_source_stratified_and_context_strict(self):
        rows = [self._rows()[0], next(row for row in self._rows() if row["source_id"] == "pathmnist")]
        predictions = [
            {"context": '{"bbox_xywh":[0,0,5,5],"birads":"4","image_size":[10,10],"side":"left"}',
             "row_id": rows[0]["row_id"], "task": "Benign."},
            {"context": None, "row_id": rows[1]["row_id"], "task": "wrong"},
        ]
        metrics = biomedical_lane1.score_predictions(rows, predictions)
        self.assertEqual(metrics["answer_macro_accuracy"], {"denominator": 2, "numerator": 1})
        self.assertEqual(metrics["answer_by_source"]["busbra"], {"denominator": 1, "numerator": 1})
        self.assertEqual(metrics["answer_by_source"]["pathmnist"], {"denominator": 1, "numerator": 0})
        self.assertEqual(metrics["context_macro_score"], {"denominator": 1, "numerator": 1})
        predictions[0]["context"] = "not json"
        self.assertEqual(biomedical_lane1.score_predictions(rows, predictions)["context_macro_score"],
                         {"denominator": 1, "numerator": 0})


class NativeEnvelopeTests(unittest.TestCase):
    def test_native_config_preserves_red_lines_and_five_arms(self):
        path = REPO / "tools/lane1_native_biomedical.py"
        spec = importlib.util.spec_from_file_location("lane1_native_biomedical_for_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        config = canonical.loads((REPO / "config/phase1/biomedical-lane1-shakedown.json").read_bytes())
        self.assertEqual(module.validate_config(config), config)
        self.assertEqual(config["authorization"]["prohibited_actions"],
                         ["final_submission", "mmbu_public_set_evaluation", "upload"])
        self.assertEqual(config["allowed_arms"], [arm["candidate_id"] for arm in module.ARMS])

    def test_slurm_envelopes_are_bounded_and_gpu_jobs_are_offline(self):
        acquisition = (REPO / "tools/prepare_biomedical_sources.sbatch").read_text()
        native = (REPO / "tools/lane1_native_biomedical.sbatch").read_text()
        self.assertIn("#SBATCH --array=0-4%5", native)
        self.assertIn("#SBATCH --gres=gpu:tesla_a100_80gb:1", native)
        self.assertIn("HF_HUB_OFFLINE=1", native)
        self.assertIn("TRANSFORMERS_OFFLINE=1", native)
        self.assertEqual(native.count("lane1_native_biomedical.py"), 1)
        self.assertNotIn("sbatch ", native)
        self.assertNotIn("--gres=gpu", acquisition)
        self.assertEqual(acquisition.count("prepare_biomedical_portfolio.py"), 1)
if __name__ == "__main__":
    unittest.main()
