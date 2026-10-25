"""Real biomedical source compilers tested with tiny synthetic containers."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from mmbu_phase1 import biomedical_sources, canonical
from mmbu_phase1.fields import ContractViolation


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


if __name__ == "__main__":
    unittest.main()
