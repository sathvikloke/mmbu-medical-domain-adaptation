"""Exact rationals, closed-field primitives, normalized paths, and the record store."""

import os
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from mmbu_phase1 import canonical, fields, paths, rational
from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.store import RecordStore


class RationalWireTests(unittest.TestCase):
    def test_normative_rational_vectors(self):
        self.assertEqual(rational.to_wire(Fraction(0)), {"denominator": 1, "numerator": 0})
        self.assertEqual(canonical.dumps(rational.to_wire(Fraction(0))), b'{"denominator":1,"numerator":0}')
        self.assertEqual(canonical.dumps(rational.to_wire(Fraction(1, 3))), b'{"denominator":3,"numerator":1}')
        self.assertEqual(canonical.dumps(rational.to_wire(Fraction(17, 24))), b'{"denominator":24,"numerator":17}')
        self.assertEqual(rational.to_wire(Fraction(-7, 20)), {"denominator": 20, "numerator": -7})
        self.assertEqual(rational.from_wire({"denominator": 24, "numerator": 17}), Fraction(17, 24))

    def test_exact_rational_wire_rejects_float_unreduced_negative_denominator_and_alt_zero(self):
        invalid = (
            0,
            0.3333333333333333,
            "1/3",
            {"denominator": 6, "numerator": 2},
            {"denominator": -3, "numerator": -1},
            {"denominator": 2, "numerator": 0},
            {"denominator": True, "numerator": 1},
            {"denominator": 3, "numerator": False},
            {"denominator": 3.0, "numerator": 1},
            {"denominator": 3, "numerator": 1.0},
            {"denominator": 0, "numerator": 1},
            {"denominator": 3},
            {"denominator": 3, "numerator": 1, "extra": 0},
            {"denominator": 9007199254740993, "numerator": 1},
            None,
        )
        for value in invalid:
            with self.subTest(value=value):
                with self.assertRaises(ContractViolation):
                    rational.from_wire(value)

    def test_canonical_bytes_from_parsed_json_are_checked(self):
        self.assertEqual(rational.from_wire(canonical.loads(b'{"denominator":1,"numerator":0}')), 0)
        with self.assertRaises(ContractViolation):
            rational.from_wire(canonical.loads(b'{"denominator":1.0,"numerator":0}'))

    def test_unrepresentable_derived_rational_rejects(self):
        with self.assertRaises(ContractViolation):
            rational.to_wire(Fraction(1, 2 ** 60 + 1))
        with self.assertRaises(TypeError):
            rational.to_wire(0.5)


class FieldPrimitiveTests(unittest.TestCase):
    def test_closed_object_rejects_missing_and_unknown_keys(self):
        self.assertEqual(fields.closed({"a": 1, "b": 2}, "x", ("a", "b")), {"a": 1, "b": 2})
        for value in ({"a": 1}, {"a": 1, "b": 2, "c": 3}, [], None):
            with self.subTest(value=value):
                with self.assertRaises(ContractViolation):
                    fields.closed(value, "x", ("a", "b"))

    def test_integer_number_and_boolean_types_are_strict(self):
        self.assertEqual(fields.integer(3, "x", minimum=0), 3)
        for bad in (True, 3.0, "3", None, -1):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractViolation):
                    fields.integer(bad, "x", minimum=0)
        self.assertEqual(fields.number(0.5, "x", minimum=0, maximum=1), 0.5)
        for bad in (True, "0.5", float("nan"), float("inf"), 2, -0.1):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractViolation):
                    fields.number(bad, "x", minimum=0, maximum=1)
        with self.assertRaises(ContractViolation):
            fields.number(0, "x", minimum=0, min_exclusive=True)
        self.assertIs(fields.boolean(False, "x"), False)
        with self.assertRaises(ContractViolation):
            fields.boolean(0, "x")

    def test_digest_and_timestamp_rules(self):
        self.assertEqual(fields.digest("a" * 64, "x"), "a" * 64)
        for bad in ("A" * 64, "a" * 63, "g" * 64, None, 1):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractViolation):
                    fields.digest(bad, "x")
        early = fields.timestamp("2026-10-16T10:00:00Z", "x")
        late = fields.timestamp("2026-10-16T10:00:00.000000001Z", "x")
        self.assertEqual(late - early, 1)
        for bad in ("2026-10-16T10:00:00", "2026-10-16T10:00:00+00:00", "2026-10-16 10:00:00Z",
                    "2026-02-30T10:00:00Z", "2026-10-16T10:00:00.1234567890Z", "2026-10-16t10:00:00z"):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractViolation):
                    fields.timestamp(bad, "x")
        self.assertRegex(fields.utc_now(), r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z$")

    def test_set_like_arrays_are_unique_and_utf8_sorted(self):
        self.assertEqual(fields.string_set(["a", "b"], "x"), ["a", "b"])
        for bad in (["b", "a"], ["a", "a"], ["a", 1], "ab"):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractViolation):
                    fields.string_set(bad, "x")
        with self.assertRaises(ContractViolation):
            fields.string_set([], "x", nonempty=True)
        # UTF-8 byte order, not UTF-16 order: U+FB33 sorts before U+1F600 here.
        self.assertEqual(fields.string_set(["\ufb33", "\U0001f600"], "x"), ["\ufb33", "\U0001f600"])
        with self.assertRaises(ContractViolation):
            fields.string_set(["x"], "x", allowed={"y"})

    def test_header_and_record_digest_binding(self):
        record = canonical.seal({"schema_id": "mmbu.phase1.example", "schema_version": 1, "v": 1})
        fields.header(record, "example")
        fields.sealed(record, "x")
        for mutation in ({"schema_version": True}, {"schema_version": 1.0}, {"schema_id": "mmbu.phase1.other"}):
            with self.subTest(mutation=mutation):
                with self.assertRaises(ContractViolation):
                    fields.header({**record, **mutation}, "example")
        with self.assertRaises(ContractViolation):
            fields.sealed({**record, "v": 2}, "x")


