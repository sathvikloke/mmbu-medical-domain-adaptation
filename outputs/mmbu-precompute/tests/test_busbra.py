import csv
import hashlib
import io
import json
import unittest


def api():
    from mmbu_prep.busbra import build_sample_plan
    return build_sample_plan


FIELDS = ["ID", "Case", "Histology", "Pathology", "BIRADS", "Device", "Width", "Height", "Side", "BBOX"]


def metadata(rows, *, extra_fields=()):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS + list(extra_fields), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def row(identifier, case, pathology, birads, *, bbox="[1,2,3,4]", width="20", height="30", **extra):
    value = {
        "ID": identifier,
        "Case": str(case),
        "Histology": "fixture histology",
        "Pathology": pathology,
        "BIRADS": str(birads),
        "Device": "fixture device",
        "Width": width,
        "Height": height,
        "Side": "left",
        "BBOX": bbox,
    }
    value.update(extra)
    return value


class SamplePlanTests(unittest.TestCase):
    def test_selection_is_metadata_bound_stratified_and_patient_unique(self):
        build = api()
        payload = metadata([
            row("bus_0003-l", 3, "malignant", 5),
            row("bus_0001-r", 1, "benign", 4),
            row("bus_0001-l", 1, "benign", 4),
            row("bus_0002-l", 2, "benign", 4),
            row("bus_0003-r", 3, "malignant", 4),
            row("bus_0004-s", 4, "malignant", 4),
        ])

        plan = build(payload)

        self.assertEqual(plan["schema"], "mmbu.busbra.quarantine_sample_plan.v1")
        self.assertEqual(plan["metadata_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual([x["record_id"] for x in plan["records"]],
                         ["bus_0001-l", "bus_0004-s", "bus_0003-l"])
        self.assertEqual([x["case_id"] for x in plan["records"]], ["1", "4", "3"])
        self.assertEqual(plan["selected_case_count"], 3)
        self.assertEqual(plan["records"][0]["image_member"], "BUSBRA/Images/bus_0001-l.png")
        self.assertEqual(plan["records"][0]["mask_member"], "BUSBRA/Masks/mask_0001-l.png")
        self.assertFalse(plan["biomedical_pixels_opened"])
        self.assertFalse(plan["model_use_authorized"])
        digest_input = dict(plan)
        digest_input.pop("plan_digest")
        encoded = json.dumps(digest_input, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                             allow_nan=False).encode("ascii")
        self.assertEqual(plan["plan_digest"], hashlib.sha256(encoded).hexdigest())

    def test_duplicate_ids_and_cases_that_disagree_fail_closed(self):
        build = api()
        bad = [
            [row("bus_0001-l", 1, "benign", 4), row("bus_0001-l", 1, "benign", 4)],
            [row("bus_0001-l", 1, "benign", 4), row("bus_0001-r", 1, "malignant", 4)],
        ]
        for rows in bad:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                build(metadata(rows))

    def test_unknown_or_validation_fields_cannot_influence_selection(self):
        build = api()
        payload = metadata([row("bus_0001-l", 1, "benign", 4, valid_1="True")], extra_fields=["valid_1"])
        with self.assertRaisesRegex(ValueError, "columns"):
            build(payload)

    def test_malformed_identity_geometry_and_limits_reject(self):
        build = api()
        bad_rows = [
            row("../bus_0001-l", 1, "benign", 4),
            row("bus_0001-l", 2, "benign", 4),
            row("bus_0001-l", 1, "benign", 4, bbox="[19,2,3,4]"),
            row("bus_0001-l", 1, "benign", 4, width="0"),
        ]
        for item in bad_rows:
            with self.subTest(item=item), self.assertRaises(ValueError):
                build(metadata([item]))
        for limit in (0, -1, True, 101):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                build(metadata([row("bus_0001-l", 1, "benign", 4)]), per_stratum=limit)


if __name__ == "__main__":
    unittest.main()
