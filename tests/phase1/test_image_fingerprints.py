import copy
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.image_fingerprints import build_duplicate_candidates, dhash64, hamming64


def record(source, version, record_id, dhash, *, sha=None, width=100, height=100):
    return {
        "source_id": source,
        "source_version": version,
        "record_id": record_id,
        "decoded_sha256": sha or canonical.raw_digest(f"{source}:{record_id}".encode()),
        "dhash64": f"{dhash:016x}",
        "width": width,
        "height": height,
    }


def inventory(source, version, rows):
    rows = sorted(rows, key=lambda row: row["record_id"])
    payload = {
        "source_id": source,
        "source_version": version,
        "complete": True,
        "records": rows,
    }
    return {**payload, "inventory_digest": canonical.value_digest(payload)}


class DHashTests(unittest.TestCase):
    def test_dhash_is_fixed_9_by_8_and_uses_adjacent_comparisons(self):
        descending = [[9 - column for column in range(9)] for _ in range(8)]
        ascending = [[column for column in range(9)] for _ in range(8)]
        self.assertEqual(dhash64(descending), (1 << 64) - 1)
        self.assertEqual(dhash64(ascending), 0)
        for bad in (descending[:7], [row[:8] for row in descending], [[0] * 9 for _ in range(7)] + [[0] * 8]):
            with self.assertRaises(ContractViolation):
                dhash64(bad)

    def test_hamming_boundaries_are_exact(self):
        self.assertEqual(hamming64(0, 0), 0)
        self.assertEqual(hamming64(0, 1), 1)
        self.assertEqual(hamming64(0, 0b1111), 4)
        self.assertEqual(hamming64(0, 0b11111), 5)
        for bad in (-1, 1 << 64, True):
            with self.assertRaises(ContractViolation):
                hamming64(bad, 0)


class DuplicateCandidateTests(unittest.TestCase):
    def closure(self, external_rows):
        item = inventory("bus-bra", "1", external_rows)
        return {
            "eligible_sources": [{"source_id": "bus-bra", "source_version": "1"}],
            "inventories": [item],
        }

    def test_hamming_zero_one_four_pass_and_five_fails(self):
        local = [record("busi-whu", "3", "local", 0)]
        external = [
            record("bus-bra", "1", "h0", 0),
            record("bus-bra", "1", "h1", 1),
            record("bus-bra", "1", "h4", 0b1111),
            record("bus-bra", "1", "h5", 0b11111),
        ]
        candidates = build_duplicate_candidates(local, self.closure(external))
        matches = {row["right_record_id"]: row for row in candidates if row["left_record_id"] == "local"}
        self.assertEqual(set(matches), {"h0", "h1", "h4"})
        self.assertEqual(matches["h4"]["hamming_distance"], 4)

    def test_aspect_boundary_and_exact_sha_rule(self):
        shared = canonical.raw_digest(b"same decoded pixels")
        local = [record("busi-whu", "3", "local", 0, sha=shared, width=100, height=100)]
        external = [
            record("bus-bra", "1", "at-boundary", 1, width=105, height=100),
            record("bus-bra", "1", "beyond", 1, width=106, height=100),
            record("bus-bra", "1", "exact-sha", 1 << 20, sha=shared, width=200, height=100),
        ]
        candidates = build_duplicate_candidates(local, self.closure(external))
        by_id = {row["right_record_id"]: row for row in candidates if row["left_record_id"] == "local"}
        self.assertIn("at-boundary", by_id)
        self.assertNotIn("beyond", by_id)
        self.assertTrue(by_id["exact-sha"]["exact_decoded_match"])

    def test_inventory_closure_digest_and_deterministic_order(self):
        local = [record("busi-whu", "3", "z", 0), record("busi-whu", "3", "a", 1)]
        rows = [record("bus-bra", "1", "b", 0), record("bus-bra", "1", "a", 1)]
        closed = self.closure(rows)
        first = build_duplicate_candidates(list(reversed(local)), copy.deepcopy(closed))
        second = build_duplicate_candidates(local, copy.deepcopy(closed))
        self.assertEqual(first, second)
        self.assertEqual(first, sorted(first, key=lambda row: (
            row["left_source_id"], row["left_source_version"], row["left_record_id"],
            row["right_source_id"], row["right_source_version"], row["right_record_id"],
        )))

        missing = copy.deepcopy(closed)
        missing["eligible_sources"].append({"source_id": "pathmnist-224", "source_version": "1"})
        with self.assertRaises(ContractViolation):
            build_duplicate_candidates(local, missing)
        bad_digest = copy.deepcopy(closed)
        bad_digest["inventories"][0]["inventory_digest"] = "0" * 64
        with self.assertRaises(ContractViolation):
            build_duplicate_candidates(local, bad_digest)


if __name__ == "__main__":
    unittest.main()
