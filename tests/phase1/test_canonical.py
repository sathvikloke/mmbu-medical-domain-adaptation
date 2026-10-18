"""Frozen conformance vectors for the single Phase 1 canonical JSON kernel."""

import hashlib
import json
import struct
import unittest
from fractions import Fraction

from mmbu_phase1 import canonical
from mmbu_phase1.canonical import CanonicalJSONError


def sha(data):
    return hashlib.sha256(data).hexdigest()


# RFC 8785 Appendix B: IEEE 754 binary64 bit patterns and their canonical text.
RFC8785_NUMBER_VECTORS = (
    ("0000000000000000", "0"),
    ("8000000000000000", "0"),
    ("0000000000000001", "5e-324"),
    ("8000000000000001", "-5e-324"),
    ("7fefffffffffffff", "1.7976931348623157e+308"),
    ("ffefffffffffffff", "-1.7976931348623157e+308"),
    ("4340000000000000", "9007199254740992"),
    ("c340000000000000", "-9007199254740992"),
    ("4430000000000000", "295147905179352830000"),
    ("44b52d02c7e14af5", "9.999999999999997e+22"),
    ("44b52d02c7e14af6", "1e+23"),
    ("44b52d02c7e14af7", "1.0000000000000001e+23"),
    ("444b1ae4d6e2ef4e", "999999999999999700000"),
    ("444b1ae4d6e2ef4f", "999999999999999900000"),
    ("444b1ae4d6e2ef50", "1e+21"),
    ("3eb0c6f7a0b5ed8c", "9.999999999999997e-7"),
    ("3eb0c6f7a0b5ed8d", "0.000001"),
    ("41b3de4355555553", "333333333.3333332"),
    ("41b3de4355555554", "333333333.33333325"),
    ("41b3de4355555555", "333333333.3333333"),
    ("41b3de4355555556", "333333333.3333334"),
    ("41b3de4355555557", "333333333.33333343"),
    ("becbf647612f3696", "-0.0000033333333333333333"),
    ("43143ff3c1cb0959", "1424953923781206.2"),
)


def double(bits):
    return struct.unpack(">d", bytes.fromhex(bits))[0]


class NumberSerializationTests(unittest.TestCase):
    def test_rfc8785_appendix_b_number_vectors(self):
        for bits, expected in RFC8785_NUMBER_VECTORS:
            with self.subTest(bits=bits):
                self.assertEqual(canonical.es6_number(double(bits)), expected)
                self.assertEqual(canonical.dumps(double(bits)), expected.encode())

    def test_nan_and_infinity_bit_patterns_reject(self):
        for bits in ("7fffffffffffffff", "7ff0000000000000", "fff0000000000000"):
            with self.subTest(bits=bits):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.dumps(double(bits))
                self.assertEqual(caught.exception.code, "nonfinite")

    def test_integer_serialization_is_exact_and_bounded(self):
        self.assertEqual(canonical.dumps(0), b"0")
        self.assertEqual(canonical.dumps(-17), b"-17")
        self.assertEqual(canonical.dumps(9007199254740992), b"9007199254740992")
        self.assertEqual(canonical.dumps(10 ** 20), b"100000000000000000000")
        for value in (9007199254740993, 2 ** 60 + 1, 2 ** 64 - 1):
            with self.subTest(value=value):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.dumps(value)
                self.assertEqual(caught.exception.code, "inexact_number")
        with self.assertRaises(CanonicalJSONError) as caught:
            canonical.dumps(10 ** 400)
        self.assertEqual(caught.exception.code, "nonfinite")

    def test_floating_and_exponent_forms_canonicalize(self):
        vectors = (
            (b"1.0", b"1"),
            (b"1E2", b"100"),
            (b"1.5e+3", b"1500"),
            (b"2e-3", b"0.002"),
            (b"1E30", b"1e+30"),
            (b"0.000001", b"0.000001"),
            (b"0.0000001", b"1e-7"),
            (b"4.50", b"4.5"),
            (b"1e21", b"1e+21"),
            (b"1e20", b"100000000000000000000"),
            (b"123.456", b"123.456"),
        )
        for raw, expected in vectors:
            with self.subTest(raw=raw):
                self.assertEqual(canonical.dumps(canonical.loads(raw)), expected)

    def test_negative_zero_has_one_canonical_form(self):
        for raw in (b"-0", b"-0.0", b"-0e5", b"0e-3", b"-0E+2"):
            with self.subTest(raw=raw):
                value = canonical.loads(raw)
                self.assertEqual(canonical.dumps(value), b"0")
                self.assertEqual(canonical.exact(value), 0)
        self.assertEqual(canonical.dumps(-0.0), b"0")

    def test_integer_and_fraction_lexemes_keep_distinct_parse_types(self):
        self.assertIs(type(canonical.loads(b"1")), int)
        self.assertIs(type(canonical.loads(b"1.0")), float)
        self.assertIs(type(canonical.loads(b"1e0")), float)

    def test_exact_value_uses_the_canonical_decimal_lexeme(self):
        self.assertEqual(canonical.exact(canonical.loads(b"0.1")), Fraction(1, 10))
        self.assertEqual(canonical.exact(canonical.loads(b"0.80")), Fraction(4, 5))
        self.assertEqual(canonical.exact(7), Fraction(7))
        self.assertEqual(canonical.exact(1e23), Fraction(10) ** 23)
        with self.assertRaises(TypeError):
            canonical.exact(True)

    def test_inexact_or_unrepresentable_lexemes_reject_instead_of_rounding(self):
        for raw in (
            b"0.1000000000000000055511151231257827",
            b"333333333.33333329",
            b"9007199254740993",
            b"1e-400",
            b"295147905179352825856",
        ):
            with self.subTest(raw=raw):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.loads(raw)
                self.assertEqual(caught.exception.code, "inexact_number")

    def test_nonfinite_and_overflowing_numbers_reject(self):
        for raw in (b"NaN", b"Infinity", b"-Infinity", b"1e9999", b"-1e9999", b"[1e400]", b"1" + b"0" * 400):
            with self.subTest(raw=raw[:12]):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.loads(raw)
                self.assertEqual(caught.exception.code, "nonfinite")
                self.assertIn("nonfinite JSON number", str(caught.exception))

    def test_resource_exhausting_number_lexeme_rejects(self):
        with self.assertRaises(CanonicalJSONError) as caught:
            canonical.loads(b"0." + b"1" * 5000)
        self.assertEqual(caught.exception.code, "resource_limit")
        with self.assertRaises(CanonicalJSONError) as caught:
            canonical.loads(b"1" * 5000)
        self.assertEqual(caught.exception.code, "resource_limit")


