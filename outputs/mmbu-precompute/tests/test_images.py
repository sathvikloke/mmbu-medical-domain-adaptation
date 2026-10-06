"""Optional Pillow integration tests use only tiny, local synthetic images."""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

try:
    images = importlib.import_module("mmbu_prep.images")
except ModuleNotFoundError:
    images = None

try:
    from PIL import Image, PngImagePlugin
except ImportError:
    Image = None


def record(path, record_id="a", **changes):
    value = {"record_id": record_id, "source_id": "synthetic-inspection-fixture", "split": "engineering",
             "image_path": path.name, "image_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    value.update(changes)
    return value


class OptionalDependencyTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(images, "Image inspection is not implemented")

    def test_core_import_and_missing_dependency_result_without_site_packages(self):
        code = """import json
from mmbu_prep.images import inspect_images
print(json.dumps(inspect_images([{'record_id':'a','source_id':'fixture','split':'engineering','image_path':'a.png','image_sha256':'0'*64}], image_root='.')))
"""
        run = subprocess.run([sys.executable, "-S", "-c", code], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertFalse(result["ok"])
        self.assertIn("dependency_unavailable", {issue["code"] for issue in result["errors"]})

    def test_empty_inputs_and_invalid_limits_return_structured_errors(self):
        for rows in ([], None, {}):
            with self.subTest(rows=rows):
                result = images.inspect_images(rows, image_root=".")
                self.assertFalse(result["ok"])
                self.assertTrue(result["errors"])
        for option in ("max_pixels", "max_file_bytes"):
            for value in (0, -1, True, 1.5, "100"):
                with self.subTest(option=option, value=value):
                    result = images.inspect_images([], image_root=".", **{option: value})
                    self.assertIn("invalid_limit", {issue["code"] for issue in result["errors"]})


@unittest.skipUnless(Image is not None, "Optional Pillow is unavailable")
class ImageInspectionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(images, "Image inspection is not implemented")
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.path = self.root / "rgb.png"
        picture = Image.new("RGB", (3, 2), (1, 2, 3))
        picture.putpixel((2, 1), (250, 10, 5))
        picture.save(self.path)

    def inspect(self, rows=None, **options):
        return images.inspect_images(rows if rows is not None else [record(self.path)], image_root=self.root, **options)

    def codes(self, result, category="errors"):
        return {issue["code"] for issue in result[category]}

    def test_decodes_pixels_reports_properties_and_raw_identity(self):
        result = self.inspect([record(self.path, image_width=3, image_height=2)])
        self.assertTrue(result["ok"], result)
        item = result["images"][0]
        self.assertEqual((item["width"], item["height"], item["format"], item["mode"], item["frames"]), (3, 2, "PNG", "RGB", 1))
        self.assertEqual(item["decoded_bits_per_sample"], 8)
        self.assertEqual(item["file_bits_per_sample"], [8, 8, 8])
        self.assertEqual(item["raw_sha256"], record(self.path)["image_sha256"])
        self.assertRegex(item["pixel_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(result["counts"]["decoded"], 1)
        self.assertIn("inspection_limits", self.codes(result, "warnings"))

    def test_exact_pixels_match_across_different_lossless_encodings(self):
        other = self.root / "rgb.bmp"
        with Image.open(self.path) as picture:
            picture.save(other)
        result = self.inspect([record(self.path), record(other, "b")])
        self.assertTrue(result["ok"], result)
        self.assertEqual(len(result["duplicate_groups"]), 1)
        group = result["duplicate_groups"][0]
        self.assertEqual(group["record_ids"], ["a", "b"])
        self.assertTrue(group["raw_encoding_differs"])
        self.assertFalse(group["cross_split"])

    def test_duplicate_pixels_crossing_sources_and_splits_fail(self):
        other = self.root / "copy.png"
        with Image.open(self.path) as picture:
            text = PngImagePlugin.PngInfo()
            text.add_text("test", "different container bytes")
            picture.save(other, pnginfo=text, compress_level=0)
        result = self.inspect([record(self.path, split="train"), record(other, "b", source_id="another", split="dev")])
        self.assertFalse(result["ok"])
        self.assertIn("decoded_split_leakage", self.codes(result))
        self.assertTrue(result["duplicate_groups"][0]["cross_split"])
        self.assertEqual(result["duplicate_groups"][0]["source_ids"], ["another", "synthetic-inspection-fixture"])

    def test_same_dimensions_with_different_pixels_are_not_duplicates(self):
        other = self.root / "different.png"
        Image.new("RGB", (3, 2), (1, 2, 4)).save(other)
        result = self.inspect([record(self.path), record(other, "b")])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["duplicate_groups"], [])

    def test_modes_are_not_silently_converted_for_matching(self):
        gray, rgb = self.root / "gray.png", self.root / "grayrgb.png"
        Image.new("L", (3, 2), 17).save(gray)
        Image.new("RGB", (3, 2), (17, 17, 17)).save(rgb)
        result = self.inspect([record(gray), record(rgb, "b")])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["duplicate_groups"], [])

    def test_palette_and_transparency_participate_in_pixel_identity(self):
        paths = []
        for name, color, transparency in (("red", (255, 0, 0), None), ("green", (0, 255, 0), None), ("transparent", (255, 0, 0), 0)):
            path = self.root / (name + ".png")
            picture = Image.new("P", (2, 2), 0)
            picture.putpalette(list(color) + [0] * 765)
            picture.save(path, **({"transparency": transparency} if transparency is not None else {}))
            paths.append(path)
        result = self.inspect([record(path, str(index)) for index, path in enumerate(paths)])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["duplicate_groups"], [])

    def test_manifest_hash_and_dimensions_are_compared_without_repair(self):
        row = record(self.path, image_sha256="0" * 64, image_width=2, image_height=3)
        original = copy.deepcopy(row)
        result = self.inspect([row])
        self.assertFalse(result["ok"])
        self.assertIn("image_hash_mismatch", self.codes(result))
        self.assertIn("image_dimensions_mismatch", self.codes(result))
        self.assertEqual(row, original)
        self.assertEqual(result["images"][0]["width"], 3)
        self.assertIsNotNone(result["images"][0]["pixel_sha256"])

    def test_missing_dimensions_are_visible_but_not_fabricated(self):
        row = record(self.path)
        result = self.inspect([row])
        self.assertTrue(result["ok"], result)
        self.assertIn("dimensions_unrecorded", self.codes(result, "warnings"))
        self.assertNotIn("image_width", row)
        for changes in ({"image_width": 3}, {"image_width": True, "image_height": 2}, {"image_width": "3", "image_height": 2}):
            with self.subTest(changes=changes):
                result = self.inspect([record(self.path, **changes)])
                self.assertFalse(result["ok"])
                self.assertIn("invalid_manifest_dimensions", self.codes(result))

    def test_nonidentity_png_exif_orientation_is_reported_not_applied(self):
        other = self.root / "oriented.png"
        exif = Image.Exif()
        exif[274] = 6
        with Image.open(self.path) as picture:
            picture.save(other, exif=exif)
        result = self.inspect([record(self.path), record(other, "b")])
        self.assertTrue(result["ok"], result)
        item = result["images"][1]
        self.assertEqual(item["exif_orientation"], 6)
        self.assertEqual((item["width"], item["height"]), (3, 2))
        self.assertTrue(item["orientation_requires_transform"])
        self.assertIn("orientation_not_applied", self.codes(result, "warnings"))
        self.assertEqual(len(result["duplicate_groups"]), 1)

    def test_nonidentity_tiff_is_rejected_before_automatic_decoder_rotation(self):
        other = self.root / "oriented.tiff"
        with Image.open(self.path) as picture:
            picture.save(other, tiffinfo={274: 6})
        result = self.inspect([record(other)])
        self.assertFalse(result["ok"])
        self.assertIn("decoder_orientation_transform", self.codes(result))
        self.assertIsNone(result["images"][0]["pixel_sha256"])

    def test_16_bit_tiff_preserves_samples_and_flags_precision(self):
        first, second = self.root / "sixteen.tif", self.root / "sixteen-other.tif"
        for path, values in ((first, [1, 256, 65535, 0]), (second, [1, 257, 65535, 0])):
            picture = Image.frombytes("I;16", (2, 2), struct.pack("<4H", *values))
            picture.save(path)
        result = self.inspect([record(first), record(second, "b")])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["images"][0]["mode"], "I;16")
        self.assertEqual(result["images"][0]["decoded_bits_per_sample"], 16)
        self.assertEqual(result["images"][0]["file_bits_per_sample"], [16])
        self.assertIn("high_bit_depth", self.codes(result, "warnings"))
        self.assertEqual(result["duplicate_groups"], [])

    def test_16_bit_rgb_png_is_rejected_when_decoder_reduces_precision(self):
        path = self.root / "rgb16.png"
        def chunk(kind, payload):
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)
        payload = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 16, 2, 0, 0, 0))
        payload += chunk(b"IDAT", zlib.compress(b"\0" + struct.pack(">3H", 256, 257, 65535))) + chunk(b"IEND", b"")
        path.write_bytes(payload)
        result = self.inspect([record(path)])
        self.assertFalse(result["ok"])
        self.assertIn("decoder_precision_reduction", self.codes(result))
        self.assertIsNone(result["images"][0]["pixel_sha256"])

    def test_high_depth_ppm_does_not_collapse_distinct_native_samples(self):
        paths = [self.root / "ppm-256.ppm", self.root / "ppm-257.ppm"]
        for path, red in zip(paths, (256, 257)):
            path.write_bytes(b"P6\n1 1\n65535\n" + struct.pack(">3H", red, 0, 65535))
        result = self.inspect([record(paths[0], split="train"), record(paths[1], "b", split="dev")])
        self.assertFalse(result["ok"])
        self.assertIn("pnm_requires_conversion", self.codes(result))
        self.assertTrue(all(item["pixel_sha256"] is None for item in result["images"]))
        self.assertEqual(result["duplicate_groups"], [])

    def test_pgm_nonstandard_maxval_is_not_silently_rescaled(self):
        for maximum, values in ((1023, (1, 1023)), (100, (1, 100))):
            with self.subTest(maximum=maximum):
                path = self.root / "scaled.pgm"
                samples = struct.pack(">2H", *values) if maximum > 255 else bytes(values)
                path.write_bytes(f"P5\n2 1\n{maximum}\n".encode() + samples)
                result = self.inspect([record(path)])
                self.assertFalse(result["ok"])
                self.assertIn("pnm_requires_conversion", self.codes(result))
                self.assertIsNone(result["images"][0]["pixel_sha256"])

    def test_binary_8bit_pnm_with_comments_retains_exact_samples(self):
        path, copy_path = self.root / "commented.pgm", self.root / "plain.png"
        path.write_bytes(b"P5\n# image comment\n2 1\n# maxval comment\n255\n" + bytes((1, 255)))
        Image.frombytes("L", (2, 1), bytes((1, 255))).save(copy_path)
        result = self.inspect([record(path), record(copy_path, "b")])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["images"][0]["file_bits_per_sample"], [8])
        self.assertEqual(len(result["duplicate_groups"]), 1)

    def test_ascii_and_bitmap_pnm_are_explicitly_out_of_scope(self):
        for payload in (b"P2\n1 1\n255\n7\n", b"P1\n1 1\n0\n"):
            with self.subTest(payload=payload):
                path = self.root / "unsupported.pnm"
                path.write_bytes(payload)
                result = self.inspect([record(path)])
                self.assertFalse(result["ok"])
                self.assertIn("unsupported_pnm_encoding", self.codes(result))
                self.assertIsNone(result["images"][0]["pixel_sha256"])

    def test_multiframe_input_is_rejected_instead_of_using_first_frame(self):
        path = self.root / "animated.gif"
        first, second = Image.new("RGB", (2, 2), "red"), Image.new("RGB", (2, 2), "blue")
        first.save(path, save_all=True, append_images=[second], duration=100, loop=0)
        result = self.inspect([record(path)])
        self.assertFalse(result["ok"])
        self.assertIn("multiple_frames", self.codes(result))
        self.assertEqual(result["images"][0]["frames"], 2)
        self.assertIsNone(result["images"][0]["pixel_sha256"])

    def test_corrupted_truncated_missing_and_nonimage_files_fail_individually(self):
        corrupt, truncated = self.root / "corrupt.png", self.root / "truncated.png"
        corrupt.write_bytes(b"not an image")
        truncated.write_bytes(self.path.read_bytes()[:50])
        rows = [record(corrupt), record(truncated, "b"), record(self.path, "c", image_path="absent.png")]
        result = self.inspect(rows)
        self.assertFalse(result["ok"])
        self.assertIn("decode_error", self.codes(result))
        self.assertIn("image_file_error", self.codes(result))
        self.assertEqual(len(result["images"]), 3)
        self.assertEqual(result["counts"]["decoded"], 0)

    def test_source_root_confines_resolved_paths(self):
        child = self.root / "source"
        child.mkdir()
        (child / "escape.png").symlink_to(self.path)
        for path in ("../rgb.png", str(self.path), "C:\\rgb.png", "escape.png"):
            with self.subTest(path=path):
                result = images.inspect_images([record(self.path, image_path=path)], image_root=child)
                self.assertFalse(result["ok"])
                self.assertIn("unsafe_image_path", self.codes(result))
                self.assertEqual(result["counts"]["decoded"], 0)

    def test_pixel_and_compressed_file_limits_are_enforced(self):
        for options, code in (({"max_pixels": 5}, "pixel_limit_exceeded"), ({"max_file_bytes": 8}, "file_limit_exceeded")):
            with self.subTest(options=options):
                result = self.inspect(**options)
                self.assertFalse(result["ok"])
                self.assertIn(code, self.codes(result))
                self.assertEqual(result["counts"]["decoded"], 0)

    def test_large_header_dimensions_are_rejected_before_pixel_allocation(self):
        path = self.root / "huge-header.png"
        contents = bytearray(self.path.read_bytes())
        contents[16:24] = struct.pack(">II", 100_000, 100_000)
        contents[29:33] = struct.pack(">I", zlib.crc32(contents[12:29]) & 0xffffffff)
        path.write_bytes(contents)
        result = self.inspect([record(path)], max_pixels=10)
        self.assertFalse(result["ok"])
        self.assertTrue({"pixel_limit_exceeded", "decompression_bomb"} & self.codes(result))
        self.assertEqual(result["counts"]["decoded"], 0)

    def test_pillow_bomb_warning_is_error_and_global_setting_is_untouched(self):
        with patch.object(Image, "MAX_IMAGE_PIXELS", 4):
            result = self.inspect()
            self.assertFalse(result["ok"])
            self.assertIn("decompression_bomb", self.codes(result))
            self.assertEqual(Image.MAX_IMAGE_PIXELS, 4)

    def test_duplicate_ids_missing_hash_and_malformed_rows_are_rejected(self):
        bad = record(self.path)
        del bad["image_sha256"]
        for rows in ([record(self.path), record(self.path)], [bad], [None]):
            with self.subTest(rows=rows):
                self.assertFalse(self.inspect(rows)["ok"])

    def test_duplicate_reporting_is_stable_under_input_order(self):
        rows = [record(self.path, "b"), record(self.path, "a")]
        first, second = self.inspect(rows), self.inspect(list(reversed(rows)))
        self.assertEqual(first["duplicate_groups"], second["duplicate_groups"])
        self.assertEqual([item["record_id"] for item in first["images"]], ["b", "a"])


if __name__ == "__main__":
    unittest.main()
