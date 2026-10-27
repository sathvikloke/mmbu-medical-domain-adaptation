"""Closed declarations for the Stage A real-source custody sequence.

This module validates identity and intent only.  It grants no source purpose,
does not open a biomedical payload, and performs no network access.
"""

from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import zipfile
import csv
import io
import xml.etree.ElementTree as ET
from copy import deepcopy
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

from mmbu_phase1 import canonical
from mmbu_phase1.external_trust import ExternalAuthorityCapability
from mmbu_phase1.store import RecordStore


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
FROZEN_SOURCE_IDENTITIES = {
    "bus-bra": {
        "source_version": "1.0",
        "source_family": "bus-bra",
        "doi": "10.5281/zenodo.8231412",
        "canonical_locators": ["https://zenodo.org/records/8231412"],
        "maximum_bytes": 134217728,
    },
    "pathmnist-224": {
        "source_version": "3.0",
        "source_family": "nct-crc",
        "doi": "10.5281/zenodo.10519652",
        "canonical_locators": [
            "https://github.com/MedMNIST/MedMNIST",
            "https://zenodo.org/records/10519652",
        ],
        "maximum_bytes": 12633243648,
    },
    "busi-whu": {
        "source_version": "3",
        "source_family": "busi-whu",
        "doi": "10.17632/k6cpmwybk3.3",
        "canonical_locators": ["https://data.mendeley.com/datasets/k6cpmwybk3/3"],
        "maximum_bytes": 129000000,
    },
}
FROZEN_ARTIFACT_IDENTITIES = {
    "bus-bra": [{
        "name": "BUSBRA.zip",
        "url": "https://zenodo.org/api/records/8231412/files/BUSBRA.zip/content",
        "expected_bytes": 133917740,
        "sha256": None,
        "upstream_checksum": {"algorithm": "md5", "value": "1f8b2be6476d58fc97bfb5e5a1ea9bab"},
        "media_type": "application/zip",
        "role": "archive",
        "official_file_id": "BUSBRA.zip",
        "allowed_hosts": ["zenodo.org"],
    }],
    "pathmnist-224": [
        {
            "name": "pathmnist_224.npz",
            "url": "https://zenodo.org/api/records/10519652/files/pathmnist_224.npz/content",
            "expected_bytes": 12629854322,
            "sha256": None,
            "upstream_checksum": {"algorithm": "md5", "value": "2c51a510bcdc9cf8ddb2af93af1eadec"},
            "media_type": "application/zip",
            "role": "archive",
            "official_file_id": "pathmnist_224.npz",
            "allowed_hosts": ["zenodo.org"],
        },
        {
            "name": "pathmnist_split_info.csv",
            "url": "https://drive.usercontent.google.com/download?id=1uxZpSW3O02TIYVzNgKBsbN2nQb-ZrzZW&export=download",
            "expected_bytes": 2785821,
            "sha256": "ba6f166b2deae125086ecb7ff84223daa90bf35a7c95053be4f030be1a4ac0bb",
            "upstream_checksum": {"algorithm": "md5", "value": "76fa12d34fd5b50cfa56310ae3f090a3"},
            "media_type": "text/csv",
            "role": "mapping",
            "official_file_id": "1uxZpSW3O02TIYVzNgKBsbN2nQb-ZrzZW",
            "allowed_hosts": ["drive.usercontent.google.com"],
        },
    ],
    "busi-whu": [
        {
            "name": "BUSI-WHU.zip",
            "url": "https://data.mendeley.com/public-files/datasets/k6cpmwybk3/files/5aa18322-e19e-4779-8392-e621ec660f79/file_downloaded",
            "expected_bytes": 128106790,
            "sha256": "5d10c0bb931666e9cff48db9161febc0ec0c74e4b611c2edcbb9726f6d9d74cc",
            "upstream_checksum": {"algorithm": "sha256", "value": "5d10c0bb931666e9cff48db9161febc0ec0c74e4b611c2edcbb9726f6d9d74cc"},
            "media_type": "application/zip",
            "role": "archive",
            "official_file_id": "5aa18322-e19e-4779-8392-e621ec660f79",
            "allowed_hosts": [
                "data.mendeley.com",
                "prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com",
            ],
        },
        {
            "name": "Patient_infos_BUSI-WHU.xlsx",
            "url": "https://data.mendeley.com/public-files/datasets/k6cpmwybk3/files/6f13c484-94e1-4378-bc73-293a68671948/file_downloaded",
            "expected_bytes": 92017,
            "sha256": "14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44",
            "upstream_checksum": {"algorithm": "sha256", "value": "14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44"},
            "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "role": "patient_mapping",
            "official_file_id": "6f13c484-94e1-4378-bc73-293a68671948",
            "allowed_hosts": [
                "data.mendeley.com",
                "prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com",
            ],
        },
    ],
}
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
STRUCTURAL_OPENING_PACKET_KEYS = {
    "schema_id", "schema_version", "packet_id", "config_digest", "repository_commit", "launch_id",
    "run_root", "created_at", "sources", "permitted_purpose", "forbidden_operations",
    "image_payload_decoding_allowed", "model_use_authorized", "mmbu_public_content_used", "record_digest",
}
STRUCTURAL_OPENING_SOURCE_KEYS = {
    "source_id", "source_version", "source_family", "proposed_purposes", "acquisition_packet_digest",
    "acquisition_authorization_digest", "authorization_registry_digest",
    "acquisition_execution_receipt_digest", "staging_destination", "observed_artifacts", "permitted_reads",
}
STRUCTURAL_READS = {
    "bus-bra": ["archive_member_headers"],
    "pathmnist-224": ["archive_member_headers", "mapping_schema", "train_val_array_headers"],
    "busi-whu": ["archive_member_headers", "workbook_schema"],
}
STRUCTURAL_OPENING_FORBIDDEN = [
    "image_payload_decoding", "label_value_reading", "mmbu_public_access", "model_loading",
    "test_member_opening", "training", "upload_or_submit",
]
BUSI_WHU_HEADERS = (
    "patient_index", "Benign(0)\nmalignant(1)", "img_names", "scale(pixel/cm)",
    "scale_category", "gt_area(pixel2)", "Image_area(pixel2)", "gt(cm2)", "gt/all",
    "centroid_x(pixel)", "centroid_y(pixel)", "max_diameter(pixel)", "min_diameter(pixel)",
)


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
        identity = FROZEN_SOURCE_IDENTITIES[source_id]
        for key, expected in identity.items():
            if source[key] != expected:
                raise ValueError(f"sources.{source_id}.{key} differs from the frozen official identity")

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
        if artifacts != FROZEN_ARTIFACT_IDENTITIES[source_id]:
            raise ValueError(f"sources.{source_id}.artifacts differ from the frozen official identities")
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
            "--records",
            f"{run_root}/records/acquisition-authority.json",
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


def _validate_acquisition_packet_source(packet: object, config: dict, source_id: str) -> dict:
    """Authenticate a historical packet and revalidate only the consumed source declaration."""
    record = _closed(packet, PACKET_KEYS, "packet")
    if record.get("record_digest") != canonical.record_digest(record):
        raise ValueError("packet record digest is invalid")
    if record.get("schema_id") != "mmbu.phase1.source_admission_stage_a_packet" or record.get("schema_version") != 1:
        raise ValueError("packet schema identity is invalid")
    if not isinstance(record.get("sources"), dict) or set(record["sources"]) != SOURCE_IDS:
        raise ValueError("packet must contain exactly the three frozen sources")
    for candidate_id, source in record["sources"].items():
        _closed(source, PACKET_SOURCE_KEYS, f"packet.sources.{candidate_id}")
    if source_id not in SOURCE_IDS:
        raise ValueError("source_id is absent from the frozen source set")
    expected = _packet_body(
        config,
        record["repository_commit"],
        record["launch_id"],
        record["run_root"],
        record["created_at"],
    )
    if canonical.dumps(record["sources"][source_id]) != canonical.dumps(expected["sources"][source_id]):
        raise ValueError(f"packet source {source_id!r} differs from the current frozen declaration")
    if record["work_margin_bytes"] != expected["work_margin_bytes"]:
        raise ValueError("packet work margin differs from the frozen declaration")
    if record["forbidden_operations"] != expected["forbidden_operations"]:
        raise ValueError("packet forbidden operations differ from the frozen declaration")
    return record


def _structural_opening_packet_body(
    config: dict,
    evidence: dict[str, dict],
    repository_commit: str,
    launch_id: str,
    run_root: str,
    created_at: str,
) -> dict:
    """Bind successful transport evidence without granting payload access."""
    from mmbu_phase1 import admission

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
    if not isinstance(evidence, dict) or set(evidence) != SOURCE_IDS:
        raise ValueError("structural opening evidence must contain exactly the three frozen sources")

    sources = {}
    for source_id in sorted(SOURCE_IDS):
        bundle = _closed(
            evidence[source_id],
            {"packet", "authority_records", "execution_receipt"},
            f"evidence.{source_id}",
        )
        packet = _validate_acquisition_packet_source(bundle["packet"], config, source_id)
        records = bundle["authority_records"]
        if not isinstance(records, list):
            raise ValueError(f"evidence.{source_id}.authority_records must be a record array")
        receipt = bundle["execution_receipt"]
        authority = _verify_acquisition_authority_records(
            records,
            packet,
            source_id,
            receipt.get("started_at") if isinstance(receipt, dict) else "",
        )
        store = RecordStore([*records, receipt])
        receipt = admission.check_acquisition_execution_receipt(
            store, receipt.get("record_digest") if isinstance(receipt, dict) else None,
            f"evidence.{source_id}.execution_receipt",
        )
        if receipt["terminal_status"] != "succeeded":
            raise ValueError(f"evidence.{source_id} does not contain a successful acquisition")
        declaration = config["sources"][source_id]
        packet_source = packet["sources"][source_id]
        sources[source_id] = {
            "source_id": source_id,
            "source_version": declaration["source_version"],
            "source_family": declaration["source_family"],
            "proposed_purposes": list(declaration["proposed_purposes"]),
            "acquisition_packet_digest": packet["record_digest"],
            "acquisition_authorization_digest": authority["authorization"]["record_digest"],
            "authorization_registry_digest": authority["registry"]["record_digest"],
            "acquisition_execution_receipt_digest": receipt["record_digest"],
            "staging_destination": packet_source["staging_destination"],
            "observed_artifacts": deepcopy(receipt["observed_artifacts"]),
            "permitted_reads": list(STRUCTURAL_READS[source_id]),
        }
    return {
        "schema_id": "mmbu.phase1.stage_a_structural_opening_packet",
        "schema_version": 1,
        "packet_id": f"stage-a-structural-opening-{launch_id}",
        "config_digest": canonical.value_digest(config),
        "repository_commit": repository_commit,
        "launch_id": launch_id,
        "run_root": run_root,
        "created_at": created_at,
        "sources": sources,
        "permitted_purpose": "quarantine_inspection",
        "forbidden_operations": list(STRUCTURAL_OPENING_FORBIDDEN),
        "image_payload_decoding_allowed": False,
        "model_use_authorized": False,
        "mmbu_public_content_used": False,
    }


