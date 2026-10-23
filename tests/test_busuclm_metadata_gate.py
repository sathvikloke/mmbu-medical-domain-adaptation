import csv
import io
import unittest


ROOT = "BUS-UCLM Breast ultrasound lesion segmentation dataset/BUS-UCLM/"
FIELDS = ["Image", "Resolution", "Label", "Doppler", "Marks", "Combined"]


def metadata(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, delimiter=";", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def row(image, label, *, doppler="No", marks="No", combined="No"):
    return {"Image": image, "Resolution": "856x606", "Label": label,
            "Doppler": doppler, "Marks": marks, "Combined": combined}


def inventory(images, *, extra=()):
    names = [ROOT + "INFO.csv"]
    names += [ROOT + "images/" + name for name in images]
    names += [ROOT + "masks/" + name for name in images]
    names += list(extra)
    return [{"name": name, "file_size": 10, "compress_size": 8, "crc32": "0123abcd"}
            for name in names]


class BusuclmMetadataGateTests(unittest.TestCase):
    def test_closes_patient_image_mask_inventory_and_preserves_schema_anomaly(self):
        from tools.busuclm_metadata_gate import audit_metadata
        payload = metadata([
            row("ABCD_000.png", "Normal"),
            row("ABCD_001.png", "Benign", doppler="Y", marks="Yes"),
            row("WXYZ_000.png", "Malignant", doppler="Yes", combined="Yes"),
        ])

        receipt = audit_metadata(payload, inventory(
            ["ABCD_000.png", "ABCD_001.png", "WXYZ_000.png"]))

        self.assertEqual(receipt["record_count"], 3)
        self.assertEqual(receipt["patient_count"], 2)
        self.assertEqual(receipt["archive_bytes"], 336_713_241)
        self.assertEqual(receipt["archive_etag"], '"66fea5503ae433b324be1cbf54ca8866"')
        self.assertEqual(receipt["source_doi"], "10.17632/7fvgj4jsp7.3")
        self.assertEqual(receipt["label_counts"], {"Benign": 1, "Malignant": 1, "Normal": 1})
        self.assertEqual(receipt["patient_label_set_counts"], {
            "Benign|Normal": 1, "Malignant": 1})
        self.assertTrue(receipt["inventory_clearance"])
        self.assertEqual(receipt["noncanonical_values"], [{
            "column": "Doppler", "count": 1, "value": "Y"}])
        self.assertFalse(receipt["schema_clearance"])
        self.assertEqual(receipt["license_disposition"], "conflict_blocks_model_use")
        self.assertFalse(receipt["training_ready"])
        self.assertFalse(receipt["model_use_authorized"])

    def test_duplicate_metadata_or_inventory_and_missing_pairs_fail_closed(self):
        from tools.busuclm_metadata_gate import audit_metadata
        one = row("ABCD_000.png", "Normal")
        cases = [
            (metadata([one, one]), inventory(["ABCD_000.png"])),
            (metadata([one]), inventory(["ABCD_000.png"], extra=[ROOT + "images/ABCD_000.png"])),
            (metadata([one]), inventory([])),
            (metadata([one]), inventory(["ABCD_000.png"], extra=["../escape.png"])),
        ]
        for payload, members in cases:
            with self.subTest(members=members), self.assertRaises(ValueError):
                audit_metadata(payload, members)

    def test_unknown_columns_values_and_bad_names_reject(self):
        from tools.busuclm_metadata_gate import audit_metadata
        bad_payloads = [
            metadata([row("abcd_000.png", "Normal")]),
            metadata([row("ABCD_000.jpg", "Normal")]),
            metadata([row("ABCD_000.png", "Unknown")]),
            metadata([{**row("ABCD_000.png", "Normal"), "Resolution": "0x606"}]),
        ]
        for payload in bad_payloads:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                audit_metadata(payload, inventory(["ABCD_000.png"]))


if __name__ == "__main__":
    unittest.main()