class StringAndOrderingTests(unittest.TestCase):
    def test_rfc8785_utf16_key_ordering(self):
        value = {
            "\u20ac": "Euro Sign",
            "\r": "Carriage Return",
            "\ufb33": "Hebrew Letter Dalet With Dagesh",
            "1": "One",
            "\U0001f600": "Emoji: Grinning Face",
            "\u0080": "Control",
            "\u00f6": "Latin Small Letter O With Diaeresis",
        }
        expected = (
            '{"\\r":"Carriage Return","1":"One","\u0080":"Control",'
            '"\u00f6":"Latin Small Letter O With Diaeresis","\u20ac":"Euro Sign",'
            '"\U0001f600":"Emoji: Grinning Face","\ufb33":"Hebrew Letter Dalet With Dagesh"}'
        ).encode("utf-8")
        self.assertEqual(canonical.dumps(value), expected)
        naive = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        self.assertNotEqual(naive, expected, "code-point sort_keys is not RFC 8785 ordering")

    def test_rfc8785_string_escaping_example(self):
        raw = b'{"literals":[null,true,false],"string":"\\u20ac$\\u000F\\u000aA\'\\u0042\\u0022\\u005c\\\\\\"\\/"}'
        expected = '{"literals":[null,true,false],"string":"\u20ac$\\u000f\\nA\'B\\"\\\\\\\\\\"/"}'.encode()
        self.assertEqual(canonical.dumps(canonical.loads(raw)), expected)

    def test_rfc8785_canonicalization_example_from_parsed_doubles(self):
        value = {
            "numbers": [333333333.33333329, 1e30, 4.50, 2e-3, 0.000000000000000000000000001],
            "string": "\u20ac$\u000f\nA'B\"\\\\\"/",
            "literals": [None, True, False],
        }
        expected = (
            '{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],'
            '"string":"\u20ac$\\u000f\\nA\'B\\"\\\\\\\\\\"/"}'
        ).encode()
        self.assertEqual(canonical.dumps(value), expected)

    def test_control_characters_use_short_or_lowercase_escapes(self):
        value = "\b\t\n\f\r\u0000\u001f\u007f\u2028"
        self.assertEqual(canonical.dumps(value), '"\\b\\t\\n\\f\\r\\u0000\\u001f\u007f\u2028"'.encode())

    def test_lone_surrogates_and_noncharacters_reject(self):
        for raw in (b'"\\ud800"', b'"\\udfff"', b'{"\\ud83d":1}', b'"\\ufdd0"', b'"\\uffff"'):
            with self.subTest(raw=raw):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.loads(raw)
                self.assertEqual(caught.exception.code, "invalid_unicode")
        with self.assertRaises(CanonicalJSONError):
            canonical.dumps("\ud800")
        with self.assertRaises(CanonicalJSONError):
            canonical.dumps({"\ufffe": 1})