def build_structural_opening_packet(
    config: dict,
    evidence: dict[str, dict],
    repository_commit: str,
    launch_id: str,
    run_root: str,
    created_at: str,
) -> dict:
    """Return a sealed structural-opening proposal; it is not an authorization."""
    return canonical.seal(_structural_opening_packet_body(
        config, evidence, repository_commit, launch_id, run_root, created_at
    ))


def validate_structural_opening_packet(packet: object, config: dict, evidence: dict[str, dict]) -> dict:
    """Validate a structural-opening packet against the exact acquisition evidence."""
    record = _closed(packet, STRUCTURAL_OPENING_PACKET_KEYS, "structural_opening_packet")
    if not isinstance(record.get("sources"), dict):
        raise ValueError("structural_opening_packet.sources must be an object")
    for source_id, source in record["sources"].items():
        _closed(source, STRUCTURAL_OPENING_SOURCE_KEYS, f"structural_opening_packet.sources.{source_id}")
    expected = build_structural_opening_packet(
        config,
        evidence,
        record["repository_commit"],
        record["launch_id"],
        record["run_root"],
        record["created_at"],
    )
    if canonical.dumps(record) != canonical.dumps(expected):
        raise ValueError("structural opening packet differs from the exact acquisition evidence")
    return record


def acquisition_method_digest(packet_source: dict) -> str:
    """Bind the named transport method as a versioned executable contract."""
    return canonical.value_digest({
        "method": packet_source["retrieval_method"],
        "version": 1,
    })


def acquisition_command_digest(packet_source: dict) -> str:
    """Bind the exact argv array; shell text is never part of the authority."""
    return canonical.value_digest({
        "argv": packet_source["retrieval_command"],
        "version": 1,
    })


STAGE_A_ACQUISITION_AUTHORITY_NAMESPACE = "mmbu.phase1.stage-a-acquisition.v1"


def stage_a_acquisition_authority_subject(packet: dict, source_id: str) -> dict:
    """Return the exact source acquisition operation an external owner must sign."""
    if packet.get("record_digest") != canonical.record_digest(packet):
        raise ValueError("acquisition packet digest is invalid")
    source = packet.get("sources", {}).get(source_id)
    if not isinstance(source, dict):
        raise ValueError("source is absent from the acquisition packet")
    return canonical.seal({
        "schema_id": "mmbu.phase1.stage_a_acquisition_authority_subject",
        "schema_version": 1,
        "packet_digest": packet["record_digest"],
        "source_id": source_id,
        "source_version": source["source_version"],
        "source_family": source["source_family"],
        "artifact_names": sorted(row["name"] for row in source["artifacts"]),
        "network_host_allowlist": sorted({
            host for artifact in source["artifacts"] for host in artifact["allowed_hosts"]
        }),
        "maximum_bytes": source["maximum_bytes"],
        "retrieval_method_digest": acquisition_method_digest(source),
        "retrieval_command_digest": acquisition_command_digest(source),
        "staging_destination": source["staging_destination"],
        "permitted_purpose": "quarantine_inspection",
        "inspection_prohibited": True,
    })


def verify_acquisition_authority(
    records: list[dict],
    packet: dict,
    config: dict,
    source_id: str,
    now: str,
    external_authority: object,
) -> dict:
    """Require an independently attested active acquisition head before network use."""
    validate_acquisition_packet(packet, config)
    result = _verify_acquisition_authority_records(records, packet, source_id, now)
    if type(external_authority) is not ExternalAuthorityCapability:
        raise TypeError("Stage A acquisition requires externally verified data-owner authority")
    if external_authority.namespace != STAGE_A_ACQUISITION_AUTHORITY_NAMESPACE:
        raise ValueError("Stage A acquisition external namespace mismatch")
    if external_authority.role != "data-owner":
        raise ValueError("Stage A acquisition external role mismatch")
    subject_digest = canonical.value_digest(
        stage_a_acquisition_authority_subject(packet, source_id)
    )
    if external_authority.subject_digest != subject_digest:
        raise ValueError("Stage A acquisition authority signed another subject")
    signed_at = datetime.fromisoformat(external_authority.signed_at.replace("Z", "+00:00"))
    if signed_at < datetime.fromisoformat(packet["created_at"].replace("Z", "+00:00")):
        raise ValueError("Stage A acquisition external signature predates its sealed packet")
    if signed_at > datetime.fromisoformat(now.replace("Z", "+00:00")):
        raise ValueError("Stage A acquisition external signature follows the authority check")
    if datetime.fromisoformat(external_authority.verified_at.replace("Z", "+00:00")) > datetime.fromisoformat(
        now.replace("Z", "+00:00")
    ):
        raise ValueError("Stage A acquisition external verification follows the authority check")
    return {
        **result,
        "external_authority_evidence_digest": external_authority.verification_evidence_digest,
        "external_authority_principal": external_authority.principal,
    }


def _verify_acquisition_authority_records(
    records: list[dict],
    packet: dict,
    source_id: str,
    now: str,
) -> dict:
    """Validate authority against an already authenticated packet revision."""
    from mmbu_phase1 import admission, fields, registries

    if source_id not in packet["sources"]:
        raise ValueError("source_id is absent from the sealed acquisition packet")
    source = packet["sources"][source_id]
    store = RecordStore(records)
    candidates = store.records("authorization_registry")
    if not candidates:
        raise ValueError("an authorization registry chain is required before acquisition")
    registry = max(candidates, key=lambda row: row["generation"])
    registry = registries.check_authorization_registry_chain(
        store, registry["record_digest"], "acquisition.registry"
    )
    key = f"{source_id}|{source['source_version']}"
    authorization_digest = registry["acquisition_heads"].get(key)
    if authorization_digest is None:
        raise ValueError(f"active acquisition authority is missing for {key!r}")
    authorization = admission.check_acquisition_authorization(
        store, authorization_digest, "acquisition.authorization"
    )
    expected_hosts = sorted({
        host for artifact in source["artifacts"] for host in artifact["allowed_hosts"]
    })
    expected = {
        "source_id": source_id,
        "source_version": source["source_version"],
        "source_family": source["source_family"],
        "allowed_artifact_names": sorted(row["name"] for row in source["artifacts"]),
        "intended_purpose": "quarantine_inspection",
        "staging_destination": source["staging_destination"],
        "retrieval_method_digest": acquisition_method_digest(source),
        "retrieval_command_digest": acquisition_command_digest(source),
        "network_host_allowlist": expected_hosts,
        "maximum_bytes": source["maximum_bytes"],
        "decision": "allowed",
        "inspection_prohibited": True,
    }
    for field, value in expected.items():
        if authorization[field] != value:
            raise ValueError(f"acquisition authorization {field} differs from the sealed packet")
    now_ns = fields.timestamp(now, "acquisition.now")
    if now_ns < fields.timestamp(authorization["authorized_at"], "acquisition.authorized_at"):
        raise ValueError("acquisition authority is not yet active")
    if now_ns >= fields.timestamp(authorization["expires_at"], "acquisition.expires_at"):
        raise ValueError("acquisition authority has expired")
    if fields.timestamp(registry["as_of"], "acquisition.registry.as_of") > now_ns:
        raise ValueError("authorization registry postdates the acquisition check")
    return {"authorization": authorization, "registry": registry, "source": source}


