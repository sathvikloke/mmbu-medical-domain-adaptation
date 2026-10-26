"""Closed synthetic tests for the real-source Stage A declaration."""

from __future__ import annotations

import copy
import hashlib
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path

from mmbu_phase1 import canonical
from mmbu_phase1.source_admission_stage_a import (
    build_acquisition_packet,
    build_structural_opening_packet,
    load_stage_a_config,
    validate_acquisition_packet,
    validate_structural_opening_packet,
    validate_stage_a_config,
    verify_inventory_opening,
    inventory_pathmnist_headers,
    inventory_busbra,
    acquisition_command_digest,
    acquisition_method_digest,
    verify_acquisition_authority,
    acquire_artifacts_once,
)
from tests.phase1.admission_fixtures import AdmissionWorld
from tests.phase1.test_biomedical_sources import _build_archive as _build_busbra_archive
from tests.phase1.test_biomedical_sources import _declaration as _busbra_declaration


REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / "config/phase1/source-admission-stage-a.json"


class StageAConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def rejects(self, mutate) -> None:
        candidate = copy.deepcopy(self.config)
        mutate(candidate)
        with self.assertRaises(ValueError):
            validate_stage_a_config(candidate)

    def test_frozen_source_identities_and_roles(self):
        validated = load_stage_a_config(CONFIG)
        self.assertEqual(set(validated["sources"]), {"bus-bra", "pathmnist-224", "busi-whu"})
        self.assertEqual(
            validated["python_executable"],
            "/storage/groups/rrg_shared/hpc/Research/Code/mylibs/anaconda3/bin/python3",
        )
        self.assertEqual(validated["work_margin_bytes"], 20 * 1024**3)
        self.assertEqual(validated["sources"]["bus-bra"]["proposed_purposes"], ["release", "train"])
        self.assertEqual(validated["sources"]["pathmnist-224"]["proposed_purposes"], ["release", "train"])
        self.assertEqual(validated["sources"]["busi-whu"]["proposed_purposes"], ["confirmation", "release"])
        mapping = validated["sources"]["pathmnist-224"]["artifacts"][1]
        self.assertEqual(mapping["expected_bytes"], 2785821)
        self.assertEqual(
            mapping["sha256"],
            "ba6f166b2deae125086ecb7ff84223daa90bf35a7c95053be4f030be1a4ac0bb",
        )
        busi = {row["name"]: row for row in validated["sources"]["busi-whu"]["artifacts"]}
        self.assertEqual(busi["BUSI-WHU.zip"]["expected_bytes"], 128106790)
        self.assertEqual(
            busi["BUSI-WHU.zip"]["sha256"],
            "5d10c0bb931666e9cff48db9161febc0ec0c74e4b611c2edcbb9726f6d9d74cc",
        )
        self.assertEqual(busi["Patient_infos_BUSI-WHU.xlsx"]["expected_bytes"], 92017)
        self.assertEqual(
            busi["Patient_infos_BUSI-WHU.xlsx"]["sha256"],
            "14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44",
        )

    def test_duplicate_contract_is_exact(self):
        duplicate = validate_stage_a_config(self.config)["duplicate_method"]
        self.assertEqual(duplicate["perceptual_hash"], "dhash64")
        self.assertEqual(duplicate["maximum_hamming_distance"], 4)
        self.assertEqual(duplicate["maximum_aspect_ratio_delta"], 0.05)
        self.assertEqual(duplicate["missing_parent_policy"], "reject_record")

    def test_unknown_key_rejects(self):
        self.rejects(lambda value: value.update({"surprise": True}))

    def test_unmeasured_python_path_rejects(self):
        self.rejects(lambda value: value.update({"python_executable": "/usr/bin/python3"}))

    def test_glob_artifact_name_rejects(self):
        self.rejects(lambda value: value["sources"]["bus-bra"]["artifacts"][0].update({"name": "BUS*.zip"}))

    def test_duplicate_artifact_name_rejects(self):
        self.rejects(
            lambda value: value["sources"]["busi-whu"]["artifacts"].append(
                copy.deepcopy(value["sources"]["busi-whu"]["artifacts"][0])
            )
        )

    def test_unlisted_download_host_rejects(self):
        self.rejects(
            lambda value: value["sources"]["bus-bra"]["artifacts"][0].update(
                {"url": "https://unlisted.invalid/BUSBRA.zip"}
            )
        )

    def test_non_https_locator_rejects(self):
        self.rejects(lambda value: value["sources"]["bus-bra"]["canonical_locators"].__setitem__(0, "http://x.test"))

    def test_release_review_cannot_be_omitted(self):
        self.rejects(lambda value: value["sources"]["bus-bra"].update({"proposed_purposes": ["train"]}))

    def test_pathmnist_test_population_rejects(self):
        self.rejects(
            lambda value: value["sources"]["pathmnist-224"]["population"].update(
                {"allowed_splits": ["test", "train", "val"]}
            )
        )

    def test_mutated_frozen_artifact_identity_rejects(self):
        mutations = (
            lambda value: value["sources"]["bus-bra"]["artifacts"][0]["upstream_checksum"].update({"value": "0" * 32}),
            lambda value: value["sources"]["pathmnist-224"]["artifacts"][0].update({"expected_bytes": 1}),
            lambda value: value["sources"]["pathmnist-224"]["artifacts"][1].update({"official_file_id": "other"}),
            lambda value: value["sources"]["busi-whu"]["artifacts"][0].update({"sha256": "0" * 64}),
            lambda value: value["sources"]["busi-whu"]["artifacts"][1].update({"expected_bytes": 1}),
        )
        for mutate in mutations:
            with self.subTest(mutation=repr(mutate)):
                self.rejects(mutate)


