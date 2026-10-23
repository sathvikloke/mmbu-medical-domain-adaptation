"""Prospective BUS-BRA quarantine planning; never grants model-use approval."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re


FIELDS = ("ID", "Case", "Histology", "Pathology", "BIRADS", "Device", "Width", "Height", "Side", "BBOX")
ID_PATTERN = re.compile(r"bus_([0-9]{4})-([lrs])")
PLAN_SCHEMA = "mmbu.busbra.quarantine_sample_plan.v1"
SELECTION_ALGORITHM = "rarest-pathology-birads-stratum-then-record-id-case-exclusive-v1"


def _canonical_digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                         allow_nan=False).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _positive_integer(value, name):
    if not isinstance(value, str) or not value.isdigit() or int(value) < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _bbox(value, width, height):
    try:
        box = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("BBOX must be a JSON xywh array") from exc
    if (not isinstance(box, list) or len(box) != 4 or
            any(type(item) is not int for item in box)):
        raise ValueError("BBOX must contain four integers")
    x, y, w, h = box
    if x < 0 or y < 0 or w < 1 or h < 1 or x + w > width or y + h > height:
        raise ValueError("BBOX is not positive and in bounds")
    return box


def _read_metadata(payload):
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("metadata must be nonempty bytes")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("metadata must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != list(FIELDS):
        raise ValueError("metadata columns must exactly match BUS-BRA bus_data.csv")
    records = []
    seen_ids = set()
    case_claims = {}
    for line, raw in enumerate(reader, 2):
        if None in raw or any(not isinstance(raw[name], str) or raw[name] == "" for name in FIELDS):
            raise ValueError(f"metadata row {line} is incomplete")
        match = ID_PATTERN.fullmatch(raw["ID"])
        if not match or raw["ID"] in seen_ids:
            raise ValueError("record IDs must be unique canonical BUS-BRA IDs")
        seen_ids.add(raw["ID"])
        case_number = _positive_integer(raw["Case"], "Case")
        if int(match.group(1)) != case_number:
            raise ValueError("record ID and Case disagree")
        width = _positive_integer(raw["Width"], "Width")
        height = _positive_integer(raw["Height"], "Height")
        box = _bbox(raw["BBOX"], width, height)
        claim = (raw["Histology"], raw["Pathology"], raw["Device"])
        if case_number in case_claims and case_claims[case_number] != claim:
            raise ValueError("records in one Case disagree on patient-level claims")
        case_claims[case_number] = claim
        suffix = raw["ID"][4:]
        records.append({
            "record_id": raw["ID"],
            "case_id": str(case_number),
            "pathology": raw["Pathology"],
            "birads": raw["BIRADS"],
            "width": width,
            "height": height,
            "bbox_xywh": box,
            "image_member": f"BUSBRA/Images/{raw['ID']}.png",
            "mask_member": f"BUSBRA/Masks/mask_{suffix}.png",
        })
    if not records:
        raise ValueError("metadata must contain at least one record")
    return records


def build_sample_plan(metadata_bytes: bytes, *, per_stratum: int = 1) -> dict:
    """Freeze a patient-exclusive sample using metadata only.

    Rare strata allocate their cases first so a multi-view patient cannot make a
    rarer stratum disappear after a more common stratum consumes that patient.
    """
    if type(per_stratum) is not int or not 1 <= per_stratum <= 100:
        raise ValueError("per_stratum must be an integer in [1,100]")
    records = _read_metadata(metadata_bytes)
    strata = {}
    for record in records:
        strata.setdefault((record["pathology"], record["birads"]), []).append(record)
    order = sorted(strata, key=lambda key: (len({x["case_id"] for x in strata[key]}), key))
    used_cases = set()
    selected = []
    for key in order:
        chosen = 0
        for record in sorted(strata[key], key=lambda item: item["record_id"]):
            if record["case_id"] in used_cases:
                continue
            used_cases.add(record["case_id"])
            selected.append(record)
            chosen += 1
            if chosen == per_stratum:
                break
    selected.sort(key=lambda item: (item["pathology"], item["birads"], item["record_id"]))
    plan = {
        "schema": PLAN_SCHEMA,
        "source_id": "busbra",
        "source_version": "1.0",
        "metadata_member": "BUSBRA/bus_data.csv",
        "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        "selection_algorithm": SELECTION_ALGORITHM,
        "per_stratum": per_stratum,
        "records": selected,
        "selected_case_count": len(used_cases),
        "biomedical_pixels_opened": False,
        "model_executed": False,
        "model_use_authorized": False,
    }
    plan["plan_digest"] = _canonical_digest(plan)
    return plan