class ParserStrictnessTests(unittest.TestCase):
    def test_duplicate_keys_reject_including_escaped_aliases(self):
        for raw in (b'{"a":1,"a":1}', b'{"x":{"b":1,"b":2}}', b'{"a":1,"\\u0061":2}'):
            with self.subTest(raw=raw):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.loads(raw)
                self.assertEqual(caught.exception.code, "duplicate_key")
                self.assertIn("duplicate JSON key", str(caught.exception))

    def test_bom_invalid_utf8_and_malformed_documents_reject(self):
        cases = (
            (b"\xef\xbb\xbf{}", "bom"),
            (b'"\xff"', "invalid_utf8"),
            (b"", "invalid_json"),
            (b"   ", "invalid_json"),
            (b'{"a":', "invalid_json"),
            (b"{'a':1}", "invalid_json"),
            (b'{"a":1,}', "invalid_json"),
            (b"01", "invalid_json"),
            (b'{"a":1} trailing', "invalid_json"),
            (b'"tab\tinside"', "invalid_json"),
        )
        for raw, code in cases:
            with self.subTest(raw=raw):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.loads(raw)
                self.assertEqual(caught.exception.code, code)

    def test_multiple_top_level_values_are_distinguished(self):
        for raw in (b'{"a":1}{"b":2}', b'{"a":1} {"b":2}', b"[1] [2]", b"1 2"):
            with self.subTest(raw=raw):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.loads(raw)
                self.assertEqual(caught.exception.code, "multiple_values")

    def test_json_whitespace_only_is_allowed_around_one_value(self):
        self.assertEqual(canonical.loads(b' \t\r\n{"a":[1,2]} \n'), {"a": [1, 2]})
        with self.assertRaises(CanonicalJSONError):
            canonical.loads('\u00a0{}'.encode())

    def test_loads_canonical_requires_exact_canonical_bytes(self):
        self.assertEqual(canonical.loads_canonical(b'{"a":1,"b":[true,null]}'), {"a": 1, "b": [True, None]})
        for raw in (b'{"b":1,"a":2}', b'{"a": 1}', b'{"a":1.0}', b'{"a":-0}', b'{"a":1}\n', b'"\\u0041"'):
            with self.subTest(raw=raw):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.loads_canonical(raw)
                self.assertEqual(caught.exception.code, "noncanonical")

    def test_serializer_rejects_non_json_types(self):
        for value in ((1, 2), {1: "a"}, {True: 1}, b"x", {"a"}, Fraction(1, 2), object()):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(CanonicalJSONError) as caught:
                    canonical.dumps(value)
                self.assertEqual(caught.exception.code, "unsupported_type")

    def test_booleans_are_never_numbers(self):
        self.assertEqual(canonical.dumps([True, False]), b"[true,false]")
        with self.assertRaises(TypeError):
            canonical.exact(False)


class DigestDomainTests(unittest.TestCase):
    RECORD = {
        "schema_id": "mmbu.phase1.example",
        "record_digest": "f" * 64,
        "nested": {"record_digest": "keep-nested"},
        "reviewer_attestation_digest": "a" * 64,
        "reviewer_attestation_digests": ["b" * 64],
        "approval_attestation_digest": "c" * 64,
        "completeness_attestation_digest": "d" * 64,
    }

    def test_record_digest_omits_only_the_top_level_record_digest(self):
        expected = (
            '{"approval_attestation_digest":"' + "c" * 64 + '","completeness_attestation_digest":"' + "d" * 64
            + '","nested":{"record_digest":"keep-nested"},"reviewer_attestation_digest":"' + "a" * 64
            + '","reviewer_attestation_digests":["' + "b" * 64 + '"],"schema_id":"mmbu.phase1.example"}'
        ).encode()
        self.assertEqual(canonical.record_digest(self.RECORD), sha(expected))

    def test_subject_domains_omit_exactly_their_named_fields(self):
        expected_omitted = {
            "single_attestation": {"record_digest", "reviewer_attestation_digest"},
            "multi_attestation": {"record_digest", "reviewer_attestation_digests"},
            "source_approval": {"record_digest", "approval_attestation_digest"},
            "model_lineage_completeness": {"record_digest", "completeness_attestation_digest"},
        }
        self.assertEqual({k: set(v) for k, v in canonical.SUBJECT_DOMAINS.items()}, expected_omitted)
        digests = {canonical.record_digest(self.RECORD), canonical.value_digest(self.RECORD)}
        for domain, omitted in expected_omitted.items():
            with self.subTest(domain=domain):
                body = {k: v for k, v in self.RECORD.items() if k not in omitted}
                digest = canonical.subject_digest(self.RECORD, domain)
                self.assertEqual(digest, sha(canonical.dumps(body)))
                digests.add(digest)
        self.assertEqual(len(digests), 6, "every digest domain must be distinct")
        with self.assertRaises(ValueError):
            canonical.subject_digest(self.RECORD, "unknown_domain")

    def test_raw_byte_and_canonical_value_digests_are_separate_domains(self):
        raw = b'{"b":1, "a":2}'
        value = canonical.loads(raw)
        self.assertEqual(canonical.raw_digest(raw), sha(raw))
        self.assertEqual(canonical.value_digest(value), sha(b'{"a":2,"b":1}'))
        self.assertNotEqual(canonical.raw_digest(raw), canonical.value_digest(value))

    def test_seal_binds_record_digest_and_rejects_non_objects(self):
        sealed = canonical.seal({"schema_id": "x", "record_digest": None, "value": 1})
        self.assertEqual(sealed["record_digest"], sha(b'{"schema_id":"x","value":1}'))
        self.assertEqual(canonical.record_digest(sealed), sealed["record_digest"])
        with self.assertRaises(TypeError):
            canonical.record_digest(["not", "an", "object"])


if __name__ == "__main__":
    unittest.main()