class StageAPacketTests(unittest.TestCase):
    def setUp(self):
        self.config = load_stage_a_config(CONFIG)
        self.commit = "a" * 40
        self.launch_id = "20261025T183000Z-123e4567-e89b-42d3-a456-426614174000"
        self.run_root = f"/storage/scr/npl015/mmbu-admission/{self.launch_id}"
        self.created_at = "2026-10-25T18:30:00Z"
        self.packet = build_acquisition_packet(
            self.config, self.commit, self.launch_id, self.run_root, self.created_at
        )

    def changed_digest(self, mutate) -> None:
        candidate = copy.deepcopy(self.packet)
        mutate(candidate)
        candidate["record_digest"] = canonical.value_digest(
            {key: value for key, value in candidate.items() if key != "record_digest"}
        )
        self.assertNotEqual(candidate["record_digest"], self.packet["record_digest"])

    def test_packet_is_deterministic_and_binds_exact_launch(self):
        again = build_acquisition_packet(
            self.config, self.commit, self.launch_id, self.run_root, self.created_at
        )
        self.assertEqual(canonical.dumps(self.packet), canonical.dumps(again))
        self.assertEqual(self.packet["repository_commit"], self.commit)
        self.assertEqual(self.packet["launch_id"], self.launch_id)
        self.assertEqual(self.packet["run_root"], self.run_root)
        self.assertEqual(self.packet["config_digest"], canonical.value_digest(self.config))
        self.assertEqual(
            self.packet["forbidden_operations"],
            ["gpu_use", "mmbu_public_access", "model_loading", "retry_or_resume", "training", "upload_or_submit"],
        )
        validate_acquisition_packet(self.packet, self.config)

    def test_packet_binds_per_source_command_and_identity(self):
        for source_id, source in self.packet["sources"].items():
            command = source["retrieval_command"]
            self.assertEqual(
                command[0],
                "/storage/groups/rrg_shared/hpc/Research/Code/mylibs/anaconda3/bin/python3",
            )
            self.assertIn(f"{self.run_root}/repo/tools/source_admission_stage_a.py", command)
            self.assertEqual(command[-2:], ["--source-id", source_id])
            self.assertNotIn("--retry", command)
            self.assertNotIn("--continue-at", command)
            self.assertEqual(source["maximum_bytes"], self.config["sources"][source_id]["maximum_bytes"])
            self.assertEqual(
                [artifact["name"] for artifact in source["artifacts"]],
                [artifact["name"] for artifact in self.config["sources"][source_id]["artifacts"]],
            )

    def test_changed_command_rejects(self):
        self.changed_digest(lambda value: value["sources"]["bus-bra"]["retrieval_command"].append("--retry"))

    def test_changed_root_rejects(self):
        self.changed_digest(lambda value: value.update({"run_root": self.run_root + "-other"}))

    def test_changed_cap_rejects(self):
        self.changed_digest(lambda value: value["sources"]["bus-bra"].update({"maximum_bytes": 1}))

    def test_changed_purpose_rejects(self):
        self.changed_digest(lambda value: value["sources"]["bus-bra"].update({"proposed_purposes": ["train"]}))

    def test_changed_artifact_identity_rejects(self):
        self.changed_digest(lambda value: value["sources"]["busi-whu"]["artifacts"][0].update({"expected_bytes": 1}))

    def test_changed_repository_commit_rejects(self):
        self.changed_digest(lambda value: value.update({"repository_commit": "b" * 40}))

    def test_packet_file_has_distinct_full_file_sha256(self):
        payload = canonical.dumps(self.packet)
        self.assertEqual(len(hashlib.sha256(payload).hexdigest()), 64)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "packet.json"
            path.write_bytes(payload)
            self.assertEqual(path.read_bytes(), payload)


