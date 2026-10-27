#!/usr/bin/env python3
"""Build and verify Stage A source-admission packets without opening data."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from mmbu_phase1 import canonical  # noqa: E402
from mmbu_phase1.source_admission_stage_a import (  # noqa: E402
    acquire_artifacts_once,
    acquisition_command_digest,
    acquisition_method_digest,
    build_acquisition_packet,
    build_structural_opening_records,
    inventory_archive_member_headers,
    inventory_busi_whu_structural,
    inventory_pathmnist_structural,
    load_stage_a_config,
    stage_a_acquisition_authority_subject,
    stage_a_structural_authority_subject,
    validate_acquisition_packet,
    validate_structural_opening_packet,
    verify_acquisition_authority,
)
from mmbu_phase1 import admission  # noqa: E402
from mmbu_phase1.external_trust import verify_external_authority  # noqa: E402
from mmbu_phase1.store import RecordStore  # noqa: E402


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        raise


def build_packet(args: argparse.Namespace) -> int:
    config = load_stage_a_config(args.config)
    commit = args.repository_commit or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    now = datetime.now(timezone.utc)
    launch_id = args.launch_id or now.strftime("%Y%m%dT%H%M%SZ-") + str(uuid.uuid4())
    run_root = args.run_root or f"/storage/scr/npl015/mmbu-admission/{launch_id}"
    created_at = args.created_at or now.isoformat(timespec="seconds").replace("+00:00", "Z")
    packet = build_acquisition_packet(config, commit, launch_id, run_root, created_at)
    payload = canonical.dumps(packet)
    _write_new(args.output, payload)
    print(f"canonical_digest={packet['record_digest']}")
    print(f"full_file_sha256={hashlib.sha256(payload).hexdigest()}")
    print(f"launch_id={launch_id}")
    print(f"run_root={run_root}")
    return 0


def verify_packet(args: argparse.Namespace) -> int:
    config = load_stage_a_config(args.config)
    payload = args.packet.read_bytes()
    packet = canonical.loads(payload)
    if canonical.dumps(packet) != payload:
        raise ValueError("packet file is not canonical RFC 8785 JSON")
    validate_acquisition_packet(packet, config)
    print(f"canonical_digest={packet['record_digest']}")
    print(f"full_file_sha256={hashlib.sha256(payload).hexdigest()}")
    return 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class _RedirectRecorder(HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.observed_hosts: set[str] = set()
        self.allowed_hosts: set[str] = set()

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        host = urlparse(newurl).hostname
        if host is None or host not in self.allowed_hosts:
            raise ValueError("redirect target host is not allowlisted")
        self.observed_hosts.add(host)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class _OneShotOpener:
    def __init__(self):
        self.redirects = _RedirectRecorder()
        self.opener = build_opener(self.redirects)

    @property
    def observed_hosts(self):
        return self.redirects.observed_hosts

    def set_allowed_hosts(self, hosts: set[str]):
        self.redirects.allowed_hosts = set(hosts)

    def __call__(self, url: str):
        request = Request(url, headers={"User-Agent": "mmbu-stage-a-acquisition/1"})
        return self.opener.open(request, timeout=300)


def _load_canonical(path: Path):
    payload = path.read_bytes()
    value = canonical.loads(payload)
    if canonical.dumps(value) != payload:
        raise ValueError(f"{path} is not canonical RFC 8785 JSON")
    return value


def acquire_source(args: argparse.Namespace) -> int:
    config = load_stage_a_config(args.config)
    packet = _load_canonical(args.packet)
    records = _load_canonical(args.records)
    if not isinstance(records, list):
        raise ValueError("acquisition authority file must be a canonical JSON array")
    started_at = _utc_now()
    external = _external_authority(
        args, "acquisition", stage_a_acquisition_authority_subject(packet, args.source_id),
        "mmbu.phase1.stage-a-acquisition.v1", "data-owner", started_at,
    )
    authority = verify_acquisition_authority(
        records, packet, config, args.source_id, started_at, external,
    )
    source = authority["source"]
    status_path = Path(packet["run_root"]) / "records" / f"{args.source_id}-transport-status.json"
    try:
        observed = acquire_artifacts_once(
            source,
            Path(source["staging_destination"]),
            _OneShotOpener(),
            required_free_bytes=(
                sum(row["maximum_bytes"] for row in packet["sources"].values())
                + packet["work_margin_bytes"]
            ),
        )
        ended_at = _utc_now()
        receipt = canonical.seal({
            "schema_id": "mmbu.phase1.acquisition_execution_receipt",
            "schema_version": 1,
            "receipt_id": f"stage-a-{packet['launch_id']}-{args.source_id}",
            "acquisition_authorization_digest": authority["authorization"]["record_digest"],
            "authorization_registry_digest": authority["registry"]["record_digest"],
            "source_id": args.source_id,
            "source_version": source["source_version"],
            "source_family": source["source_family"],
            "executed_method_digest": acquisition_method_digest(source),
            "executed_command_digest": acquisition_command_digest(source),
            "operator_id": authority["authorization"]["operator_id"],
            "observed_hosts": observed["observed_hosts"],
            "observed_artifacts": observed["observed_artifacts"],
            "staging_destination": source["staging_destination"],
            "started_at": started_at,
            "ended_at": ended_at,
            "retrieval_log_digest": canonical.value_digest(observed),
            "exit_code": 0,
            "terminal_status": "succeeded",
        })
        store = RecordStore([*records, receipt])
        admission.check_acquisition_execution_receipt(
            store, receipt["record_digest"], "stage_a.execution_receipt"
        )
        receipt_path = Path(packet["run_root"]) / "records" / f"{args.source_id}-execution-receipt.json"
        _write_new(receipt_path, canonical.dumps(receipt))
        status = canonical.seal({
            "schema_id": "mmbu.phase1.stage_a_transport_status",
            "schema_version": 1,
            "source_id": args.source_id,
            "status": "succeeded",
            "execution_receipt_digest": receipt["record_digest"],
            "error_class": None,
            "error_message": None,
            "mmbu_public_content_used": False,
            "payload_opened": False,
            "ended_at": ended_at,
        })
        _write_new(status_path, canonical.dumps(status))
        print(f"execution_receipt_digest={receipt['record_digest']}")
        return 0
    except BaseException as exc:
        status = canonical.seal({
            "schema_id": "mmbu.phase1.stage_a_transport_status",
            "schema_version": 1,
            "source_id": args.source_id,
            "status": "failed",
            "execution_receipt_digest": None,
            "error_class": type(exc).__name__,
            "error_message": str(exc),
            "mmbu_public_content_used": False,
            "payload_opened": False,
            "ended_at": _utc_now(),
        })
        _write_new(status_path, canonical.dumps(status))
        print(f"acquisition failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def structural_inspect(args: argparse.Namespace) -> int:
    config = load_stage_a_config(args.config)
    packet_payload = args.packet.read_bytes()
    if hashlib.sha256(packet_payload).hexdigest() != args.packet_sha256:
        raise ValueError("structural packet full-file SHA-256 mismatch")
    packet = canonical.loads(packet_payload)
    if canonical.dumps(packet) != packet_payload:
        raise ValueError("structural packet is not canonical JSON")
    evidence = {}
    for source_id in ("bus-bra", "busi-whu", "pathmnist-224"):
        evidence[source_id] = {
            "packet": _load_canonical(args.evidence_root / f"{source_id}-acquisition-packet.json"),
            "authority_records": _load_canonical(args.evidence_root / f"{source_id}-acquisition-authority.json"),
            "execution_receipt": _load_canonical(args.evidence_root / f"{source_id}-execution-receipt.json"),
        }
    validate_structural_opening_packet(packet, config, evidence)
    if packet["repository_commit"] != args.repository_commit.read_text(encoding="ascii").strip():
        raise ValueError("staged repository commit differs from the sealed structural packet")
    source = packet["sources"][args.source_id]
    output = Path(packet["run_root"]) / "results" / args.source_id
    status_path = Path(packet["run_root"]) / "records" / f"{args.source_id}-structural-status.json"
    if output.exists() or status_path.exists():
        raise FileExistsError("structural output already exists; one-shot inspection will not overwrite")
    output.mkdir(parents=True, mode=0o700)
    try:
        started = datetime.now(timezone.utc).replace(microsecond=0)
        reviewed_at = started.isoformat().replace("+00:00", "Z")
        subject = stage_a_structural_authority_subject(packet, args.source_id)
        owner = _external_authority(
            args, "owner", subject, "mmbu.phase1.stage-a-structural-opening.v1",
            "data-owner", reviewed_at,
        )
        reviewer = _external_authority(
            args, "reviewer", subject, "mmbu.phase1.stage-a-structural-opening.v1",
            "independent-reviewer", reviewed_at,
        )
        records = build_structural_opening_records(
            packet, args.source_id, evidence[args.source_id]["authority_records"],
            evidence[args.source_id]["execution_receipt"], owner, reviewer, reviewed_at,
        )
        records_path = output / "opening-records.json"
        _write_new(records_path, canonical.dumps(records))
        now = _utc_now()
        staging = Path(source["staging_destination"])
        if args.source_id == "bus-bra":
            result = inventory_archive_member_headers(staging / "BUSBRA.zip", records, now, args.source_id)
        elif args.source_id == "pathmnist-224":
            result = inventory_pathmnist_structural(
                staging / "pathmnist_224.npz", staging / "pathmnist_split_info.csv",
                records, now, config["sources"][args.source_id],
            )
        elif args.source_id == "busi-whu":
            result = inventory_busi_whu_structural(
                staging / "BUSI-WHU.zip", staging / "Patient_infos_BUSI-WHU.xlsx", records, now,
            )
        else:
            raise ValueError("source is outside the sealed structural source set")
        _write_new(output / "structural-inventory.json", canonical.dumps(result))
        status = canonical.seal({
            "schema_id": "mmbu.phase1.stage_a_structural_status", "schema_version": 1,
            "source_id": args.source_id, "status": "succeeded",
            "packet_digest": packet["record_digest"], "inventory_digest": result["record_digest"],
            "error_class": None, "error_message": None,
            "image_payload_decoding_used": False, "label_values_read": False,
            "model_use_authorized": False, "mmbu_public_content_used": False,
            "ended_at": _utc_now(),
        })
        _write_new(status_path, canonical.dumps(status))
        print(f"inventory_digest={result['record_digest']}")
        return 0
    except BaseException as exc:
        status = canonical.seal({
            "schema_id": "mmbu.phase1.stage_a_structural_status", "schema_version": 1,
            "source_id": args.source_id, "status": "failed", "packet_digest": packet["record_digest"],
            "inventory_digest": None, "error_class": type(exc).__name__, "error_message": str(exc),
            "image_payload_decoding_used": False, "label_values_read": False,
            "model_use_authorized": False, "mmbu_public_content_used": False,
            "ended_at": _utc_now(),
        })
        _write_new(status_path, canonical.dumps(status))
        print(f"structural inspection failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def _external_authority(
    args: argparse.Namespace, prefix: str, subject: dict, namespace: str,
    role: str, verified_at: str,
):
    value = lambda name: getattr(args, f"{prefix}_external_{name}")  # noqa: E731
    return verify_external_authority(
        policy_bytes=value("policy").read_bytes(),
        policy_pin_sha256=value("policy_pin"),
        public_key_bytes=value("public_key").read_bytes(),
        public_key_pin_sha256=value("public_key_pin"),
        revocation_bytes=value("revocation").read_bytes(),
        revocation_pin_sha256=value("revocation_pin"),
        signature_bytes=value("signature").read_bytes(),
        subject=subject,
        namespace=namespace,
        principal=value("principal"), role=role,
        signed_at=value("signed_at"), verified_at=verified_at,
        verifier_path=value("verifier"), verifier_pin_sha256=value("verifier_pin"),
    )


def _add_external_authority_arguments(parser: argparse.ArgumentParser, prefix: str) -> None:
    option = f"--{prefix}-external-"
    parser.add_argument(option + "policy", type=Path, required=True)
    parser.add_argument(option + "policy-pin", required=True)
    parser.add_argument(option + "public-key", type=Path, required=True)
    parser.add_argument(option + "public-key-pin", required=True)
    parser.add_argument(option + "revocation", type=Path, required=True)
    parser.add_argument(option + "revocation-pin", required=True)
    parser.add_argument(option + "signature", type=Path, required=True)
    parser.add_argument(option + "principal", required=True)
    parser.add_argument(option + "signed-at", required=True)
    parser.add_argument(option + "verifier", type=Path, required=True)
    parser.add_argument(option + "verifier-pin", required=True)


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser()
    sub = cli.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build-packet")
    build.add_argument("--config", type=Path, default=REPO / "config/phase1/source-admission-stage-a.json")
    build.add_argument("--repository-commit")
    build.add_argument("--launch-id")
    build.add_argument("--run-root")
    build.add_argument("--created-at")
    build.add_argument("--output", type=Path, required=True)
    build.set_defaults(func=build_packet)
    verify = sub.add_parser("verify-packet")
    verify.add_argument("--config", type=Path, default=REPO / "config/phase1/source-admission-stage-a.json")
    verify.add_argument("--packet", type=Path, required=True)
    verify.set_defaults(func=verify_packet)
    acquire = sub.add_parser("acquire-source")
    acquire.add_argument("--config", type=Path, default=REPO / "config/phase1/source-admission-stage-a.json")
    acquire.add_argument("--packet", type=Path, required=True)
    acquire.add_argument("--records", type=Path, required=True)
    acquire.add_argument("--source-id", required=True)
    _add_external_authority_arguments(acquire, "acquisition")
    acquire.set_defaults(func=acquire_source)
    inspect = sub.add_parser("structural-inspect")
    inspect.add_argument("--config", type=Path, default=REPO / "config/phase1/source-admission-stage-a.json")
    inspect.add_argument("--packet", type=Path, required=True)
    inspect.add_argument("--packet-sha256", required=True)
    inspect.add_argument("--evidence-root", type=Path, required=True)
    inspect.add_argument("--repository-commit", type=Path, required=True)
    _add_external_authority_arguments(inspect, "owner")
    _add_external_authority_arguments(inspect, "reviewer")
    inspect.add_argument("--source-id", choices=("bus-bra", "pathmnist-224", "busi-whu"), required=True)
    inspect.set_defaults(func=structural_inspect)
    return cli


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
