"""Closed declarations for the Stage A real-source custody sequence.

This module validates identity and intent only.  It grants no source purpose,
does not open a biomedical payload, and performs no network access.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from mmbu_phase1 import canonical


TOP_KEYS = {"schema_id", "schema_version", "python_executable", "work_margin_bytes", "duplicate_method", "sources"}
DUPLICATE_KEYS = {
    "exact_decoded_identity", "perceptual_hash", "maximum_hamming_distance",
    "maximum_aspect_ratio_delta", "comparison_scope", "missing_parent_policy",
}
SOURCE_KEYS = {
    "source_id", "source_version", "source_family", "role", "doi", "canonical_locators",
    "proposed_purposes", "maximum_bytes", "artifacts", "population",
}
ARTIFACT_KEYS = {
    "name", "url", "expected_bytes", "sha256", "upstream_checksum", "media_type", "role",
    "official_file_id", "allowed_hosts",
}
CHECKSUM_KEYS = {"algorithm", "value"}
POPULATION_KEYS = {
    "rule", "allowed_splits", "forbidden_member_prefixes", "minimum_eligible_parents",
    "target_derived_filtering",
}
SOURCE_IDS = {"bus-bra", "pathmnist-224", "busi-whu"}
EXPECTED_PURPOSES = {
    "bus-bra": ["release", "train"],
    "pathmnist-224": ["release", "train"],
    "busi-whu": ["confirmation", "release"],
}
EXPECTED_ROLES = {"bus-bra": "training", "pathmnist-224": "training", "busi-whu": "confirmation"}
HEX = re.compile(r"[0-9a-f]+")
GLOB = re.compile(r"[*?\[\]]")
LAUNCH_ID = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}")
PACKET_KEYS = {
    "schema_id", "schema_version", "packet_id", "config_digest", "repository_commit", "launch_id",
    "run_root", "created_at", "work_margin_bytes", "sources", "forbidden_operations", "record_digest",
}
PACKET_SOURCE_KEYS = {
    "source_id", "source_version", "source_family", "proposed_purposes", "maximum_bytes", "artifacts",
    "retrieval_method", "retrieval_command", "staging_destination", "inspection_prohibited",
}
FORBIDDEN_OPERATIONS = [
    "gpu_use", "mmbu_public_access", "model_loading", "retry_or_resume", "training", "upload_or_submit",
]


def _closed(value: object, keys: set[str], path: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        actual = set(value) if isinstance(value, dict) else type(value).__name__
        raise ValueError(f"{path} must have exact keys {sorted(keys)}; got {actual}")
    return value


def _text(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{path} must be a nonempty string")
    return value


def _positive_int(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{path} must be a positive integer")
    return value


def _sorted_unique_strings(value: object, path: str, *, empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not empty) or any(not isinstance(x, str) or not x for x in value):
        raise ValueError(f"{path} must be a {'possibly empty ' if empty else 'nonempty '}string array")
    if value != sorted(set(value)):
        raise ValueError(f"{path} must be unique and UTF-8 sorted")
    return value


def _https(value: object, path: str) -> str:
    url = _text(value, path)
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"{path} must be an absolute HTTPS URL")
    return url


def _hex(value: object, length: int, path: str) -> str:
    text = _text(value, path)
    if len(text) != length or HEX.fullmatch(text) is None:
        raise ValueError(f"{path} must be {length} lowercase hexadecimal characters")
    return text


def validate_stage_a_config(config: object) -> dict:
    root = _closed(config, TOP_KEYS, "config")
    if root["schema_id"] != "mmbu.phase1.source_admission_stage_a_config" or root["schema_version"] != 1:
        raise ValueError("unsupported Stage A config schema")
    if root["python_executable"] != "/storage/groups/rrg_shared/hpc/Research/Code/mylibs/anaconda3/bin/python3":
        raise ValueError("python_executable differs from the measured MOCS runtime")
    if _positive_int(root["work_margin_bytes"], "work_margin_bytes") != 20 * 1024**3:
        raise ValueError("work_margin_bytes must be exactly 20 GiB")

    duplicate = _closed(root["duplicate_method"], DUPLICATE_KEYS, "duplicate_method")
    if duplicate != {
        "exact_decoded_identity": "sha256_rgb_pixels_width_height_v1",
        "perceptual_hash": "dhash64",
        "maximum_hamming_distance": 4,
        "maximum_aspect_ratio_delta": 0.05,
        "comparison_scope": "within_and_across_stage_a_sources",
        "missing_parent_policy": "reject_record",
    }:
        raise ValueError("duplicate_method differs from the frozen Stage A contract")

    sources = root["sources"]
    if not isinstance(sources, dict) or set(sources) != SOURCE_IDS:
        raise ValueError("sources must contain exactly the three frozen source IDs")
    for source_id in sorted(SOURCE_IDS):
        source = _closed(sources[source_id], SOURCE_KEYS, f"sources.{source_id}")
        if source["source_id"] != source_id:
            raise ValueError(f"sources.{source_id}.source_id mismatch")
        for key in ("source_version", "source_family", "doi"):
            _text(source[key], f"sources.{source_id}.{key}")
        if source["role"] != EXPECTED_ROLES[source_id]:
            raise ValueError(f"sources.{source_id}.role differs from the frozen role")
        locators = _sorted_unique_strings(source["canonical_locators"], f"sources.{source_id}.canonical_locators")
        for index, locator in enumerate(locators):
            _https(locator, f"sources.{source_id}.canonical_locators[{index}]")
        purposes = _sorted_unique_strings(source["proposed_purposes"], f"sources.{source_id}.proposed_purposes")
        if purposes != EXPECTED_PURPOSES[source_id]:
            raise ValueError(f"sources.{source_id}.proposed_purposes differs from the frozen review request")
        maximum = _positive_int(source["maximum_bytes"], f"sources.{source_id}.maximum_bytes")

        artifacts = source["artifacts"]
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError(f"sources.{source_id}.artifacts must be nonempty")
        names: list[str] = []
        expected_total = 0
        for index, raw_artifact in enumerate(artifacts):
            path = f"sources.{source_id}.artifacts[{index}]"
            artifact = _closed(raw_artifact, ARTIFACT_KEYS, path)
            name = _text(artifact["name"], f"{path}.name")
            if "/" in name or "\\" in name or GLOB.search(name):
                raise ValueError(f"{path}.name must be an exact basename without glob characters")
            names.append(name)
            url = _https(artifact["url"], f"{path}.url")
            hosts = _sorted_unique_strings(artifact["allowed_hosts"], f"{path}.allowed_hosts")
            if urlparse(url).hostname not in hosts:
                raise ValueError(f"{path}.url host is not allowlisted")
            expected_total += _positive_int(artifact["expected_bytes"], f"{path}.expected_bytes")
            if artifact["sha256"] is not None:
                _hex(artifact["sha256"], 64, f"{path}.sha256")
            checksum = artifact["upstream_checksum"]
            if checksum is not None:
                checksum = _closed(checksum, CHECKSUM_KEYS, f"{path}.upstream_checksum")
                lengths = {"md5": 32, "sha256": 64}
                if checksum["algorithm"] not in lengths:
                    raise ValueError(f"{path}.upstream_checksum.algorithm is unsupported")
                _hex(checksum["value"], lengths[checksum["algorithm"]], f"{path}.upstream_checksum.value")
            for key in ("media_type", "role", "official_file_id"):
                _text(artifact[key], f"{path}.{key}")
        if len(names) != len(set(names)):
            raise ValueError(f"sources.{source_id}.artifacts contains duplicate basenames")
        if expected_total > maximum:
            raise ValueError(f"sources.{source_id}.maximum_bytes is below expected artifact bytes")

        population = _closed(source["population"], POPULATION_KEYS, f"sources.{source_id}.population")
        _text(population["rule"], f"sources.{source_id}.population.rule")
        allowed = _sorted_unique_strings(population["allowed_splits"], f"sources.{source_id}.population.allowed_splits")
        forbidden = _sorted_unique_strings(
            population["forbidden_member_prefixes"],
            f"sources.{source_id}.population.forbidden_member_prefixes",
            empty=True,
        )
        _positive_int(population["minimum_eligible_parents"], f"sources.{source_id}.population.minimum_eligible_parents")
        if population["target_derived_filtering"] is not False:
            raise ValueError(f"sources.{source_id}.population.target_derived_filtering must be false")
        if source_id == "pathmnist-224" and (allowed != ["train", "val"] or forbidden != ["test_"]):
            raise ValueError("PathMNIST population must allow only train/val and forbid test_ members")
    return root


def load_stage_a_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return validate_stage_a_config(json.load(handle))


def _packet_body(
    config: dict,
    repository_commit: str,
    launch_id: str,
    run_root: str,
    created_at: str,
) -> dict:
    validate_stage_a_config(config)
    _hex(repository_commit, 40, "repository_commit")
    if LAUNCH_ID.fullmatch(launch_id) is None:
        raise ValueError("launch_id must be a UTC timestamp plus a lowercase UUIDv4")
    expected_root = f"/storage/scr/npl015/mmbu-admission/{launch_id}"
    if run_root != expected_root:
        raise ValueError(f"run_root must be exactly {expected_root}")
    try:
        parsed_created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        raise ValueError("created_at must be an RFC 3339 timestamp") from None
    if parsed_created.tzinfo is None or not created_at.endswith("Z"):
        raise ValueError("created_at must be UTC with a Z suffix")

    sources = {}
    for source_id in sorted(config["sources"]):
        declaration = config["sources"][source_id]
        command = [
            config["python_executable"],
            f"{run_root}/repo/tools/source_admission_stage_a.py",
            "acquire-source",
            "--packet",
            f"{run_root}/records/acquisition-packet.json",
            "--source-id",
            source_id,
        ]
        sources[source_id] = {
            "source_id": source_id,
            "source_version": declaration["source_version"],
            "source_family": declaration["source_family"],
            "proposed_purposes": list(declaration["proposed_purposes"]),
            "maximum_bytes": declaration["maximum_bytes"],
            "artifacts": deepcopy(declaration["artifacts"]),
            "retrieval_method": "stage_a_python_o_excl_stream_v1",
            "retrieval_command": command,
            "staging_destination": f"{run_root}/staging/{source_id}",
            "inspection_prohibited": True,
        }
    return {
        "schema_id": "mmbu.phase1.source_admission_stage_a_packet",
        "schema_version": 1,
        "packet_id": f"stage-a-{launch_id}",
        "config_digest": canonical.value_digest(config),
        "repository_commit": repository_commit,
        "launch_id": launch_id,
        "run_root": run_root,
        "created_at": created_at,
        "work_margin_bytes": config["work_margin_bytes"],
        "sources": sources,
        "forbidden_operations": list(FORBIDDEN_OPERATIONS),
    }


def build_acquisition_packet(
    config: dict,
    repository_commit: str,
    launch_id: str,
    run_root: str,
    created_at: str,
) -> dict:
    """Return a deterministic sealed packet; it is not an authorization."""
    return canonical.seal(_packet_body(config, repository_commit, launch_id, run_root, created_at))


def validate_acquisition_packet(packet: object, config: dict) -> dict:
    """Validate a packet against its frozen config and derived command surface."""
    record = _closed(packet, PACKET_KEYS, "packet")
    for source_id, source in record.get("sources", {}).items():
        _closed(source, PACKET_SOURCE_KEYS, f"packet.sources.{source_id}")
    expected = build_acquisition_packet(
        config,
        record["repository_commit"],
        record["launch_id"],
        record["run_root"],
        record["created_at"],
    )
    if canonical.dumps(record) != canonical.dumps(expected):
        raise ValueError("packet differs from the deterministic Stage A declaration")
    return record


__all__ = [
    "build_acquisition_packet",
    "load_stage_a_config",
    "validate_acquisition_packet",
    "validate_stage_a_config",
]