class StageACustodyTests(unittest.TestCase):
    def setUp(self):
        self.world = AdmissionWorld()
        self.records = list(self.world.records.values())

    def test_complete_chain_allows_only_inventory_opening(self):
        result = verify_inventory_opening(self.records, "syn-src", "2026-10-16T08:10:30Z")
        self.assertEqual(result["source"]["status"], "quarantined")
        self.assertEqual(result["split"]["role"], "quarantine")
        self.assertEqual(result["authorization"]["purpose"], "quarantine_inspection")
        self.assertEqual(result["opening"]["opening_kind"], "protected_access")
        self.assertEqual(result["manifest"]["source_id"], "syn-src")

    def test_missing_manifest_rejects(self):
        records = [row for row in self.records if row["schema_id"] != "mmbu.phase1.source_artifact_manifest"]
        with self.assertRaises(ValueError):
            verify_inventory_opening(records, "syn-src", "2026-10-16T08:10:30Z")

    def test_stale_opening_registry_rejects(self):
        records = [row for row in self.records if row.get("generation") != 1 or row["schema_id"] != "mmbu.phase1.opening_receipt_registry"]
        with self.assertRaises(ValueError):
            verify_inventory_opening(records, "syn-src", "2026-10-16T08:10:30Z")

    def test_wrong_source_rejects(self):
        with self.assertRaises(ValueError):
            verify_inventory_opening(self.records, "other-source", "2026-10-16T08:10:30Z")

    def test_opening_after_authorization_expiry_rejects(self):
        with self.assertRaises(ValueError):
            verify_inventory_opening(self.records, "syn-src", "2028-10-16T08:10:30Z")


class StageAAcquisitionAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.config = load_stage_a_config(CONFIG)
        self.launch_id = "20261025T183000Z-123e4567-e89b-42d3-a456-426614174000"
        self.run_root = f"/storage/scr/npl015/mmbu-admission/{self.launch_id}"
        self.packet = build_acquisition_packet(
            self.config, "a" * 40, self.launch_id, self.run_root, "2026-10-25T18:30:00Z"
        )
        source = self.packet["sources"]["bus-bra"]

        def bind(record, _world):
            record.update({
                "allowed_artifact_names": ["BUSBRA.zip"],
                "maximum_bytes": source["maximum_bytes"],
                "network_host_allowlist": ["zenodo.org"],
                "operator_id": "stage-a-operator",
                "retrieval_command_digest": acquisition_command_digest(source),
                "retrieval_method_digest": acquisition_method_digest(source),
                "staging_destination": source["staging_destination"],
            })

        world = AdmissionWorld(
            overrides={"acquisition": bind},
            source_id="bus-bra",
            version="1.0",
            family="bus-bra",
        )
        self.records = list(world.records.values())

    def test_exact_active_authority_passes(self):
        result = verify_acquisition_authority(
            self.records, self.packet, self.config, "bus-bra", "2026-10-25T18:31:00Z"
        )
        self.assertEqual(result["authorization"]["operator_id"], "stage-a-operator")
        self.assertEqual(result["source"]["retrieval_command"], self.packet["sources"]["bus-bra"]["retrieval_command"])

    def test_command_or_registry_substitution_rejects(self):
        changed = copy.deepcopy(self.packet)
        changed["sources"]["bus-bra"]["retrieval_command"].append("--retry")
        changed["record_digest"] = canonical.value_digest(
            {key: value for key, value in changed.items() if key != "record_digest"}
        )
        with self.assertRaises(ValueError):
            verify_acquisition_authority(
                self.records, changed, self.config, "bus-bra", "2026-10-25T18:31:00Z"
            )
        without_registry = [
            row for row in self.records if row["schema_id"] != "mmbu.phase1.authorization_registry"
        ]
        with self.assertRaises(ValueError):
            verify_acquisition_authority(
                without_registry, self.packet, self.config, "bus-bra", "2026-10-25T18:31:00Z"
            )