class PathRuleTests(unittest.TestCase):
    def test_relative_paths_are_normalized(self):
        self.assertEqual(paths.relative_path("a/b.json", "p"), "a/b.json")
        for bad in ("", "/a", "a//b", "a/./b", "a/../b", "..", "a\\b", "a/\x00", "a/", "./a",
                    "e\u0301.json"):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractViolation):
                    paths.relative_path(bad, "p")

    def test_path_sets_reject_case_fold_and_normalization_collisions(self):
        paths.unique_paths(["a/B.json", "a/c.json"], "p")
        for bad in (["a/B.json", "a/b.json"], ["x.json", "x.json"], ["Stra\u00dfe", "STRASSE"]):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractViolation):
                    paths.unique_paths(bad, "p")

    def test_absolute_paths_are_normalized(self):
        self.assertEqual(paths.absolute_path("/a/b", "p"), "/a/b")
        for bad in ("a/b", "//a", "/a/", "/a//b", "/a/./b", "/a/../b", "/a\\b", "/a\x00", "/e\u0301", 3):
            with self.subTest(bad=bad):
                with self.assertRaises(ContractViolation):
                    paths.absolute_path(bad, "p")

    def test_lstat_chain_rejects_symlink_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(os.path.realpath(tmp))
            (base / "real").mkdir()
            (base / "real/file.txt").write_text("x")
            (base / "link").symlink_to(base / "real", target_is_directory=True)
            paths.lstat_chain(str(base / "real/file.txt"))
            with self.assertRaises(ContractViolation):
                paths.lstat_chain(str(base / "link/file.txt"))
            with self.assertRaises(ContractViolation):
                paths.lstat_chain(str(base / "missing"))

    def test_bundle_member_must_be_regular_unaliased_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(os.path.realpath(tmp))
            (root / "d").mkdir()
            (root / "d/a.json").write_bytes(b"{}")
            self.assertEqual(paths.member_bytes(root, "d/a.json"), b"{}")
            os.link(root / "d/a.json", root / "d/hard.json")
            with self.assertRaises(ContractViolation):
                paths.member_bytes(root, "d/hard.json")
            (root / "d/sym.json").symlink_to(root / "d/a.json")
            with self.assertRaises(ContractViolation):
                paths.member_bytes(root, "d/sym.json")
            with self.assertRaises(ContractViolation):
                paths.member_bytes(root, "d")

    def test_bundle_member_rejects_change_during_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(os.path.realpath(tmp))
            target = root / "member.bin"
            target.write_bytes(b"a" * ((1 << 20) + 1))
            original_read = os.read
            changed = False

            def mutate_after_first_chunk(descriptor, size):
                nonlocal changed
                data = original_read(descriptor, size)
                if data and not changed:
                    changed = True
                    with target.open("ab") as handle:
                        handle.write(b"changed")
                return data

            with patch("mmbu_phase1.paths.os.read", side_effect=mutate_after_first_chunk):
                with self.assertRaises(ContractViolation):
                    paths.member_bytes(root, "member.bin")


class RecordStoreTests(unittest.TestCase):
    def test_store_resolves_by_record_digest_and_schema(self):
        store = RecordStore()
        record = canonical.seal({"schema_id": "mmbu.phase1.example", "schema_version": 1, "v": 1})
        digest = store.add(record)
        self.assertEqual(store.get(digest, "example"), record)
        with self.assertRaises(ContractViolation):
            store.get(digest, "other")
        with self.assertRaises(ContractViolation):
            store.get("0" * 64, "example")

    def test_store_rejects_stale_digest_and_conflicting_duplicate(self):
        store = RecordStore()
        record = canonical.seal({"schema_id": "mmbu.phase1.example", "schema_version": 1, "v": 1})
        with self.assertRaises(ContractViolation):
            store.add({**record, "v": 2})
        store.add(record)
        store.add(dict(record))
        artifact = store.add_artifact(b"raw bytes")
        self.assertEqual(store.artifact(artifact, "x"), b"raw bytes")
        with self.assertRaises(ContractViolation):
            store.artifact("1" * 64, "x")

    def test_store_detaches_records_from_caller_mutation(self):
        store = RecordStore()
        record = canonical.seal({
            "schema_id": "mmbu.phase1.example",
            "schema_version": 1,
            "nested": {"values": [1, 2]},
        })
        digest = store.add(record)

        record["nested"]["values"].append(3)

        self.assertEqual(store.get(digest, "example")["nested"]["values"], [1, 2])

    def test_store_returns_detached_records(self):
        store = RecordStore()
        record = canonical.seal({
            "schema_id": "mmbu.phase1.example",
            "schema_version": 1,
            "nested": {"values": [1, 2]},
        })
        digest = store.add(record)

        store.get(digest, "example")["nested"]["values"].append(3)
        store.records("example")[0]["nested"]["values"].append(4)

        self.assertEqual(store.get(digest, "example")["nested"]["values"], [1, 2])


if __name__ == "__main__":
    unittest.main()
