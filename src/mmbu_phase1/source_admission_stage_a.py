"""Closed declarations for the Stage A real-source custody sequence.

This module validates identity and intent only.  It grants no source purpose,
does not open a biomedical payload, and performs no network access.
"""

from __future__ import annotations

import json
import hashlib
import re
import zipfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from mmbu_phase1 import canonical
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
            "expected_bytes": 55465,
            "sha256": None,
            "upstream_checksum": None,
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
    "build_acquisition_packet",
    "load_stage_a_config",
    "validate_acquisition_packet",
    "validate_stage_a_config",
    "verify_inventory_opening",
    "inventory_pathmnist_headers",
    "inventory_busbra",
]