class StageAStructuralOpeningPacketTests(unittest.TestCase):
    def setUp(self):
        self.config = load_stage_a_config(CONFIG)
        launch_id = "20261025T200000Z-123e4567-e89b-42d3-a456-426614174000"
        self.acquisition_packet = build_acquisition_packet(
            self.config,
            "a" * 40,
            launch_id,
            f"/storage/scr/npl015/mmbu-admission/{launch_id}",
            "2026-10-25T20:00:00Z",
        )
        self.evidence = {}
        for source_id, declaration in self.config["sources"].items():
            packet_source = self.acquisition_packet["sources"][source_id]
            artifacts = [{
                "logical_path": row["name"],
                "bytes": row["expected_bytes"],
                "sha256": row["sha256"] or ("f" * 64),
            } for row in declaration["artifacts"]]

            def bind_acquisition(record, _world, source=packet_source):
                record.update({
                    "allowed_artifact_names": sorted(row["name"] for row in source["artifacts"]),
                    "maximum_bytes": source["maximum_bytes"],
                    "network_host_allowlist": sorted({
                        host for row in source["artifacts"] for host in row["allowed_hosts"]
                    }),
                    "operator_id": "stage-a-operator",
                    "retrieval_command_digest": acquisition_command_digest(source),
                    "retrieval_method_digest": acquisition_method_digest(source),
                    "staging_destination": source["staging_destination"],
                })

            def bind_receipt(record, world, source=packet_source):
                record.update({
                    "acquisition_authorization_digest": world.digest("acquisition"),
                    "authorization_registry_digest": world.digest("registry_g1"),
                    "executed_command_digest": acquisition_command_digest(source),
                    "executed_method_digest": acquisition_method_digest(source),
                    "observed_hosts": sorted({
                        host for row in source["artifacts"] for host in row["allowed_hosts"]
                    }),
                    "operator_id": "stage-a-operator",
                    "staging_destination": source["staging_destination"],
                })

            world = AdmissionWorld(
                overrides={"acquisition": bind_acquisition, "receipt": bind_receipt},
                proposed=declaration["proposed_purposes"],
                source_id=source_id,
                version=declaration["source_version"],
                family=declaration["source_family"],
                artifacts=artifacts,
            )
            self.evidence[source_id] = {
                "packet": self.acquisition_packet,
                "authority_records": [
                    world.get("registry_g0"),
                    world.get("acquisition_attestation"),
                    world.get("acquisition"),
                    world.get("registry_g1"),
                ],
                "execution_receipt": world.get("receipt"),
            }

    def packet(self):
        return build_structural_opening_packet(
            self.config,
            self.evidence,
            "b" * 40,
            "20261025T210000Z-123e4567-e89b-42d3-a456-426614174001",
            "/storage/scr/npl015/mmbu-admission/20261025T210000Z-123e4567-e89b-42d3-a456-426614174001",
            "2026-10-25T21:00:00Z",
        )

    def test_packet_binds_all_receipts_and_only_structural_reads(self):
        packet = self.packet()
        self.assertEqual(set(packet["sources"]), {"bus-bra", "pathmnist-224", "busi-whu"})
        self.assertEqual(packet["sources"]["bus-bra"]["permitted_reads"], ["archive_member_headers"])
        self.assertEqual(packet["sources"]["pathmnist-224"]["permitted_reads"], [
            "archive_member_headers", "mapping_schema", "train_val_array_headers",
        ])
        self.assertEqual(packet["sources"]["busi-whu"]["permitted_reads"], [
            "archive_member_headers", "workbook_schema",
        ])
        for source_id, source in packet["sources"].items():
            self.assertEqual(
                source["acquisition_execution_receipt_digest"],
                self.evidence[source_id]["execution_receipt"]["record_digest"],
            )
        self.assertFalse(packet["image_payload_decoding_allowed"])
        self.assertFalse(packet["model_use_authorized"])
        self.assertFalse(packet["mmbu_public_content_used"])

    def test_missing_source_or_changed_receipt_rejects(self):
        missing = copy.deepcopy(self.evidence)
        missing.pop("busi-whu")
        with self.assertRaises(ValueError):
            build_structural_opening_packet(
                self.config, missing, "b" * 40,
                "20261025T210000Z-123e4567-e89b-42d3-a456-426614174001",
                "/storage/scr/npl015/mmbu-admission/20261025T210000Z-123e4567-e89b-42d3-a456-426614174001",
                "2026-10-25T21:00:00Z",
            )
        changed = self.packet()
        changed["sources"]["pathmnist-224"]["acquisition_execution_receipt_digest"] = "0" * 64
        changed["record_digest"] = canonical.value_digest(
            {key: value for key, value in changed.items() if key != "record_digest"}
        )
        with self.assertRaises(ValueError):
            validate_structural_opening_packet(changed, self.config, self.evidence)

    def test_unchanged_source_from_authenticated_historical_packet_is_accepted(self):
        evidence = copy.deepcopy(self.evidence)
        historical = copy.deepcopy(evidence["bus-bra"]["packet"])
        evidence["bus-bra"]["packet"] = historical
        historical["sources"]["pathmnist-224"]["artifacts"][1]["expected_bytes"] = 55465
        historical["config_digest"] = "1" * 64
        historical["record_digest"] = canonical.value_digest(
            {key: value for key, value in historical.items() if key != "record_digest"}
        )
        packet = build_structural_opening_packet(
            self.config,
            evidence,
            "b" * 40,
            "20261025T210000Z-123e4567-e89b-42d3-a456-426614174001",
            "/storage/scr/npl015/mmbu-admission/20261025T210000Z-123e4567-e89b-42d3-a456-426614174001",
            "2026-10-25T21:00:00Z",
        )
        self.assertEqual(
            packet["sources"]["bus-bra"]["acquisition_packet_digest"],
            historical["record_digest"],
        )

