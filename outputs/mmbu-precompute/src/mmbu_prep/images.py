"""Optional, read-only Pillow inspection; no permission or annotation decision.

Pillow is deliberately imported only inside inspect_images. Exact duplicate
identity uses a versioned decoded representation, without image transforms.
"""
from __future__ import annotations

from array import array
import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import sys
import warnings


ALLOWED_FORMATS = ("PNG", "JPEG", "TIFF", "BMP", "GIF", "WEBP", "PPM")
SPLITS = frozenset({"engineering", "train", "dev", "confirmation", "official_dev"})
DIGEST_VERSION = "pillow-decoded-representation-v1"
BITS_BY_MODE = {"1": 1, "L": 8, "LA": 8, "La": 8, "P": 8, "PA": 8,
                "RGB": 8, "RGBA": 8, "RGBa": 8, "RGBX": 8, "CMYK": 8,
                "YCbCr": 8, "LAB": 8, "HSV": 8, "I": 32, "F": 32,
                "I;16": 16, "I;16L": 16, "I;16B": 16, "I;16N": 16}


class _InspectionError(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _issue(items, code, message, **location):
    items.append({"code": code, "message": message, **location})


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _safe_path(value):
    if not _text(value) or "\\" in value or "\x00" in value or re.match(r"^[A-Za-z]:", value):
        return False
    path = PurePosixPath(value)
    return bool(path.parts) and not path.is_absolute() and ".." not in path.parts


def _pnm_header(payload):
    """Bounded parser for the only admitted PNM variants: byte P5/P6 maxval 255."""
    index, tokens = 0, []
    ceiling = min(len(payload), 65_536)
    whitespace = b" \t\r\n\v\f"
    for _ in range(4):
        while index < ceiling:
            if payload[index] in whitespace:
                index += 1
            elif payload[index] == 35:
                end = payload.find(b"\n", index, ceiling)
                if end < 0:
                    raise _InspectionError("invalid_pnm_header", "PNM comment exceeds the bounded header")
                index = end + 1
            else:
                break
        start = index
        while index < ceiling and payload[index] not in whitespace and payload[index] != 35:
            index += 1
        if start == index or index == ceiling:
            raise _InspectionError("invalid_pnm_header", "PNM header is incomplete or exceeds 64 KiB")
        token = payload[start:index]
        if not tokens and token not in (b"P5", b"P6"):
            raise _InspectionError("unsupported_pnm_encoding", "Only binary P5/P6 with maxval 255 are supported; other PNM variants require reviewed conversion")
        tokens.append(token)
    if any(not token.isdigit() or len(token) > 64 for token in tokens[1:]):
        raise _InspectionError("invalid_pnm_header", "PNM dimensions and maxval must be bounded ASCII integers")
    width, height, maximum = (int(token) for token in tokens[1:])
    if width <= 0 or height <= 0 or not 1 <= maximum <= 65_535:
        raise _InspectionError("invalid_pnm_header", "PNM dimensions or maxval are invalid")
    return tokens[0], width, height, maximum


def _file_bits(picture, payload):
    if picture.format == "PNG" and payload.startswith(b"\x89PNG\r\n\x1a\n") and len(payload) >= 29:
        channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(payload[25])
        return [payload[24]] * channels if channels else None
    if picture.format == "TIFF":
        values = picture.tag_v2.get(258)
        values = [values] if isinstance(values, int) else list(values) if isinstance(values, tuple) else None
        return values if values and all(type(value) is int and value > 0 for value in values) else None
    if picture.format == "JPEG" and isinstance(getattr(picture, "bits", None), int):
        return [picture.bits] * len(picture.getbands())
    if picture.format in ("GIF", "WEBP"):
        return [8] * len(picture.getbands())
    if picture.format == "PPM":
        # _decode checks the exact magic and maxval before invoking Pillow.
        return [8] * len(picture.getbands())
    return None


def _metadata_value(value):
    """Typed serialization for transparency, without changing its values."""
    if isinstance(value, (bytes, bytearray)):
        return {"type": "bytes", "hex": bytes(value).hex()}
    if isinstance(value, tuple):
        return {"type": "tuple", "value": list(value)}
    return {"type": type(value).__name__, "value": value}


def _pixel_digest(picture):
    pixels = picture.tobytes()
    storage_order = "mode-defined"
    # Canonicalize the serialization of native-endian 32-bit samples, never
    # their numeric values. UInt packing preserves even floating NaN bit patterns.
    if picture.mode in ("I", "F", "I;16N"):
        expected_size = 2 if picture.mode == "I;16N" else 4
        samples = array("H" if expected_size == 2 else "I")
        if samples.itemsize != expected_size:
            raise _InspectionError("unsupported_storage", "Native sample storage size is unsupported")
        samples.frombytes(pixels)
        if sys.byteorder == "little":
            samples.byteswap()
        pixels = samples.tobytes()
        storage_order = "big-endian"
    palette, palette_info = b"", None
    if picture.palette is not None:
        palette_mode, palette_data = picture.palette.getdata()
        palette = bytes(palette_data)
        palette_info = {"mode": picture.palette.mode, "rawmode": palette_mode}
    header = {
        "version": DIGEST_VERSION, "width": picture.width, "height": picture.height,
        "mode": picture.mode, "bands": list(picture.getbands()), "storage_order": storage_order,
        "palette": palette_info, "transparency": _metadata_value(picture.info.get("transparency")),
    }
    digest = hashlib.sha256()
    for part in (json.dumps(header, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"), palette, pixels):
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


def _decode(payload, item, Image, max_pixels, warning_items, location):
    """Header inspection, format integrity verification, then complete decoding."""
    pnm = _pnm_header(payload) if payload.startswith(b"P") else None
    if pnm is not None:
        magic, width, height, maximum = pnm
        item.update(width=width, height=height, format="PPM", pnm_maxval=maximum,
                    file_bits_per_sample=[8 if maximum < 256 else 16] * (1 if magic == b"P5" else 3))
        if maximum != 255:
            raise _InspectionError("pnm_requires_conversion", "PNM maxval must be exactly 255; other values can cause decoder scaling or precision reduction")
    with Image.open(BytesIO(payload), formats=ALLOWED_FORMATS) as picture:
        item.update(width=picture.width, height=picture.height, format=picture.format, mode=picture.mode)
        if picture.format == "PPM" and (pnm is None or (picture.width, picture.height) != pnm[1:3]):
            raise _InspectionError("invalid_pnm_header", "PNM header interpretation disagrees with the decoder")
        if picture.width <= 0 or picture.height <= 0 or picture.width * picture.height > max_pixels:
            raise _InspectionError("pixel_limit_exceeded", "Declared pixel count exceeds the configured ceiling")
        item["frames"] = getattr(picture, "n_frames", 1)
        item["file_bits_per_sample"] = _file_bits(picture, payload)
        item["decoded_bits_per_sample"] = BITS_BY_MODE.get(picture.mode)
        if item["frames"] != 1:
            raise _InspectionError("multiple_frames", "Multi-frame images are rejected; selecting the first frame is not permitted")
        # PNG getexif() can load pixels while locating EXIF. Verify before any
        # metadata access that can consume the stream, then reopen for decoding.
        picture.verify()
    with Image.open(BytesIO(payload), formats=ALLOWED_FORMATS) as picture:
        orientation = picture.getexif().get(274)
        if orientation is not None and (type(orientation) is not int or orientation not in range(1, 9)):
            raise _InspectionError("invalid_orientation", "EXIF orientation must be absent or an integer from 1 through 8")
        item["exif_orientation"] = orientation
        item["orientation_requires_transform"] = orientation not in (None, 1)
        profile = picture.info.get("icc_profile")
        item["icc_profile_sha256"] = hashlib.sha256(profile).hexdigest() if isinstance(profile, bytes) else None
        if item["orientation_requires_transform"]:
            if picture.format == "TIFF":
                raise _InspectionError("decoder_orientation_transform", "Pillow automatically applies TIFF orientation; this file requires a reviewed conversion")
            _issue(warning_items, "orientation_not_applied", "Nonidentity EXIF orientation was recorded and not applied", **location)
        if item["decoded_bits_per_sample"] is None:
            raise _InspectionError("unsupported_mode", "Decoded mode has no supported sample-depth contract")
        file_bits = item["file_bits_per_sample"]
        if file_bits is None:
            _issue(warning_items, "file_bit_depth_unavailable", "Encoded sample depth is not established for this format; decoded storage depth is reported", **location)
        elif max(file_bits) > item["decoded_bits_per_sample"]:
            raise _InspectionError("decoder_precision_reduction", "Pillow's decoded mode has fewer bits per sample than the file; no exact pixel identity is claimed")
        if item["decoded_bits_per_sample"] > 8 or file_bits and max(file_bits) > 8:
            _issue(warning_items, "high_bit_depth", "High-bit-depth samples are retained; no 8-bit conversion was applied", **location)
        if profile is not None:
            _issue(warning_items, "icc_profile_not_applied", "ICC profile is recorded separately and excluded from decoded-sample identity; no color management was applied", **location)
        picture.load()
        if (picture.width, picture.height, picture.mode) != (item["width"], item["height"], item["mode"]):
            raise _InspectionError("decoder_representation_changed", "Decoder changed the declared dimensions or mode while loading")
        item["pixel_sha256"] = _pixel_digest(picture)


def inspect_images(records, *, image_root, max_pixels=40_000_000, max_file_bytes=67_108_864) -> dict:
    """Inspect actual local files and find exact decoded representation duplicates.

    This is not an eligibility gate; use the manifest validator separately.
    Missing Pillow is a structured failure, never an implicit installation.
    """
    result = {"ok": False, "errors": [], "warnings": [], "counts": {"records": 0, "files_read": 0, "decoded": 0, "duplicate_groups": 0},
              "images": [], "duplicate_groups": [], "pixel_digest_version": DIGEST_VERSION, "pillow_version": None}
    errors, warning_items = result["errors"], result["warnings"]
    for name, value in (("max_pixels", max_pixels), ("max_file_bytes", max_file_bytes)):
        if type(value) is not int or value <= 0:
            _issue(errors, "invalid_limit", "Inspection ceilings must be positive integers excluding Boolean", field=name)
    if not isinstance(records, list) or not records:
        _issue(errors, "invalid_records", "Inspection requires a nonempty list of record objects")
    else:
        result["counts"]["records"] = len(records)
    try:
        root = Path(image_root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("image_root is not a directory")
    except (OSError, ValueError, TypeError, RuntimeError) as exc:
        _issue(errors, "invalid_image_root", str(exc))
    if errors:
        return result
    try:
        from PIL import Image, ImageFile
    except ImportError:
        _issue(errors, "dependency_unavailable", "Optional Pillow is unavailable; run in an environment with Pillow installed")
        return result
    result["pillow_version"] = Image.__version__
    if ImageFile.LOAD_TRUNCATED_IMAGES:
        _issue(errors, "unsafe_decoder_configuration", "Pillow LOAD_TRUNCATED_IMAGES is enabled; strict inspection requires it disabled")
        return result
    _issue(warning_items, "inspection_limits", "Exact decoded representation checks do not establish perceptual uniqueness, correct labels, biomedical validity, source permission, or image-coordinate intent")
    seen_ids = set()
    for index, row in enumerate(records):
        location = {"record_index": index}
        item = {"record_index": index, "record_id": None, "source_id": None, "split": None,
                "image_path": None, "ok": False, "raw_sha256": None, "pixel_sha256": None,
                "width": None, "height": None, "format": None, "mode": None, "frames": None,
                "decoded_bits_per_sample": None, "file_bits_per_sample": None,
                "pnm_maxval": None,
                "exif_orientation": None, "orientation_requires_transform": False,
                "icc_profile_sha256": None}
        result["images"].append(item)
        before = len(errors)
        if not isinstance(row, dict):
            _issue(errors, "invalid_record", "Each inspection record must be an object", **location)
            continue
        for name in ("record_id", "source_id", "split", "image_path"):
            if not _text(row.get(name)):
                _issue(errors, "invalid_record", "Inspection field must be a nonblank string", field=name, **location)
            else:
                item[name] = row[name]
        if item["record_id"] is not None:
            location["record_id"] = item["record_id"]
            if item["record_id"] in seen_ids:
                _issue(errors, "duplicate_record_id", "Inspection record_id is repeated", **location)
            seen_ids.add(item["record_id"])
        if item["split"] not in SPLITS:
            _issue(errors, "invalid_record", "Inspection split is unsupported", field="split", **location)
        manifest_hash = row.get("image_sha256")
        if not isinstance(manifest_hash, str) or re.fullmatch(r"[0-9a-f]{64}", manifest_hash) is None:
            _issue(errors, "invalid_record", "image_sha256 must contain 64 lowercase hexadecimal characters", field="image_sha256", **location)
        if not _safe_path(row.get("image_path")):
            _issue(errors, "unsafe_image_path", "Image path must be relative POSIX syntax without traversal", **location)
        if len(errors) != before:
            continue
        declared_width, declared_height = row.get("image_width"), row.get("image_height")
        has_dimensions = "image_width" in row or "image_height" in row
        valid_dimensions = all(type(value) is int and value > 0 for value in (declared_width, declared_height))
        if has_dimensions and not valid_dimensions:
            _issue(errors, "invalid_manifest_dimensions", "Declared image dimensions must both be positive integers excluding Boolean", **location)
        elif not has_dimensions:
            _issue(warning_items, "dimensions_unrecorded", "Manifest has no image dimensions to compare; decoded dimensions are reported separately", **location)
        try:
            path = (root / row["image_path"]).resolve()
            if not path.is_relative_to(root):
                raise _InspectionError("unsafe_image_path", "Resolved image path escapes image_root")
            if not path.is_file():
                raise _InspectionError("image_file_error", "Image file is missing or is not a regular file")
            if path.stat().st_size > max_file_bytes:
                raise _InspectionError("file_limit_exceeded", "Encoded file exceeds the configured byte ceiling")
            with path.open("rb") as stream:
                payload = stream.read(max_file_bytes + 1)
            if len(payload) > max_file_bytes:
                raise _InspectionError("file_limit_exceeded", "Encoded file exceeds the configured byte ceiling")
            result["counts"]["files_read"] += 1
            item["raw_sha256"] = hashlib.sha256(payload).hexdigest()
            if item["raw_sha256"] != manifest_hash:
                _issue(errors, "image_hash_mismatch", "Actual file hash differs from manifest; neither was changed", **location)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                try:
                    _decode(payload, item, Image, max_pixels, warning_items, location)
                finally:
                    for warning in caught:
                        _issue(warning_items, "decoder_warning", str(warning.message)[:500], **location)
            result["counts"]["decoded"] += 1
            if valid_dimensions and (declared_width, declared_height) != (item["width"], item["height"]):
                _issue(errors, "image_dimensions_mismatch", "Decoded dimensions differ from the manifest; neither was changed", **location)
        except _InspectionError as exc:
            _issue(errors, exc.code, str(exc), **location)
        except (Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
            _issue(errors, "decompression_bomb", str(exc), **location)
        except OSError as exc:
            _issue(errors, "decode_error" if item["raw_sha256"] is not None else "image_file_error", str(exc), **location)
        except Exception as exc:
            # Plugin decoders have heterogeneous exception types. Preserve their
            # type and a bounded message at this external-file error boundary.
            _issue(errors, "decode_error", f"{type(exc).__name__}: {str(exc)[:500]}", **location)
        item["ok"] = len(errors) == before

    groups = {}
    for item in result["images"]:
        if item["pixel_sha256"] is not None:
            groups.setdefault(item["pixel_sha256"], []).append(item)
    for digest, items in sorted(groups.items()):
        if len(items) < 2:
            continue
        splits = sorted({item["split"] for item in items})
        group = {"pixel_sha256": digest, "record_ids": sorted(item["record_id"] for item in items),
                 "source_ids": sorted({item["source_id"] for item in items}), "splits": splits,
                 "raw_sha256s": sorted({item["raw_sha256"] for item in items}),
                 "raw_encoding_differs": len({item["raw_sha256"] for item in items}) > 1,
                 "cross_split": len(splits) > 1}
        result["duplicate_groups"].append(group)
        if group["cross_split"]:
            _issue(errors, "decoded_split_leakage", "Exact decoded representations cross existing splits", record_ids=group["record_ids"], splits=splits)
        else:
            _issue(warning_items, "decoded_duplicates", "Multiple records share an exact decoded representation", record_ids=group["record_ids"])
        if len({item["exif_orientation"] for item in items}) > 1:
            _issue(warning_items, "duplicate_orientation_difference", "Matching stored samples carry different orientation metadata; rendered appearance is not claimed equivalent", record_ids=group["record_ids"])
    result["counts"]["duplicate_groups"] = len(result["duplicate_groups"])
    result["ok"] = not errors
    return result