def acquire_artifacts_once(
    packet_source: dict,
    destination: Path,
    open_url,
    *,
    required_free_bytes: int | None = None,
) -> dict:
    """Retrieve each frozen artifact exactly once with create-new semantics.

    A failed transfer deliberately leaves its ``.partial`` bytes in place.
    This function never retries, resumes, replaces, or opens payload content.
    """
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"staging destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    required = required_free_bytes or packet_source["maximum_bytes"] + 20 * 1024**3
    _positive_int(required, "required_free_bytes")
    if shutil.disk_usage(destination.parent).free < required:
        raise OSError("insufficient free space for sealed byte cap plus 20 GiB margin")
    destination.mkdir(mode=0o700)
    observed_artifacts = []
    observed_hosts = set()
    for artifact in packet_source["artifacts"]:
        target = destination / artifact["name"]
        partial = destination / f"{artifact['name']}.partial"
        if target.exists() or partial.exists():
            raise FileExistsError(f"artifact output already exists for {artifact['name']}")
        descriptor = os.open(partial, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
        sha256 = hashlib.sha256()
        upstream = artifact["upstream_checksum"]
        secondary = hashlib.new(upstream["algorithm"]) if upstream is not None else None
        count = 0
        initial_host = urlparse(artifact["url"]).hostname
        if initial_host is not None:
            observed_hosts.add(initial_host)
        try:
            if hasattr(open_url, "set_allowed_hosts"):
                open_url.set_allowed_hosts(set(artifact["allowed_hosts"]))
            response = open_url(artifact["url"])
            with response, os.fdopen(descriptor, "wb") as output:
                final_host = urlparse(response.geturl()).hostname
                if final_host is None or final_host not in artifact["allowed_hosts"]:
                    raise ValueError(f"artifact {artifact['name']} resolved to an unlisted host")
                observed_hosts.add(final_host)
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    count += len(chunk)
                    if count > artifact["expected_bytes"] or count > packet_source["maximum_bytes"]:
                        raise ValueError(f"artifact {artifact['name']} exceeded its sealed byte cap")
                    output.write(chunk)
                    sha256.update(chunk)
                    if secondary is not None:
                        secondary.update(chunk)
                output.flush()
                os.fsync(output.fileno())
            observed_hosts.update(getattr(open_url, "observed_hosts", ()))
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            raise
        if count != artifact["expected_bytes"]:
            raise ValueError(f"artifact {artifact['name']} byte count differs from the frozen identity")
        observed_sha256 = sha256.hexdigest()
        if artifact["sha256"] is not None and observed_sha256 != artifact["sha256"]:
            raise ValueError(f"artifact {artifact['name']} SHA-256 differs from the frozen identity")
        if secondary is not None and secondary.hexdigest() != upstream["value"]:
            raise ValueError(f"artifact {artifact['name']} upstream checksum differs from the frozen identity")
        os.link(partial, target, follow_symlinks=False)
        partial.unlink()
        observed_artifacts.append({
            "logical_path": artifact["name"],
            "bytes": count,
            "sha256": observed_sha256,
        })
    return {
        "observed_hosts": sorted(observed_hosts),
        "observed_artifacts": observed_artifacts,
    }


def verify_inventory_opening(records: list[dict], source_id: str, now: str) -> dict:
    """Resolve the active quarantine and protected-opening graph for one source.

    This function is the only gate inventory code may call.  It creates no
    authority and returns only records already validated by the Phase 1
    contracts.
    """
    from mmbu_phase1 import admission, fields, locks, registries

    _text(source_id, "source_id")
    now_ns = fields.timestamp(now, "now")
    store = RecordStore(records)
    authorization_registries = store.records("authorization_registry")
    opening_registries = store.records("opening_receipt_registry")
    if not authorization_registries or not opening_registries:
        raise ValueError("both authorization and opening registry chains are required")
    authorization_registry = None
    source_digest = None
    for candidate in sorted(authorization_registries, key=lambda row: row["generation"], reverse=True):
        candidate_source = candidate["source_heads"].get(source_id)
        candidate_authorization = candidate["authorization_heads"].get(f"{source_id}|quarantine_inspection")
        if candidate_source is None or candidate_authorization is None:
            continue
        candidate_record = store.get(candidate_source, "source", "inventory.source_candidate")
        if candidate_record["status"] == "quarantined":
            authorization_registry = registries.check_authorization_registry_chain(
                store, candidate["record_digest"], "inventory.authorization_registry"
            )
            source_digest = candidate_source
            break
    if authorization_registry is None or source_digest is None:
        raise ValueError(f"source {source_id!r} has no quarantine-inspection registry generation")
    source = admission.check_source(store, source_digest, "inventory.source")
    if source["status"] != "quarantined" or source["allowed_purposes"] != ["quarantine_inspection"]:
        raise ValueError("inventory requires the active quarantined source with quarantine-only authority")
    manifest = admission.check_source_artifact_manifest(
        store, source["artifact_manifest_digest"], "inventory.manifest"
    )
    acquisition = admission.check_acquisition_authorization(
        store, manifest["acquisition_authorization_digest"], "inventory.acquisition"
    )
    if now_ns >= fields.timestamp(acquisition["expires_at"], "inventory.acquisition.expires_at"):
        raise ValueError("acquisition authorization has expired")

    authorization_digest = authorization_registry["authorization_heads"].get(
        f"{source_id}|quarantine_inspection"
    )
    if authorization_digest is None:
        raise ValueError("active quarantine-inspection authorization is missing")
    authorization = admission.check_purpose_authorization(
        store, authorization_digest, "inventory.authorization"
    )
    if authorization["decision"] != "allowed" or authorization["source_digest"] != source_digest:
        raise ValueError("quarantine-inspection authorization does not allow the active source")
    if len(authorization["split_digests"]) != 1:
        raise ValueError("quarantine inspection requires exactly one container split")
    split = admission.check_split(store, authorization["split_digests"][0], "inventory.split")

    inventory_locks = []
    for lock in store.records("prospective_lock"):
        if (
            lock.get("scope", {}).get("phase") == "custody_inventory"
            and lock.get("scope", {}).get("purpose") == "quarantine_inspection"
            and lock.get("candidate_ids") == [source_id]
            and source_digest in lock.get("input_artifact_digests", [])
            and manifest["record_digest"] in lock.get("input_artifact_digests", [])
        ):
            inventory_locks.append(lock)
    if len(inventory_locks) != 1:
        raise ValueError("exactly one matching custody-inventory lock is required")
    lock = locks.validate_prospective_lock(inventory_locks[0], "inventory.lock")

    opening_registry = max(opening_registries, key=lambda row: row["generation"])
    opening_registry = registries.check_opening_receipt_registry_chain(
        store, opening_registry["record_digest"], "inventory.opening_registry"
    )
    heads = [head for head in opening_registry["heads"] if head["lock_digest"] == lock["record_digest"]]
    if len(heads) != 1:
        raise ValueError("inventory lock lacks one active opening-receipt head")
    opening = locks.require_registered_head(
        store,
        opening_registry["record_digest"],
        heads[0]["head_receipt_digest"],
        "inventory.opening_registry",
    )
    if opening["opening_kind"] != "protected_access" or opening["manifest_digests"] != [manifest["record_digest"]]:
        raise ValueError("protected opening does not bind the exact source manifest")
    if fields.timestamp(opening["first_access_at"], "inventory.opening.first_access_at") > now_ns:
        raise ValueError("inventory opening is later than the requested verification time")
    return {
        "source": source,
        "manifest": manifest,
        "split": split,
        "authorization": authorization,
        "lock": lock,
        "opening": opening,
        "authorization_registry": authorization_registry,
        "opening_registry": opening_registry,
    }


def _at(value: str, seconds: int) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or not value.endswith("Z"):
        raise ValueError("reviewed_at must be UTC with a Z suffix")
    return (parsed + timedelta(seconds=seconds)).isoformat(timespec="seconds").replace("+00:00", "Z")


STAGE_A_STRUCTURAL_AUTHORITY_NAMESPACE = "mmbu.phase1.stage-a-structural-opening.v1"


def stage_a_structural_authority_subject(packet: dict, source_id: str) -> dict:
    """Return the exact sealed subject that two external authorities must sign."""
    if packet.get("record_digest") != canonical.record_digest(packet):
        raise ValueError("structural opening packet digest is invalid")
    source = packet.get("sources", {}).get(source_id)
    if not isinstance(source, dict):
        raise ValueError("source is absent from the structural opening packet")
    return canonical.seal({
        "schema_id": "mmbu.phase1.stage_a_structural_opening_authority_subject",
        "schema_version": 1,
        "packet_digest": packet["record_digest"],
        "source_id": source_id,
        "source_version": source["source_version"],
        "permitted_reads": source["permitted_reads"],
    })


def _validate_external_structural_authorities(
    packet: dict, source_id: str, owner: object, reviewer: object, reviewed_at: str,
) -> tuple[ExternalAuthorityCapability, ExternalAuthorityCapability]:
    if type(owner) is not ExternalAuthorityCapability or type(reviewer) is not ExternalAuthorityCapability:
        raise TypeError("Stage A structural opening requires two externally verified authority capabilities")
    subject_digest = canonical.value_digest(stage_a_structural_authority_subject(packet, source_id))
    for capability, role, label in (
        (owner, "data-owner", "owner"),
        (reviewer, "independent-reviewer", "reviewer"),
    ):
        if capability.namespace != STAGE_A_STRUCTURAL_AUTHORITY_NAMESPACE:
            raise ValueError(f"Stage A {label} external namespace mismatch")
        if capability.role != role:
            raise ValueError(f"Stage A {label} external role mismatch")
        if capability.subject_digest != subject_digest:
            raise ValueError(f"Stage A {label} signed another subject")
        if not capability.principal:
            raise ValueError(f"Stage A {label} external principal is empty")
        if datetime.fromisoformat(capability.verified_at.replace("Z", "+00:00")) > datetime.fromisoformat(
            reviewed_at.replace("Z", "+00:00")
        ):
            raise ValueError(f"Stage A {label} external verification follows internal authorization")
    if owner.principal == reviewer.principal:
        raise ValueError("Stage A owner and independent reviewer must be different principals")
    return owner, reviewer


def _attestation(
    record: dict, reviewer: ExternalAuthorityCapability,
    owner: ExternalAuthorityCapability, at: str,
) -> dict:
    payload = {
        "statement_version": "mmbu-review-attestation-v1",
        "reviewer_id": reviewer.principal,
        "reviewer_role": "purpose_authorization_reviewer",
        "subject_digest": canonical.subject_digest(record, "single_attestation"),
        "purposes": ["quarantine_inspection"],
        "disposition": "approved",
        "limitations_digest": canonical.raw_digest(
            b"Structural header/schema inspection only; no model use, labels, image decoding, training, or release."
        ),
        "reviewed_at": at,
        "declaration_text_digest": reviewer.signature_sha256,
    }
    return canonical.seal({
        "schema_id": "mmbu.phase1.reviewer_attestation",
        "schema_version": 1,
        "attestation_id": f"stage-a-structural-purpose-{record['authorization_id']}",
        "payload": payload,
        "payload_digest": canonical.value_digest(payload),
        "verification": {
            "method": "cryptographic_signature",
            "verifier_id": owner.principal,
            "verified_at": at,
            "verification_artifact_digest": reviewer.verification_evidence_digest,
        },
    })


def build_structural_opening_records(
    packet: dict,
    source_id: str,
    acquisition_records: list[dict],
    execution_receipt: dict,
    owner_authority: ExternalAuthorityCapability,
    reviewer_authority: ExternalAuthorityCapability,
    reviewed_at: str,
) -> list[dict]:
    """Build the exact quarantine-only chain needed for one structural opening.

    Two independently pinned external signatures are bound as evidence, but this function creates no
    rights, grouping, clinical, model-use, training, confirmation, or release
    authority.
    """
    from mmbu_phase1 import admission, locks, registries

    if packet.get("record_digest") != canonical.record_digest(packet):
        raise ValueError("structural opening packet digest is invalid")
    if packet.get("schema_id") != "mmbu.phase1.stage_a_structural_opening_packet":
        raise ValueError("unexpected structural opening packet schema")
    if packet.get("image_payload_decoding_allowed") or packet.get("model_use_authorized"):
        raise ValueError("structural packet attempts to grant forbidden access")
    source = packet.get("sources", {}).get(source_id)
    if not isinstance(source, dict):
        raise ValueError("source is absent from the structural opening packet")
    owner_authority, reviewer_authority = _validate_external_structural_authorities(
        packet, source_id, owner_authority, reviewer_authority, reviewed_at,
    )

    receipt_store = RecordStore([*acquisition_records, execution_receipt])
    authorization = admission.check_acquisition_authorization(
        receipt_store, source["acquisition_authorization_digest"], "structural.acquisition_authorization"
    )
    registry = registries.check_authorization_registry_chain(
        receipt_store, source["authorization_registry_digest"], "structural.acquisition_registry"
    )
    if registry["acquisition_heads"].get(f"{source_id}|{source['source_version']}") != authorization["record_digest"]:
        raise ValueError("structural packet does not bind the active acquisition authority")
    for name in ("source_id", "source_version", "source_family", "staging_destination"):
        if source[name] != authorization[name]:
            raise ValueError(f"structural source {name} differs from acquisition authority")
    receipt = admission.check_acquisition_execution_receipt(
        receipt_store, execution_receipt.get("record_digest"), "structural.execution_receipt"
    )
    if receipt["terminal_status"] != "succeeded" or receipt["record_digest"] != source["acquisition_execution_receipt_digest"]:
        raise ValueError("structural packet does not bind this successful execution receipt")

    declaration_artifacts = {row["logical_path"]: row for row in receipt["observed_artifacts"]}
    artifacts = []
    for name in sorted(declaration_artifacts):
        row = declaration_artifacts[name]
        suffix = Path(name).suffix.lower()
        artifacts.append({
            "logical_path": name,
            "bytes": row["bytes"],
            "sha256": row["sha256"],
            "upstream_checksum": None,
            "media_type": {
                ".zip": "application/zip",
                ".npz": "application/zip",
                ".csv": "text/csv",
                ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }.get(suffix, "application/octet-stream"),
            "role": "archive" if suffix in {".zip", ".npz"} else "metadata",
        })
    manifest = canonical.seal({
        "schema_id": "mmbu.phase1.source_artifact_manifest",
        "schema_version": 1,
        "manifest_id": f"stage-a-structural-{packet['launch_id']}-{source_id}",
        "source_id": source_id,
        "source_version": source["source_version"],
        "source_family": source["source_family"],
        "canonical_locator_ids": authorization["canonical_locator_ids"],
        "acquisition_authorization_digest": authorization["record_digest"],
        "acquisition_execution_receipt_digest": receipt["record_digest"],
        "artifacts": artifacts,
        "total_bytes": sum(row["bytes"] for row in artifacts),
        "retriever_id": receipt["operator_id"],
        "retrieved_at": receipt["ended_at"],
        "retrieval_log_digest": receipt["retrieval_log_digest"],
    })
    base_source = {
        "schema_id": "mmbu.phase1.source",
        "schema_version": 1,
        "source_id": source_id,
        "source_version": source["source_version"],
        "source_family": source["source_family"],
        "origin_class": "external_quarantine",
        "artifact_manifest_digest": manifest["record_digest"],
        "proposed_purposes": source["proposed_purposes"],
        "rights_receipt_digest": None,
        "grouping_receipt_digest": None,
        "qa_receipt_digest": None,
        "admission_decision_receipt_digest": None,
        "approval_attestation_digest": None,
        "reviewer_id": None,
        "reviewed_at": None,
    }
    candidate = canonical.seal({
        **base_source, "status": "candidate", "allowed_purposes": [],
        "created_at": reviewed_at, "supersedes_digest": None,
    })
    quarantined = canonical.seal({
        **base_source, "status": "quarantined", "allowed_purposes": ["quarantine_inspection"],
        "created_at": _at(reviewed_at, 1), "supersedes_digest": candidate["record_digest"],
    })
    artifact_names = [row["logical_path"] for row in artifacts]
    split = canonical.seal({
        "schema_id": "mmbu.phase1.split", "schema_version": 1,
        "split_id": f"stage-a-structural-quarantine-{source_id}",
        "source_digest": quarantined["record_digest"],
        "source_artifact_manifest_digest": manifest["record_digest"],
        "role": "quarantine", "record_manifest_digest": canonical.value_digest(artifact_names),
        "parent_namespace": "artifact_path", "parent_ids_digest": canonical.value_digest(artifact_names),
        "record_ids_digest": canonical.value_digest(artifact_names),
        "construction_rule_digest": canonical.value_digest({"rule": "mmbu.phase1.canonical_path_projection", "version": 1}),
        "created_at": _at(reviewed_at, 1),
    })
    basis = sorted({
        packet["record_digest"], owner_authority.verification_evidence_digest,
        reviewer_authority.verification_evidence_digest,
    })
    purpose_body = {
        "schema_id": "mmbu.phase1.purpose_authorization", "schema_version": 1,
        "authorization_id": f"stage-a-structural-{packet['launch_id']}-{source_id}",
        "purpose": "quarantine_inspection", "source_digest": quarantined["record_digest"],
        "split_digests": [split["record_digest"]], "lineage_root_digests": [],
        "decision": "allowed", "decision_basis_digests": basis,
        "reviewer_id": reviewer_authority.principal,
        "reviewer_attestation_digest": None, "released_checkpoint_digest": None,
        "validated_model_lineage_digest": None, "release_rights_receipt_digest": None,
        "release_decision_receipt_digest": None, "no_new_data_access": None,
        "decided_at": _at(reviewed_at, 2), "expires_at": None, "supersedes_digest": None,
    }
    attestation = _attestation(purpose_body, reviewer_authority, owner_authority, _at(reviewed_at, 2))
    purpose = canonical.seal({**purpose_body, "reviewer_attestation_digest": attestation["record_digest"]})

    prior_registry = max(
        (row for row in acquisition_records if row.get("schema_id") == "mmbu.phase1.authorization_registry"),
        key=lambda row: row["generation"],
    )
    registry = canonical.seal({
        "schema_id": "mmbu.phase1.authorization_registry", "schema_version": 1,
        "registry_id": f"stage-a-structural-{source_id}-g{prior_registry['generation'] + 1}",
        "generation": prior_registry["generation"] + 1,
        "supersedes_registry_digest": prior_registry["record_digest"],
        "acquisition_authorization_digests": list(prior_registry["acquisition_authorization_digests"]),
        "source_record_digests": sorted([candidate["record_digest"], quarantined["record_digest"]]),
        "purpose_authorization_digests": [purpose["record_digest"]],
        "acquisition_heads": deepcopy(prior_registry["acquisition_heads"]),
        "source_heads": {source_id: quarantined["record_digest"]},
        "authorization_heads": {f"{source_id}|quarantine_inspection": purpose["record_digest"]},
        "revoked_digests": list(prior_registry["revoked_digests"]), "as_of": _at(reviewed_at, 2),
    })
    source_state = canonical.value_digest({"packet": packet["record_digest"], "source": source})
    lock = canonical.seal({
        "schema_id": "mmbu.phase1.prospective_lock", "schema_version": 1,
        "lock_id": f"stage-a-structural-{source_id}",
        "scope": {"scope_id": f"stage-a-structural-{source_id}", "purpose": "quarantine_inspection",
                  "phase": "custody_inventory", "primary_estimand_id": "structural-schema-complete",
                  "comparison_ids": ["structural-only"], "analysis_population_digest": manifest["record_digest"]},
        "source_state_digest": source_state,
        "input_artifact_digests": sorted([manifest["record_digest"], quarantined["record_digest"]]),
        "qa_sampling_plan_digest": None, "excluded_result_digests": [], "candidate_ids": [source_id],
        "seed_ids": [], "thresholds": [], "groups": [],
        "evaluator_digest": canonical.value_digest({"contract": "stage-a-structural-inspector", "version": 1}),
        "multiplicity_rule": {"family_id": "structural", "alpha": 0.05, "method": "none",
                                "hypothesis_ids": ["structural-complete"],
                                "rule_digest": canonical.value_digest({"rule": "structural-only", "version": 1})},
        "compute_plan_digest": canonical.value_digest({"partition": "epyc-cpu", "gpu": False, "version": 1}),
        "decision_function_digest": canonical.value_digest({"rule": "emit-schema-no-decision", "version": 1}),
        "claim_boundary": {"primary_claim_id": "structural-schema-complete",
                           "allowed_claim_ids": ["structural-schema-complete"],
                           "prohibited_claim_ids": ["clinical-validity", "model-use", "training-ready"],
                           "failure_claim_id": "structural-schema-failed"},
        "planned_opening_event": {"opening_kind": "protected_access", "trigger": "stage-a-structural-inspector",
                                  "not_before": _at(reviewed_at, 4), "operator_role": "custody_reviewer",
                                  "protected_artifact_digests": [manifest["record_digest"]],
                                  "command_template_digest": canonical.value_digest({"reads": source["permitted_reads"], "version": 1})},
        "retry_policies": [], "created_at": _at(reviewed_at, 3),
        "supersedes_digest": None, "amendment_reason": None,
    })
    opening = canonical.seal({
        "schema_id": "mmbu.phase1.opening_receipt", "schema_version": 1,
        "opening_id": f"stage-a-structural-{packet['launch_id']}-{source_id}",
        "lock_digest": lock["record_digest"], "source_state_digest": source_state,
        "manifest_digests": [manifest["record_digest"]],
        "command_digest": canonical.value_digest({"reads": source["permitted_reads"], "version": 1}),
        "environment_digest": canonical.value_digest({"partition": "epyc-cpu", "gpu": False, "version": 1}),
        "operator_id": "npl015-stage-a", "opening_kind": "protected_access",
        "first_access_at": _at(reviewed_at, 5), "receipt_generation": 0,
        "supersedes_receipt_digest": None, "expected_run_ids": [], "observed_failure_ids": [], "retries": [],
    })
    opening_g0 = canonical.seal({
        "schema_id": "mmbu.phase1.opening_receipt_registry", "schema_version": 1,
        "registry_id": f"stage-a-structural-{source_id}-opening-g0", "generation": 0,
        "supersedes_registry_digest": None, "heads": [], "created_at": _at(reviewed_at, 3),
    })
    opening_g1 = canonical.seal({
        "schema_id": "mmbu.phase1.opening_receipt_registry", "schema_version": 1,
        "registry_id": f"stage-a-structural-{source_id}-opening-g1", "generation": 1,
        "supersedes_registry_digest": opening_g0["record_digest"],
        "heads": [{"lock_digest": lock["record_digest"], "opening_id": opening["opening_id"],
                   "head_receipt_digest": opening["record_digest"], "receipt_generation": 0}],
        "created_at": _at(reviewed_at, 5),
    })
    records = [*acquisition_records, execution_receipt, manifest, candidate, quarantined, split,
               attestation, purpose, registry, lock, opening, opening_g0, opening_g1]
    store = RecordStore(records)
    admission.check_source_artifact_manifest(store, manifest["record_digest"])
    admission.check_source(store, quarantined["record_digest"])
    admission.check_purpose_authorization(store, purpose["record_digest"])
    registries.check_authorization_registry_chain(store, registry["record_digest"])
    locks.validate_prospective_lock(lock)
    registries.check_opening_receipt_registry_chain(store, opening_g1["record_digest"])
    verify_inventory_opening(records, source_id, _at(reviewed_at, 6))
    return records


def inventory_archive_member_headers(
    archive_path: Path,
    records: list[dict],
    now: str,
    source_id: str,
) -> dict:
    """Read a ZIP central directory without opening any member payload."""
    opening = verify_inventory_opening(records, source_id, now)
    _require_protected_opening(opening, source_id)
    path = Path(archive_path)
    _require_manifest_artifact(path, opening)
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ValueError(f"{path.name} is not a valid ZIP archive") from None
    with archive:
        infos = archive.infolist()
        names = [row.filename for row in infos]
        if len(names) != len(set(names)):
            raise ValueError("archive contains duplicate member names")
        members = [{
            "name": row.filename,
            "compressed_bytes": row.compress_size,
            "uncompressed_bytes": row.file_size,
            "compression_method": row.compress_type,
            "crc32": f"{row.CRC:08x}",
            "is_directory": row.is_dir(),
        } for row in infos]
    return canonical.seal({
        "schema_id": "mmbu.phase1.archive_member_header_inventory",
        "schema_version": 1,
        "source_id": source_id,
        "artifact_name": path.name,
        "members": members,
        "member_count": len(members),
        "member_payloads_opened": False,
        "image_payload_decoding_used": False,
        "label_values_read": False,
        "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })


def inventory_csv_schema(path: Path) -> dict:
    """Read exactly one bounded CSV header row and no data row."""
    path = Path(path)
    with path.open("rb") as stream:
        first = stream.readline(65537)
    if not first or len(first) > 65536 or not first.endswith((b"\n", b"\r")):
        raise ValueError("CSV header is absent or exceeds the 64 KiB schema ceiling")
    try:
        columns = next(csv.reader(io.StringIO(first.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error, StopIteration):
        raise ValueError("CSV header is not valid UTF-8 CSV") from None
    if not columns or any(not column.strip() for column in columns):
        raise ValueError("CSV header contains an empty column name")
    return canonical.seal({
        "schema_id": "mmbu.phase1.csv_schema_inventory", "schema_version": 1,
        "artifact_name": path.name, "columns": columns,
        "header_bytes": len(first), "data_rows_read": 0,
        "label_values_read": False, "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })


def _safe_xml_member(archive: zipfile.ZipFile, name: str, maximum_bytes: int = 4 * 1024 * 1024) -> bytes:
    try:
        info = archive.getinfo(name)
    except KeyError:
        raise ValueError(f"XLSX is missing required member {name!r}") from None
    if info.file_size > maximum_bytes:
        raise ValueError(f"XLSX structural member {name!r} exceeds its schema ceiling")
    with archive.open(info) as stream:
        payload = stream.read(maximum_bytes + 1)
    if len(payload) > maximum_bytes or b"<!DOCTYPE" in payload or b"<!ENTITY" in payload:
        raise ValueError(f"XLSX structural member {name!r} is unsafe")
    return payload


def inventory_xlsx_schema(path: Path) -> dict:
    """Inspect workbook/sheet structure without resolving or emitting cell values."""
    path = Path(path)
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ValueError(f"{path.name} is not a valid XLSX/ZIP archive") from None
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    office_rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with archive:
        workbook = ET.fromstring(_safe_xml_member(archive, "xl/workbook.xml"))
        rels = ET.fromstring(_safe_xml_member(archive, "xl/_rels/workbook.xml.rels"))
        targets = {
            row.attrib["Id"]: row.attrib["Target"]
            for row in rels.findall(f"{{{rel_ns}}}Relationship")
            if "Id" in row.attrib and "Target" in row.attrib
        }
        sheets = []
        for sheet in workbook.findall(f".//{{{main_ns}}}sheet"):
            rel_id = sheet.attrib.get(office_rel)
            target = targets.get(rel_id or "")
            if target is None or target.startswith("/") or ".." in Path(target).parts:
                raise ValueError("XLSX sheet relationship is missing or unsafe")
            member = str(Path("xl") / target)
            try:
                info = archive.getinfo(member)
            except KeyError:
                raise ValueError(f"XLSX is missing required member {member!r}") from None
            if info.file_size > 64 * 1024 * 1024:
                raise ValueError("XLSX worksheet exceeds its structural-inspection ceiling")
            with archive.open(info) as probe:
                prefix = probe.read(4096)
            if b"<!DOCTYPE" in prefix or b"<!ENTITY" in prefix:
                raise ValueError("XLSX worksheet XML is unsafe")
            dimension_ref = None
            header_cells = []
            with archive.open(info) as stream:
                for event, element in ET.iterparse(stream, events=("start", "end")):
                    if event == "start" and element.tag == f"{{{main_ns}}}dimension":
                        dimension_ref = element.attrib.get("ref")
                    if event == "end" and element.tag == f"{{{main_ns}}}row":
                        header_cells = [
                            {"reference": cell.attrib.get("r", ""), "type": cell.attrib.get("t", "n")}
                            for cell in element.findall(f"{{{main_ns}}}c")
                        ]
                        break
            sheets.append({
                "name": sheet.attrib.get("name", ""), "sheet_id": sheet.attrib.get("sheetId", ""),
                "member": member, "dimension": dimension_ref,
                "header_cells": header_cells,
            })
    return canonical.seal({
        "schema_id": "mmbu.phase1.xlsx_schema_inventory", "schema_version": 1,
        "artifact_name": path.name, "sheets": sheets,
        "shared_string_values_resolved": False, "cell_values_emitted": False,
        "data_rows_read": 0, "label_values_read": False,
        "model_use_authorized": False, "mmbu_public_content_used": False,
    })


def inventory_pathmnist_structural(
    archive_path: Path,
    mapping_path: Path,
    records: list[dict],
    now: str,
    declaration: dict,
) -> dict:
    opening = verify_inventory_opening(records, "pathmnist-224", now)
    _require_manifest_artifact(Path(mapping_path), opening)
    return canonical.seal({
        "schema_id": "mmbu.phase1.pathmnist_structural_inventory", "schema_version": 1,
        "archive_headers": inventory_archive_member_headers(
            archive_path, records, now, "pathmnist-224"
        ),
        "array_headers": inventory_pathmnist_headers(archive_path, records, now, declaration),
        "mapping_schema": inventory_csv_schema(mapping_path),
        "test_member_payload_opened": False, "label_values_read": False,
        "image_payload_decoding_used": False, "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })


def inventory_busi_whu_structural(
    archive_path: Path,
    workbook_path: Path,
    records: list[dict],
    now: str,
) -> dict:
    opening = verify_inventory_opening(records, "busi-whu", now)
    _require_manifest_artifact(Path(workbook_path), opening)
    return canonical.seal({
        "schema_id": "mmbu.phase1.busi_whu_structural_inventory", "schema_version": 1,
        "archive_headers": inventory_archive_member_headers(archive_path, records, now, "busi-whu"),
        "workbook_schema": inventory_xlsx_schema(workbook_path),
        "label_values_read": False, "image_payload_decoding_used": False,
        "model_use_authorized": False, "mmbu_public_content_used": False,
    })


def validate_pathmnist_mapping(
    header: list[str], rows: list[dict], expected_counts: dict[str, int]
) -> dict:
    """Validate a decoded synthetic mapping against the frozen train/val shape.

    This function is deliberately pure.  It does not open the real mapping or
    any NPZ member; a later protected opening can feed rows through the same
    contract without changing its decision logic.
    """
    if header != ["split", "index", "image_id"]:
        raise ValueError("PathMNIST mapping header must be exactly split,index,image_id")
    if (
        not isinstance(expected_counts, dict)
        or set(expected_counts) != {"train", "val"}
        or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0
               for value in expected_counts.values())
    ):
        raise ValueError("expected_counts must contain positive integer train and val counts")
    if not isinstance(rows, list):
        raise ValueError("PathMNIST mapping rows must be a list")

    by_split: dict[str, dict[int, str]] = {"train": {}, "val": {}}
    image_ids: set[str] = set()
    for position, row in enumerate(rows):
        if not isinstance(row, dict) or list(row.keys()) != header:
            raise ValueError(f"mapping row {position} must preserve the exact closed schema")
        split = row["split"]
        raw_index = row["index"]
        image_id = row["image_id"]
        if split not in by_split:
            raise ValueError(f"mapping row {position} uses a forbidden split")
        if not isinstance(raw_index, str) or re.fullmatch(r"0|[1-9][0-9]*", raw_index) is None:
            raise ValueError(f"mapping row {position} has a non-canonical index")
        if not isinstance(image_id, str) or not image_id or image_id.strip() != image_id:
            raise ValueError(f"mapping row {position} has an invalid image_id")
        index = int(raw_index)
        if index in by_split[split]:
            raise ValueError(f"mapping contains duplicate {split} index {index}")
        if image_id in image_ids:
            raise ValueError(f"mapping contains duplicate image_id {image_id!r}")
        by_split[split][index] = image_id
        image_ids.add(image_id)

    records = []
    for split in ("train", "val"):
        expected = expected_counts[split]
        if sorted(by_split[split]) != list(range(expected)):
            raise ValueError(f"mapping {split} indices must be exactly contiguous 0..{expected - 1}")
        for index in range(expected):
            records.append({
                "record_id": f"pathmnist-224:{split}:{index}",
                "split": split,
                "index": index,
                "image_id": by_split[split][index],
            })
    return canonical.seal({
        "schema_id": "mmbu.phase1.pathmnist_mapping_validation",
        "schema_version": 1,
        "header": list(header),
        "split_counts": {"train": len(by_split["train"]), "val": len(by_split["val"])},
        "records": records,
        "test_split_used": False,
        "label_values_read": False,
        "image_payload_decoding_used": False,
        "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })


def read_pathmnist_mapping(
    path: Path,
    expected_counts: dict[str, int],
    *,
    maximum_bytes: int,
    maximum_rows: int,
) -> dict:
    """Read one bounded mapping file and pass it through the closed validator.

    Real execution remains gated by a separately acknowledged protected-opening
    packet.  This reader exists so that packet can bind already-tested code.
    """
    path = Path(path)
    if isinstance(maximum_bytes, bool) or not isinstance(maximum_bytes, int) or maximum_bytes <= 0:
        raise ValueError("maximum_bytes must be a positive integer")
    if isinstance(maximum_rows, bool) or not isinstance(maximum_rows, int) or maximum_rows <= 0:
        raise ValueError("maximum_rows must be a positive integer")
    size = path.stat().st_size
    if size <= 0 or size > maximum_bytes:
        raise ValueError("PathMNIST mapping exceeds its bounded byte ceiling")
    selected_rows: list[dict] = []
    source_rows_read = 0
    excluded_counts = {"test": 0}
    all_image_ids: set[str] = set()
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            header = reader.fieldnames
            if header != ["split", "index", "image_id"]:
                raise ValueError("PathMNIST mapping header must be exactly split,index,image_id")
            for row in reader:
                source_rows_read += 1
                if source_rows_read > maximum_rows:
                    raise ValueError("PathMNIST mapping exceeds its bounded row ceiling")
                if list(row) != header:
                    raise ValueError("PathMNIST mapping row differs from the closed schema")
                split, raw_index, image_id = row["split"], row["index"], row["image_id"]
                if split not in {"train", "val", "test"}:
                    raise ValueError("PathMNIST mapping contains an unknown split")
                if re.fullmatch(r"0|[1-9][0-9]*", raw_index or "") is None:
                    raise ValueError("PathMNIST mapping contains a non-canonical index")
                if not image_id or image_id.strip() != image_id or image_id in all_image_ids:
                    raise ValueError("PathMNIST mapping contains an invalid or duplicate image_id")
                all_image_ids.add(image_id)
                if split == "test":
                    excluded_counts["test"] += 1
                else:
                    selected_rows.append(row)
    except UnicodeDecodeError:
        raise ValueError("PathMNIST mapping is not valid UTF-8 CSV") from None
    validated = validate_pathmnist_mapping(header, selected_rows, expected_counts)
    payload = {key: value for key, value in validated.items() if key != "record_digest"}
    payload["source_rows_read"] = source_rows_read
    payload["source_bytes_read"] = size
    payload["excluded_split_counts"] = excluded_counts
    payload["excluded_rows_emitted"] = 0
    payload["test_mapping_rows_read"] = excluded_counts["test"] > 0
    return canonical.seal(payload)


def resolve_xlsx_header_strings(
    path: Path,
    sheet_name: str,
    expected_references: list[str],
    *,
    maximum_shared_strings_bytes: int = 4 * 1024 * 1024,
) -> dict:
    """Resolve only shared strings referenced by one workbook header row."""
    if not isinstance(sheet_name, str) or not sheet_name:
        raise ValueError("sheet_name must be nonempty")
    if (
        not isinstance(expected_references, list)
        or not expected_references
        or expected_references != sorted(set(expected_references))
        or any(re.fullmatch(r"[A-Z]{1,3}1", ref) is None for ref in expected_references)
    ):
        raise ValueError("expected_references must be sorted unique row-one cell references")
    if (
        isinstance(maximum_shared_strings_bytes, bool)
        or not isinstance(maximum_shared_strings_bytes, int)
        or maximum_shared_strings_bytes <= 0
    ):
        raise ValueError("maximum_shared_strings_bytes must be positive")
    path = Path(path)
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    office_rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ValueError(f"{path.name} is not a valid XLSX/ZIP archive") from None
    with archive:
        workbook = ET.fromstring(_safe_xml_member(archive, "xl/workbook.xml"))
        rels = ET.fromstring(_safe_xml_member(archive, "xl/_rels/workbook.xml.rels"))
        targets = {
            row.attrib["Id"]: row.attrib["Target"]
            for row in rels.findall(f"{{{rel_ns}}}Relationship")
            if "Id" in row.attrib and "Target" in row.attrib
        }
        matching = [row for row in workbook.findall(f".//{{{main_ns}}}sheet")
                    if row.attrib.get("name") == sheet_name]
        if len(matching) != 1:
            raise ValueError("XLSX must contain exactly one requested sheet")
        target = targets.get(matching[0].attrib.get(office_rel, ""))
        if target is None or target.startswith("/") or ".." in Path(target).parts:
            raise ValueError("XLSX sheet relationship is missing or unsafe")
        sheet_member = str(Path("xl") / target)
        try:
            sheet_info = archive.getinfo(sheet_member)
        except KeyError:
            raise ValueError(f"XLSX is missing required member {sheet_member!r}") from None
        if sheet_info.file_size > 64 * 1024 * 1024:
            raise ValueError("XLSX worksheet exceeds its header-resolution ceiling")

        header_indices: dict[str, int] = {}
        with archive.open(sheet_info) as stream:
            for event, element in ET.iterparse(stream, events=("end",)):
                if element.tag != f"{{{main_ns}}}row":
                    continue
                if element.attrib.get("r") != "1":
                    raise ValueError("XLSX first materialized row must be row 1")
                cells = element.findall(f"{{{main_ns}}}c")
                references = [cell.attrib.get("r", "") for cell in cells]
                if references != expected_references:
                    raise ValueError("XLSX header references differ from the frozen contract")
                for cell in cells:
                    if cell.attrib.get("t") != "s":
                        raise ValueError("XLSX header cells must use shared strings")
                    value = cell.find(f"{{{main_ns}}}v")
                    raw = value.text if value is not None else None
                    if raw is None or re.fullmatch(r"0|[1-9][0-9]*", raw) is None:
                        raise ValueError("XLSX header shared-string index is invalid")
                    header_indices[cell.attrib["r"]] = int(raw)
                break
        if set(header_indices) != set(expected_references):
            raise ValueError("XLSX header row was not found")

        try:
            shared_info = archive.getinfo("xl/sharedStrings.xml")
        except KeyError:
            raise ValueError("XLSX is missing sharedStrings.xml") from None
        if shared_info.file_size > maximum_shared_strings_bytes:
            raise ValueError("XLSX shared-string table exceeds its bounded byte ceiling")
        needed = set(header_indices.values())
        resolved: dict[int, str] = {}
        with archive.open(shared_info) as stream:
            for index, (_event, element) in enumerate(
                (item for item in ET.iterparse(stream, events=("end",))
                 if item[1].tag == f"{{{main_ns}}}si")
            ):
                if index in needed:
                    value = "".join(node.text or "" for node in element.iter(f"{{{main_ns}}}t"))
                    if not value or value.strip() != value:
                        raise ValueError("XLSX header string is empty or not canonical")
                    resolved[index] = value
                element.clear()
                if set(resolved) == needed:
                    break
        if set(resolved) != needed or len(set(resolved.values())) != len(resolved):
            raise ValueError("XLSX header strings are missing or duplicated")
    headers = [{"reference": ref, "value": resolved[header_indices[ref]]}
               for ref in expected_references]
    return canonical.seal({
        "schema_id": "mmbu.phase1.xlsx_header_string_inventory", "schema_version": 1,
        "artifact_name": path.name, "sheet_name": sheet_name, "headers": headers,
        "shared_string_entries_resolved": len(resolved), "data_rows_read": 0,
        "label_values_read": False, "image_payload_decoding_used": False,
        "model_use_authorized": False, "mmbu_public_content_used": False,
    })


def _xlsx_shared_strings(archive: zipfile.ZipFile, main_ns: str, maximum_bytes: int) -> list[str]:
    try:
        info = archive.getinfo("xl/sharedStrings.xml")
    except KeyError:
        raise ValueError("XLSX is missing sharedStrings.xml") from None
    if info.file_size > maximum_bytes:
        raise ValueError("XLSX shared-string table exceeds its bounded byte ceiling")
    values = []
    with archive.open(info) as stream:
        for _event, element in ET.iterparse(stream, events=("end",)):
            if element.tag != f"{{{main_ns}}}si":
                continue
            value = "".join(node.text or "" for node in element.iter(f"{{{main_ns}}}t"))
            if not value:
                raise ValueError("XLSX shared strings must be nonempty")
            values.append(value)
            element.clear()
    return values


def _xlsx_cell_value(cell: ET.Element, main_ns: str, shared: list[str]) -> str:
    if cell.find(f"{{{main_ns}}}f") is not None:
        raise ValueError("XLSX formulas are forbidden in the protected metadata join")
    kind = cell.attrib.get("t")
    if kind == "inlineStr":
        value = "".join(node.text or "" for node in cell.iter(f"{{{main_ns}}}t"))
    else:
        node = cell.find(f"{{{main_ns}}}v")
        value = node.text if node is not None else None
        if value is None:
            raise ValueError("XLSX data cells must contain a value")
        if kind == "s":
            if re.fullmatch(r"0|[1-9][0-9]*", value) is None:
                raise ValueError("XLSX shared-string index is invalid")
            index = int(value)
            if index >= len(shared):
                raise ValueError("XLSX shared-string index is out of range")
            value = shared[index]
        elif kind not in {None, "n", "str"}:
            raise ValueError(f"unsupported XLSX cell type: {kind!r}")
    if not value or value.strip() != value:
        raise ValueError("XLSX cell value is empty or not canonical")
    return value


def _integral_decimal(value: str, path: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        raise ValueError(f"{path} must be numeric") from None
    if not parsed.is_finite() or parsed != parsed.to_integral_value():
        raise ValueError(f"{path} must be a finite integer")
    result = int(parsed)
    if result < minimum or (maximum is not None and result > maximum):
        raise ValueError(f"{path} is outside the allowed range")
    return result


def _finite_decimal(value: str, path: str) -> None:
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        raise ValueError(f"{path} must be numeric") from None
    if not parsed.is_finite():
        raise ValueError(f"{path} must be finite")


def read_busi_whu_workbook_rows(
    path: Path,
    member_record_ids: list[str],
    *,
    maximum_rows: int = 2000,
    maximum_shared_strings_bytes: int = 4 * 1024 * 1024,
    maximum_sheet_bytes: int = 64 * 1024 * 1024,
    include_geometry: bool = False,
) -> dict:
    """Read the exact BUSI-WHU patient/image join without opening image payloads."""
    if (
        not isinstance(member_record_ids, list)
        or not member_record_ids
        or member_record_ids != sorted(set(member_record_ids))
        or any(re.fullmatch(r"[A-Za-z0-9_-]+", value) is None for value in member_record_ids)
    ):
        raise ValueError("member_record_ids must be a sorted unique closed identifier list")
    if isinstance(maximum_rows, bool) or not isinstance(maximum_rows, int) or maximum_rows <= 0:
        raise ValueError("maximum_rows must be positive")
    if type(include_geometry) is not bool:
        raise ValueError("include_geometry must be boolean")
    if len(member_record_ids) > maximum_rows:
        raise ValueError("member record population exceeds the bounded row ceiling")

    path = Path(path)
    main_ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    office_rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ValueError(f"{path.name} is not a valid XLSX/ZIP archive") from None
    with archive:
        workbook = ET.fromstring(_safe_xml_member(archive, "xl/workbook.xml"))
        rels = ET.fromstring(_safe_xml_member(archive, "xl/_rels/workbook.xml.rels"))
        sheets = workbook.findall(f".//{{{main_ns}}}sheet")
        if len(sheets) != 1 or sheets[0].attrib.get("name") != "Sheet1":
            raise ValueError("BUSI-WHU workbook must contain exactly Sheet1")
        targets = {
            row.attrib["Id"]: row.attrib["Target"]
            for row in rels.findall(f"{{{rel_ns}}}Relationship")
            if "Id" in row.attrib and "Target" in row.attrib
        }
        target = targets.get(sheets[0].attrib.get(office_rel, ""))
        if target is None or target.startswith("/") or ".." in Path(target).parts:
            raise ValueError("BUSI-WHU worksheet relationship is missing or unsafe")
        sheet_member = str(Path("xl") / target)
        try:
            sheet_info = archive.getinfo(sheet_member)
        except KeyError:
            raise ValueError("BUSI-WHU worksheet member is missing") from None
        if sheet_info.file_size > maximum_sheet_bytes:
            raise ValueError("BUSI-WHU worksheet exceeds its bounded byte ceiling")
        shared = _xlsx_shared_strings(archive, main_ns, maximum_shared_strings_bytes)
        expected_columns = list("ABCDEFGHIJKLM")
        rows: list[dict] = []
        observed_ids: set[str] = set()
        patients: set[str] = set()
        label_counts = {"0": 0, "1": 0}
        expected_row_number = 1
        with archive.open(sheet_info) as stream:
            for _event, element in ET.iterparse(stream, events=("end",)):
                if element.tag != f"{{{main_ns}}}row":
                    continue
                raw_row_number = element.attrib.get("r", "")
                if re.fullmatch(r"[1-9][0-9]*", raw_row_number) is None:
                    raise ValueError("BUSI-WHU workbook row number is invalid")
                row_number = int(raw_row_number)
                if row_number != expected_row_number:
                    raise ValueError("BUSI-WHU workbook rows must be contiguous")
                expected_row_number += 1
                if row_number > maximum_rows + 1:
                    raise ValueError("BUSI-WHU workbook exceeds the bounded row ceiling")
                cells = element.findall(f"{{{main_ns}}}c")
                references = [cell.attrib.get("r", "") for cell in cells]
                expected_references = [f"{column}{row_number}" for column in expected_columns]
                if references != expected_references:
                    raise ValueError("BUSI-WHU workbook row differs from the closed 13-column schema")
                values = [_xlsx_cell_value(cell, main_ns, shared) for cell in cells]
                if row_number == 1:
                    if tuple(values) != BUSI_WHU_HEADERS:
                        raise ValueError("BUSI-WHU workbook headers differ from the frozen contract")
                    element.clear()
                    continue

                patient = str(_integral_decimal(values[0], f"row {row_number} patient_index", minimum=1))
                label = str(_integral_decimal(values[1], f"row {row_number} label", maximum=1))
                raw_image = values[2]
                image_name = Path(raw_image).name
                if raw_image != image_name or image_name.lower().endswith(".bmp") is False:
                    raise ValueError("BUSI-WHU img_names must be exact BMP basenames")
                record_id = image_name[:-4]
                if re.fullmatch(r"[A-Za-z0-9_-]+", record_id) is None or record_id in observed_ids:
                    raise ValueError("BUSI-WHU image identifiers must be safe and unique")
                for column_index in (3, 5, 6, 7, 8, 9, 10, 11, 12):
                    _finite_decimal(values[column_index], f"row {row_number} column {column_index + 1}")
                row_value = dict(zip(BUSI_WHU_HEADERS, values))
                parsed_row = {
                    "record_id": record_id,
                    "parent_id": f"busi-whu:patient:{patient}",
                    "label_code": label,
                    "workbook_row": row_number,
                    "row_digest": canonical.value_digest(row_value),
                }
                if include_geometry:
                    parsed_row["workbook_geometry"] = {
                        "scale_pixel_per_cm": values[3], "scale_category": values[4],
                        "gt_area_pixel2": values[5], "image_area_pixel2": values[6],
                        "gt_cm2": values[7], "gt_all": values[8],
                        "centroid_x": values[9], "centroid_y": values[10],
                        "max_diameter": values[11], "min_diameter": values[12],
                    }
                rows.append(parsed_row)
                observed_ids.add(record_id)
                patients.add(patient)
                label_counts[label] += 1
                element.clear()
        if len(rows) != len(member_record_ids) or observed_ids != set(member_record_ids):
            raise ValueError("BUSI-WHU workbook and image/mask member identifiers do not form a bijection")
    rows.sort(key=lambda row: row["record_id"])
    return canonical.seal({
        "schema_id": "mmbu.phase1.busi_whu_patient_join_inventory", "schema_version": 1,
        "artifact_name": path.name, "sheet_name": "Sheet1", "records": rows,
        "record_count": len(rows), "patient_count": len(patients), "label_counts": label_counts,
        "image_member_join_complete": True, "annotation_member_join_complete": True,
        "label_values_read": True, "image_payload_decoding_used": False,
        "annotation_payload_decoding_used": False, "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })


def _closed_member_names(member_names: list[str], directories: set[str]) -> list[str]:
    if not isinstance(member_names, list) or any(not isinstance(name, str) or not name for name in member_names):
        raise ValueError("archive member names must be a nonempty string list")
    if len(member_names) != len(set(member_names)):
        raise ValueError("archive contains duplicate member names")
    for name in member_names:
        parts = name.replace("\\", "/").split("/")
        if name.startswith(("/", "\\")) or "\\" in name or ".." in parts or "." in parts:
            raise ValueError(f"archive member path is unsafe: {name!r}")
        if name.endswith("/") and name not in directories:
            raise ValueError(f"archive contains an unknown directory: {name!r}")
    if not directories.issubset(set(member_names)):
        raise ValueError("archive is missing a required directory entry")
    return member_names


def pair_busbra_members(member_names: list[str]) -> dict:
    """Prove the BUS-BRA image/mask bijection from names only."""
    directories = {"BUSBRA/", "BUSBRA/Images/", "BUSBRA/Masks/"}
    known_files = {
        "BUSBRA/LICENSE.txt", "BUSBRA/bus_data.csv",
        "BUSBRA/5-fold-cv.csv", "BUSBRA/10-fold-cv.csv",
    }
    names = _closed_member_names(member_names, directories)
    if not known_files.issubset(set(names)):
        raise ValueError("BUS-BRA archive is missing required structural metadata")
    images: dict[str, str] = {}
    masks: dict[str, str] = {}
    image_pattern = re.compile(r"BUSBRA/Images/(bus_[0-9]{4}-(?:l|r|s))\.png")
    mask_pattern = re.compile(r"BUSBRA/Masks/mask_([0-9]{4}-(?:l|r|s))\.png")
    for name in names:
        if name in directories or name in known_files:
            continue
        image = image_pattern.fullmatch(name)
        mask = mask_pattern.fullmatch(name)
        if image:
            images[image.group(1)] = name
        elif mask:
            masks[f"bus_{mask.group(1)}"] = name
        else:
            raise ValueError(f"BUS-BRA archive contains an unknown member: {name!r}")
    if set(images) != set(masks) or not images:
        raise ValueError("BUS-BRA image and mask members must form a nonempty bijection")
    pairs = [{"record_id": key, "image_member": images[key], "mask_member": masks[key]}
             for key in sorted(images)]
    return canonical.seal({
        "schema_id": "mmbu.phase1.busbra_member_pairing", "schema_version": 1,
        "pairs": pairs, "pair_count": len(pairs), "member_payloads_opened": False,
        "label_values_read": False, "image_payload_decoding_used": False,
        "model_use_authorized": False, "mmbu_public_content_used": False,
    })


def pair_busi_whu_members(member_names: list[str]) -> dict:
    """Prove the BUSI-WHU image/annotation bijection from names only."""
    directories = {"img/", "gt/"}
    names = _closed_member_names(member_names, directories)
    images: dict[str, str] = {}
    annotations: dict[str, str] = {}
    image_pattern = re.compile(r"img/([A-Za-z0-9_-]+)\.bmp")
    annotation_pattern = re.compile(r"gt/([A-Za-z0-9_-]+)_anno\.bmp")
    for name in names:
        if name in directories:
            continue
        image = image_pattern.fullmatch(name)
        annotation = annotation_pattern.fullmatch(name)
        if image:
            images[image.group(1)] = name
        elif annotation:
            annotations[annotation.group(1)] = name
        else:
            raise ValueError(f"BUSI-WHU archive contains an unknown member: {name!r}")
    if set(images) != set(annotations) or not images:
        raise ValueError("BUSI-WHU image and annotation members must form a nonempty bijection")
    pairs = [{"record_id": key, "image_member": images[key], "annotation_member": annotations[key]}
             for key in sorted(images)]
    return canonical.seal({
        "schema_id": "mmbu.phase1.busi_whu_member_pairing", "schema_version": 1,
        "pairs": pairs, "pair_count": len(pairs), "member_payloads_opened": False,
        "label_values_read": False, "image_payload_decoding_used": False,
        "model_use_authorized": False, "mmbu_public_content_used": False,
    })


def inventory_pathmnist_headers(
    archive_path: Path,
    records: list[dict],
    now: str,
    declaration: dict,
) -> dict:
    """Inspect only allowlisted PathMNIST train/val NPY headers.

    ZIP central-directory names are visible, but forbidden test members are
    never opened.  This is a structural pre-inventory and emits no labels,
    rows, or model-use authority.
    """
    from mmbu_phase1.biomedical_sources import ContractViolation, _npy_header

    declaration = _closed(declaration, SOURCE_KEYS, "pathmnist_declaration")
    if (
        declaration["source_id"] != "pathmnist-224"
        or declaration["role"] != "training"
        or declaration["proposed_purposes"] != ["release", "train"]
        or declaration["population"]["allowed_splits"] != ["train", "val"]
        or declaration["population"]["forbidden_member_prefixes"] != ["test_"]
    ):
        raise ValueError("PathMNIST declaration differs from the protected train/val contract")
    opening_evidence = verify_inventory_opening(records, "pathmnist-224", now)
    _require_protected_opening(opening_evidence, "pathmnist-224")
    path = Path(archive_path)
    if not path.is_file() or path.name != "pathmnist_224.npz":
        raise ValueError("PathMNIST archive must be the exact declared basename")
    _require_manifest_artifact(path, opening_evidence)
    expected = {f"{split}_{kind}.npy" for split in ("train", "val", "test") for kind in ("images", "labels")}
    allowed = {f"{split}_{kind}.npy" for split in ("train", "val") for kind in ("images", "labels")}
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ValueError("PathMNIST artifact is not a valid NPZ/ZIP archive") from None
    opened = []
    with archive:
        names = [item.filename for item in archive.infolist()]
        if len(names) != len(set(names)) or set(names) != expected:
            raise ValueError("PathMNIST archive must contain exactly the six official array members")
        for member in sorted(allowed):
            try:
                with archive.open(member) as stream:
                    dtype, shape, header_bytes = _npy_header(stream, f"pathmnist.{member}")
            except ContractViolation as exc:
                raise ValueError(str(exc)) from None
            opened.append({"member": member, "dtype": dtype, "shape": list(shape), "header_bytes": header_bytes})
    return {
        "schema_id": "mmbu.phase1.pathmnist_header_inventory",
        "schema_version": 1,
        "opened_members": opened,
        "unopened_forbidden_members": sorted(expected - allowed),
        "test_payload_opened": False,
        "model_use_authorized": False,
        "mmbu_public_content_used": False,
    }


def _require_protected_opening(opening_evidence: dict, source_id: str) -> None:
    opening = opening_evidence.get("opening", {})
    manifest = opening_evidence.get("manifest", {})
    source = opening_evidence.get("source", {})
    if (
        source.get("source_id") != source_id
        or manifest.get("source_id") != source_id
        or source.get("status") != "quarantined"
        or opening.get("opening_kind") != "protected_access"
        or opening.get("manifest_digests") != [manifest.get("record_digest")]
    ):
        raise ValueError("a verified exact protected opening is required before source access")


def _require_manifest_artifact(path: Path, opening_evidence: dict) -> dict:
    """Bind the exact local bytes to the protected manifest before opening them."""
    matches = [
        row for row in opening_evidence["manifest"]["artifacts"]
        if Path(row["logical_path"]).name == path.name
    ]
    if len(matches) != 1:
        raise ValueError("protected manifest must contain exactly one matching artifact basename")
    artifact = matches[0]
    digest = hashlib.sha256()
    observed_bytes = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            observed_bytes += len(chunk)
            digest.update(chunk)
    if observed_bytes != artifact["bytes"] or digest.hexdigest() != artifact["sha256"]:
        raise ValueError("local artifact bytes differ from the protected manifest")
    return artifact


def inventory_busbra(
    archive_path: Path,
    records: list[dict],
    now: str,
    declaration: dict,
) -> dict:
    """Compile BUS-BRA structurally, but admit only the frozen training population."""
    from mmbu_phase1.biomedical_sources import ContractViolation, compile_busbra

    opening_evidence = verify_inventory_opening(records, "bus-bra", now)
    _require_protected_opening(opening_evidence, "bus-bra")
    _require_manifest_artifact(Path(archive_path), opening_evidence)
    try:
        compiled = compile_busbra(archive_path, declaration)
    except ContractViolation as exc:
        raise ValueError(str(exc)) from None
    records = []
    eligible_parents = set()
    for row in compiled["rows"]:
        eligible = row["split"] == "train"
        if eligible:
            eligible_parents.add(row["independent_unit_id"])
        records.append({
            "record_id": row["row_id"],
            "parent_id": row["independent_unit_id"],
            "source_split": row["split"],
            "disposition": "eligible" if eligible else "excluded",
            "exclusion_reason_code": None if eligible else "outside_frozen_training_population",
            "row_digest": canonical.value_digest(row),
        })
    return canonical.seal({
        "schema_id": "mmbu.phase1.busbra_structural_inventory",
        "schema_version": 1,
        "source_receipt_digest": canonical.value_digest(compiled["receipt"]),
        "records": records,
        "eligible_record_count": sum(row["disposition"] == "eligible" for row in records),
        "eligible_parent_count": len(eligible_parents),
        "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })
__all__ = [
    "acquisition_command_digest",
    "acquisition_method_digest",
    "acquire_artifacts_once",
    "build_acquisition_packet",
    "build_structural_opening_packet",
    "build_structural_opening_records",
    "stage_a_acquisition_authority_subject",
    "stage_a_structural_authority_subject",
    "load_stage_a_config",
    "validate_acquisition_packet",
    "validate_structural_opening_packet",
    "validate_stage_a_config",
    "verify_inventory_opening",
    "inventory_pathmnist_headers",
    "inventory_pathmnist_structural",
    "inventory_busbra",
    "inventory_archive_member_headers",
    "inventory_csv_schema",
    "inventory_xlsx_schema",
    "inventory_busi_whu_structural",
    "pair_busbra_members",
    "pair_busi_whu_members",
    "read_pathmnist_mapping",
    "resolve_xlsx_header_strings",
    "read_busi_whu_workbook_rows",
    "validate_pathmnist_mapping",
    "verify_acquisition_authority",
]