class _Response:
    def __init__(self, payload: bytes, url: str):
        self.payload = payload
        self.url = url
        self.offset = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return self.url

    def read(self, size: int):
        chunk = self.payload[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk


class StageATransportTests(unittest.TestCase):
    def source(self, payload: bytes, *, checksum: str | None = None) -> dict:
        return {
            "maximum_bytes": 100,
            "artifacts": [{
                "name": "source.zip",
                "url": "https://official.test/source.zip",
                "expected_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "upstream_checksum": {
                    "algorithm": "md5",
                    "value": checksum or hashlib.md5(payload).hexdigest(),  # nosec: synthetic upstream checksum
                },
                "media_type": "application/zip",
                "role": "archive",
                "official_file_id": "source.zip",
                "allowed_hosts": ["official.test"],
            }],
        }

    def test_one_attempt_publishes_without_partial_or_overwrite(self):
        payload = b"synthetic-source"
        calls = []

        def open_url(url):
            calls.append(url)
            return _Response(payload, url)

        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "new-source"
            result = acquire_artifacts_once(self.source(payload), destination, open_url)
            self.assertEqual((destination / "source.zip").read_bytes(), payload)
            self.assertFalse((destination / "source.zip.partial").exists())
        self.assertEqual(calls, ["https://official.test/source.zip"])
        self.assertEqual(result["observed_hosts"], ["official.test"])
        self.assertEqual(result["observed_artifacts"][0]["bytes"], len(payload))

    def test_checksum_failure_preserves_partial_and_never_retries(self):
        payload = b"synthetic-source"
        calls = []

        def open_url(url):
            calls.append(url)
            return _Response(payload, url)

        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "new-source"
            with self.assertRaises(ValueError):
                acquire_artifacts_once(self.source(payload, checksum="0" * 32), destination, open_url)
            self.assertEqual((destination / "source.zip.partial").read_bytes(), payload)
            self.assertFalse((destination / "source.zip").exists())
        self.assertEqual(len(calls), 1)

    def test_existing_destination_blocks_before_network(self):
        calls = []
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "existing"
            destination.mkdir()
            with self.assertRaises(FileExistsError):
                acquire_artifacts_once(
                    self.source(b"x"), destination, lambda url: calls.append(url)
                )
        self.assertEqual(calls, [])


class StageALauncherTests(unittest.TestCase):
    def test_launcher_is_cpu_only_one_shot_and_uses_sealed_inputs(self):
        text = (REPO / "tools/source_admission_stage_a.sbatch").read_text(encoding="utf-8")
        self.assertIn("#SBATCH --partition=epyc-cpu", text)
        self.assertIn("#SBATCH --array=0-2%3", text)
        self.assertIn("#SBATCH --cpus-per-task=1", text)
        self.assertIn("#SBATCH --no-requeue", text)
        self.assertNotIn("--gres", text)
        self.assertNotIn("--gpus", text)
        self.assertNotIn("--retry", text)
        self.assertNotIn("--continue-at", text)
        self.assertNotIn("while ", text)
        self.assertNotIn("for ", text)
        self.assertIn("source_ids=(bus-bra pathmnist-224 busi-whu)", text)
        self.assertIn("acquisition-packet.json", text)
        self.assertIn("acquisition-authority.json", text)
        self.assertIn("exec \"${STAGE_A_PYTHON}\"", text)


