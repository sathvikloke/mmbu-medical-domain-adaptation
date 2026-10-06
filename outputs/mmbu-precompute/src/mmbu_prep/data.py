"""Offline provenance validation and deterministic assignment of whole lineages.

Recorded approvals are inputs to this mechanical gate, not legal determinations.
This module neither decodes images nor evaluates annotation correctness.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re

from .contracts import CONTEXT_FIELDS, validate_xywh


TASKS = frozenset({"global_classification", "counting", "box_classification",
                   "mask_classification", "detection"})
SPLITS = frozenset({"engineering", "train", "dev", "confirmation", "official_dev"})
EXTERNAL_SPLITS = ("train", "dev", "confirmation")
SOURCE_ROLES = frozenset({"external", "official", "synthetic"})
SOURCE_STATUSES = frozenset({"candidate", "quarantined", "approved", "engineering_only"})
CORE_FIELDS = frozenset({"schema_version", "record_id", "source_id", "source_version",
                         "source_family", "split", "image_path", "image_sha256",
                         "parent_image_sha256", "group_id", "task", "question", "answer",
                         "context", "annotation_origin", "conversion_version",
                         "review_status", "synthetic"})
TEXT_FIELDS = ("record_id", "source_id", "source_version", "source_family", "group_id",
               "annotation_origin", "conversion_version", "review_status")


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _member(value, choices):
    return isinstance(value, str) and value in choices


def _sha(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _finite_json(value):
    try:
        json.dumps(value, allow_nan=False)
        return True
    except (TypeError, ValueError, OverflowError, RecursionError):
        return False


def _issue(target, code, message, **details):
    target.append({"code": code, "message": message, **details})


def _safe_relative_path(value):
    if not _text(value) or "\\" in value or "\x00" in value or re.match(r"^[A-Za-z]:", value):
        return False
    path = PurePosixPath(value)
    return bool(path.parts) and not path.is_absolute() and ".." not in path.parts


def _validate_targets(row, errors, location):
    context = row.get("context")
    if isinstance(context, dict):
        for key, value in context.items():
            if not _member(key, CONTEXT_FIELDS) or not _text(value):
                _issue(errors, "invalid_context", "Context requires canonical fields with nonblank string values.",
                       field=key, **location)
    task, answer = row.get("task"), row.get("answer")
    if task in ("global_classification", "box_classification"):
        if not _text(answer):
            _issue(errors, "invalid_target", "Classification answer must be a nonblank string.", **location)
    elif task == "mask_classification":
        if not (_text(answer) or isinstance(answer, list) and bool(answer) and all(_text(value) for value in answer)):
            _issue(errors, "invalid_target", "Mask classification requires a nonblank label or nonempty list of labels.", **location)
    elif task == "counting":
        if not (type(answer) is int and answer >= 0 or isinstance(answer, str) and re.fullmatch(r"0|[1-9][0-9]*", answer)):
            _issue(errors, "invalid_target", "Count must be a nonnegative integer or canonical ASCII decimal string.", **location)
    elif task == "detection":
        if not isinstance(answer, list) or not answer:
            _issue(errors, "invalid_target", "Detection requires one xywh box or a nonempty list of xywh boxes.", **location)
            return
        boxes = [answer] if len(answer) == 4 and all(not isinstance(value, list) for value in answer) else answer
        for box_index, box in enumerate(boxes):
            try:
                if not isinstance(box, list):
                    raise ValueError("Each box must be a JSON array")
                validate_xywh(box, row.get("image_width"), row.get("image_height"))
            except ValueError as exc:
                _issue(errors, "invalid_target", str(exc), box_index=box_index, **location)


def _source_index(registry, errors):
    sources = {}
    if not isinstance(registry, dict):
        _issue(errors, "invalid_registry", "Registry must be an object.")
        return sources
    if type(registry.get("schema_version")) is not int or registry["schema_version"] != 1:
        _issue(errors, "invalid_registry", "Registry schema_version must be integer 1.")
    entries = registry.get("sources")
    if not isinstance(entries, list):
        _issue(errors, "invalid_registry", "Registry sources must be a list.")
        return sources
    for index, entry in enumerate(entries):
        location = {"source_index": index}
        if not isinstance(entry, dict):
            _issue(errors, "invalid_source", "Each source must be an object.", **location)
            continue
        sid = entry.get("source_id")
        if _text(sid):
            location["source_id"] = sid
            if sid in sources:
                _issue(errors, "duplicate_source_id", "Registry source_id is repeated.", **location)
            else:
                sources[sid] = entry
        for field in ("source_id", "source_version", "source_family"):
            if not _text(entry.get(field)):
                _issue(errors, "invalid_source_field", "Source identity fields must be nonempty strings.",
                       field=field, **location)
        for field, choices in (("source_role", SOURCE_ROLES), ("status", SOURCE_STATUSES)):
            if not _member(entry.get(field), choices):
                _issue(errors, "invalid_source_field", "Unknown or absent source field.", field=field, **location)
        purposes = entry.get("allowed_purposes")
        if (not isinstance(purposes, list) or any(not _member(value, SPLITS) for value in purposes)
                or len(purposes) != len(set(value for value in purposes if isinstance(value, str)))):
            _issue(errors, "invalid_source_field", "allowed_purposes must be a list of unique supported purposes.",
                   field="allowed_purposes", **location)
        if entry.get("status") == "engineering_only" or entry.get("source_role") == "synthetic":
            if (entry.get("source_role") != "synthetic" or entry.get("status") != "engineering_only"
                    or purposes != ["engineering"]):
                _issue(errors, "invalid_engineering_source",
                       "Synthetic sources must be engineering_only with only engineering permission.", **location)
        if entry.get("status") == "approved":
            evidence = entry.get("evidence")
            if (not isinstance(evidence, list) or not evidence
                    or any(not ((isinstance(value, dict) and bool(value) and _finite_json(value))
                               or _text(value)) for value in evidence)
                    or not _text(entry.get("reviewed_by")) or not _text(entry.get("reviewed_at"))):
                _issue(errors, "missing_approval_evidence",
                       "Approved sources require evidence, reviewed_by and reviewed_at.", **location)
    return sources


def _components(records):
    """Global content lineage, plus family-scoped group identifiers."""
    parents = list(range(len(records)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parents[max(left, right)] = min(left, right)

    seen = {}
    for index, row in enumerate(records):
        if not isinstance(row, dict):
            continue
        keys = [("sha256", row[field]) for field in ("image_sha256", "parent_image_sha256")
                if _sha(row.get(field))]
        if _text(row.get("source_family")) and _text(row.get("group_id")):
            keys.append(("group", row["source_family"], row["group_id"]))
        for key in keys:
            if key in seen:
                union(index, seen[key])
            else:
                seen[key] = index
    groups = {}
    for index, row in enumerate(records):
        if isinstance(row, dict):
            groups.setdefault(find(index), []).append(index)
    return list(groups.values())


def validate_manifest(records, registry, *, image_root=None, purpose="engineering") -> dict:
    """Return structured errors, warnings and counts without changing inputs.

    Operational purposes require each record's split to match the purpose.
    Engineering audits can inspect multiple splits; all permissions still apply.
    With no image_root, safe relative path syntax is checked but files are not read.
    """
    return _validate_manifest(records, registry, image_root=image_root, purpose=purpose,
                              require_purpose_split=True)


def _validate_manifest(records, registry, *, image_root=None, purpose, require_purpose_split):
    """Shared mechanical audit; only assignment bypasses preassignment split match."""
    errors, warnings = [], []
    counts = {"records": 0, "sources": 0, "components": 0, "files_checked": 0,
              "by_split": {}, "by_task": {}}
    sources = _source_index(registry, errors)
    if not _member(purpose, SPLITS):
        _issue(errors, "invalid_purpose", "Purpose must be engineering, train, dev, confirmation or official_dev.")
    if not isinstance(records, list):
        _issue(errors, "invalid_records", "Records must be a list of objects.")
        rows = []
    else:
        rows = records
        counts["records"] = len(rows)
        if not rows:
            _issue(errors, "empty_manifest", "Manifest must contain at least one record.")

    root = None
    if image_root is not None:
        try:
            root = Path(image_root).resolve(strict=True)
            if not root.is_dir():
                raise ValueError("image_root is not a directory")
        except (OSError, ValueError, TypeError, RuntimeError) as exc:
            root = None
            _issue(errors, "invalid_image_root", str(exc))
    else:
        _issue(warnings, "files_unchecked", "No image_root supplied: file existence and SHA-256 were not checked.")
    _issue(warnings, "semantic_checks_not_performed",
           "Byte hashes do not establish image decoding, coordinate-frame correctness, label validity, visual support, "
           "near-duplicate absence, correct grouping, or legal/official authorization.")

    seen_ids, used_sources, file_hashes = set(), set(), {}
    for index, row in enumerate(rows):
        location = {"record_index": index}
        if not isinstance(row, dict):
            _issue(errors, "invalid_record", "Record must be an object.", **location)
            continue
        if _text(row.get("record_id")):
            location["record_id"] = row["record_id"]
            if row["record_id"] in seen_ids:
                _issue(errors, "duplicate_record_id", "record_id is repeated.", **location)
            seen_ids.add(row["record_id"])
        for field in sorted(CORE_FIELDS - row.keys()):
            _issue(errors, "missing_field", "Required field is absent; no value was invented.", field=field, **location)
        for field in TEXT_FIELDS:
            if not _text(row.get(field)):
                _issue(errors, "invalid_record_field", "Provenance fields must be nonempty strings.", field=field, **location)
        if type(row.get("schema_version")) is not int or row["schema_version"] != 1:
            _issue(errors, "invalid_record_field", "schema_version must be integer 1.", field="schema_version", **location)
        if type(row.get("synthetic")) is not bool:
            _issue(errors, "invalid_record_field", "synthetic must be a Boolean.", field="synthetic", **location)
        if not _text(row.get("question")):
            _issue(errors, "invalid_record_field", "question must be a nonempty string.", field="question", **location)
        if row.get("answer") is None or (isinstance(row.get("answer"), str) and not _text(row["answer"])):
            _issue(errors, "invalid_record_field", "answer must be present and not null or a blank string.", field="answer", **location)
        if not isinstance(row.get("context"), dict):
            _issue(errors, "invalid_record_field", "context must be an object.", field="context", **location)
        if not _finite_json(row):
            _issue(errors, "invalid_record_field", "Record must serialize to JSON without nonfinite values or cycles.", **location)
        _validate_targets(row, errors, location)
        for field, choices in (("task", TASKS), ("split", SPLITS)):
            if not _member(row.get(field), choices):
                _issue(errors, "invalid_record_field", "Unsupported task or split.", field=field, **location)
            else:
                bucket = counts["by_task" if field == "task" else "by_split"]
                bucket[row[field]] = bucket.get(row[field], 0) + 1
        if (require_purpose_split and _member(purpose, SPLITS) and purpose != "engineering"
                and row.get("split") != purpose):
            _issue(errors, "purpose_split_mismatch", "Operational purpose must match the record's existing split.",
                   purpose=purpose, **location)
        for field in ("image_sha256", "parent_image_sha256"):
            value = row.get(field)
            if not (field == "parent_image_sha256" and value is None) and not _sha(value):
                _issue(errors, "invalid_record_field", "Hash must be 64 lowercase hexadecimal characters.", field=field, **location)

        sid = row.get("source_id")
        entry = sources.get(sid) if isinstance(sid, str) else None
        if _text(sid):
            used_sources.add(sid)
        if entry is None:
            _issue(errors, "unknown_source", "Record source_id is absent from registry.", **location)
        else:
            for field in ("source_version", "source_family"):
                if row.get(field) != entry.get(field):
                    _issue(errors, "source_mismatch", "Record and registry disagree.", field=field, **location)
            status, role = entry.get("status"), entry.get("source_role")
            allowed = entry.get("allowed_purposes")
            allowed = allowed if isinstance(allowed, list) else []
            if status not in ("approved", "engineering_only"):
                _issue(errors, "source_ineligible", "Source is not eligible for use.", **location)
            if purpose not in allowed:
                _issue(errors, "purpose_not_permitted", "Requested purpose has no recorded source permission.", **location)
            if row.get("split") not in allowed:
                _issue(errors, "split_not_permitted", "Record split has no recorded source permission.", **location)
            if type(row.get("synthetic")) is bool and row["synthetic"] != (role == "synthetic"):
                _issue(errors, "synthetic_mismatch", "Record synthetic flag and registry role disagree.", **location)
            if row.get("synthetic") is True or role == "synthetic":
                if row.get("split") != "engineering" or purpose != "engineering":
                    _issue(errors, "synthetic_not_engineering", "Synthetic fixtures are restricted to engineering.", **location)
                if row.get("review_status") not in ("engineering_reviewed", "approved"):
                    _issue(errors, "record_not_approved", "Synthetic fixture requires engineering review.", **location)
            elif row.get("split") != "engineering" or purpose != "engineering":
                if row.get("review_status") != "approved":
                    _issue(errors, "record_not_approved", "Non-engineering use requires approved item review.", **location)
            elif row.get("review_status") not in ("engineering_reviewed", "approved"):
                _issue(errors, "record_not_approved", "Engineering record requires recorded review.", **location)
            if role == "official" and (row.get("split") in EXTERNAL_SPLITS or purpose in EXTERNAL_SPLITS):
                _issue(errors, "official_split_forbidden", "Official/challenge records cannot enter external optimization or selection splits.", **location)
            if (row.get("split") == "official_dev" or purpose == "official_dev") and role != "official":
                _issue(errors, "official_dev_requires_official", "official_dev is reserved for explicitly permitted official records.", **location)

        image_path = row.get("image_path")
        if not _safe_relative_path(image_path):
            _issue(errors, "unsafe_image_path", "image_path must be a relative POSIX path without traversal.", **location)
        elif root is not None:
            try:
                path = (root / image_path).resolve()
                if not path.is_relative_to(root):
                    _issue(errors, "unsafe_image_path", "Resolved image path escapes image_root.", **location)
                    continue
                if path not in file_hashes:
                    if not path.is_file():
                        raise ValueError("Image path is missing or is not a regular file")
                    with path.open("rb") as stream:
                        file_hashes[path] = hashlib.file_digest(stream, "sha256").hexdigest()
                    counts["files_checked"] += 1
                if _sha(row.get("image_sha256")) and file_hashes[path] != row["image_sha256"]:
                    _issue(errors, "image_hash_mismatch", "File SHA-256 differs from manifest; neither was changed.", **location)
            except (OSError, ValueError, RuntimeError) as exc:
                _issue(errors, "image_file_error", str(exc), **location)

    groups = _components(rows)
    counts["components"] = len(groups)
    counts["sources"] = len(used_sources)
    for component in groups:
        splits = sorted({rows[index]["split"] for index in component if _member(rows[index].get("split"), SPLITS)})
        if len(splits) > 1:
            _issue(errors, "split_leakage", "A connected image/parent/group lineage crosses splits.",
                   record_ids=sorted(rows[index]["record_id"] for index in component if _text(rows[index].get("record_id"))),
                   record_indices=component, splits=splits)
    return {"ok": not errors, "errors": errors, "warnings": warnings, "counts": counts}


def assign_splits(records, *, registry, seed, ratios) -> list[dict]:
    """Assign approved external components, requiring registry authorization.

    Ratios are deterministic hash-bucket probabilities, not exact record quotas.
    Existing cross-split leakage is rejected, not silently repaired. Existing dev
    and confirmation records can only retain their split. Caller order is
    preserved and returned records are independent deep copies.
    """
    if type(seed) is not int:
        raise ValueError("seed must be an integer (not Boolean)")
    if not isinstance(ratios, dict) or not ratios:
        raise ValueError("ratios must be a nonempty mapping of external split names to probabilities")
    if any(not _member(name, EXTERNAL_SPLITS) for name in ratios):
        raise ValueError("Only train, dev and confirmation can be assigned")
    if any(type(value) not in (int, float) or value < 0 or value > 1 or not math.isfinite(value)
           for value in ratios.values()):
        raise ValueError("Split ratios must be finite numbers in [0, 1], excluding Boolean")
    if not math.isclose(math.fsum(ratios.values()), 1.0, rel_tol=0.0, abs_tol=1e-12):
        raise ValueError("Split ratios must sum to 1")
    targets = [(name, ratios[name]) for name in EXTERNAL_SPLITS if ratios.get(name, 0) > 0]
    result = _validate_manifest(records, registry, purpose=targets[0][0], require_purpose_split=False)
    if not result["ok"]:
        codes = sorted({error["code"] for error in result["errors"]})
        raise ValueError("Manifest is ineligible for split assignment: " + ", ".join(codes))
    sources = {entry["source_id"]: entry for entry in registry["sources"]}
    for row in records:
        entry = sources[row["source_id"]]
        if entry["source_role"] != "external" or row["synthetic"] or row["review_status"] != "approved":
            raise ValueError("Only approved, nonsynthetic external records can be assigned")
        if any(name not in entry["allowed_purposes"] for name, _ in targets):
            raise ValueError("Every positive-ratio target split requires explicit source permission")
        if row["split"] in ("dev", "confirmation") and any(name != row["split"] for name, _ in targets):
            raise ValueError("Existing dev and confirmation records are protected; assignment cannot retire or move them")
    assigned = copy.deepcopy(records)
    for component in _components(records):
        identities = sorted([records[index]["source_id"], records[index]["source_version"],
                             records[index]["record_id"]] for index in component)
        payload = json.dumps(["mmbu-split-v1", seed, identities], separators=(",", ":"), ensure_ascii=True)
        digest = hashlib.sha256(payload.encode("utf-8")).digest()
        bucket = int.from_bytes(digest, "big") / (1 << 256)
        cumulative = 0.0
        selected = targets[-1][0]
        for name, ratio in targets:
            cumulative += ratio
            if bucket < cumulative:
                selected = name
                break
        for index in component:
            assigned[index]["split"] = selected
    return assigned