def _npy_bytes(descr: str, shape: tuple[int, ...], payload: bytes) -> bytes:
    header = repr({"descr": descr, "fortran_order": False, "shape": shape})
    prefix = b"\x93NUMPY\x01\x00"
    padding = (16 - ((len(prefix) + 2 + len(header) + 1) % 16)) % 16
    encoded = (header + " " * padding + "\n").encode("latin1")
    return prefix + struct.pack("<H", len(encoded)) + encoded + payload


class StageAInventoryTests(unittest.TestCase):
    def setUp(self):
        self.declaration = load_stage_a_config(CONFIG)["sources"]["pathmnist-224"]

    def _records(self, path: Path, source_id: str, version: str, family: str) -> list[dict]:
        payload = path.read_bytes()
        world = AdmissionWorld(
            source_id=source_id,
            version=version,
            family=family,
            artifacts=[{
                "logical_path": path.name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }],
        )
        return list(world.records.values())

    def _archive(self, folder: str) -> Path:
        path = Path(folder) / "pathmnist_224.npz"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
            for split in ("train", "val"):
                archive.writestr(f"{split}_images.npy", _npy_bytes("|u1", (2, 2, 2, 3), bytes(24)))
                archive.writestr(f"{split}_labels.npy", _npy_bytes("|u1", (2, 1), bytes([0, 1])))
            archive.writestr("test_images.npy", b"poison-never-open")
            archive.writestr("test_labels.npy", b"poison-never-open")
        return path

    def test_pathmnist_headers_open_only_train_and_val(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._archive(folder)
            records = self._records(path, "pathmnist-224", "3.0", "nct-crc")
            result = inventory_pathmnist_headers(path, records, "2026-10-16T08:10:30Z", self.declaration)
        self.assertEqual(
            [row["member"] for row in result["opened_members"]],
            ["train_images.npy", "train_labels.npy", "val_images.npy", "val_labels.npy"],
        )
        self.assertEqual(result["unopened_forbidden_members"], ["test_images.npy", "test_labels.npy"])
        self.assertFalse(result["test_payload_opened"])

    def test_missing_or_extra_member_rejects(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._archive(folder)
            records = self._records(path, "pathmnist-224", "3.0", "nct-crc")
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("surprise.npy", b"x")
            with self.assertRaises(ValueError):
                inventory_pathmnist_headers(path, records, "2026-10-16T08:10:30Z", self.declaration)

    def test_mismatched_custody_records_reject_before_archive_access(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._archive(folder)
            bad = self._records(path, "other-source", "3.0", "nct-crc")
            with self.assertRaises(ValueError):
                inventory_pathmnist_headers(path, bad, "2026-10-16T08:10:30Z", self.declaration)

    def test_changed_payload_rejects_before_archive_access(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._archive(folder)
            records = self._records(path, "pathmnist-224", "3.0", "nct-crc")
            path.write_bytes(path.read_bytes() + b"changed")
            with self.assertRaises(ValueError):
                inventory_pathmnist_headers(path, records, "2026-10-16T08:10:30Z", self.declaration)

    def test_busbra_inventory_keeps_only_frozen_training_population_eligible(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "BUSBRA.zip"
            _build_busbra_archive(path)
            records = self._records(path, "bus-bra", "1.0", "bus-bra")
            result = inventory_busbra(
                path, records, "2026-10-16T08:10:30Z", _busbra_declaration(path)
            )
        dispositions = {row["record_id"]: row["disposition"] for row in result["records"]}
        self.assertEqual(dispositions["bus_0001-l"], "eligible")
        self.assertEqual(dispositions["bus_0001-r"], "eligible")
        self.assertEqual(dispositions["bus_0002-s"], "excluded")
        self.assertEqual(result["eligible_parent_count"], 1)
        self.assertFalse(result["model_use_authorized"])
        self.assertFalse(result["mmbu_public_content_used"])

    def test_busbra_inventory_requires_protected_opening(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "BUSBRA.zip"
            _build_busbra_archive(path)
            bad = self._records(path, "other-source", "1.0", "bus-bra")
            with self.assertRaises(ValueError):
                inventory_busbra(path, bad, "2026-10-16T08:10:30Z", _busbra_declaration(path))


if __name__ == "__main__":
    unittest.main()
