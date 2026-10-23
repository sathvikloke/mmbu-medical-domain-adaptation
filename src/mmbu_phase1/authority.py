"""Bootstrap and validate the three mutable Phase 1 execution-state authorities.

``python3 -m mmbu_phase1.authority bootstrap [--root DIR]`` is the one tested
command that creates ``config/phase1/current-status.json`` plus generation-zero
authorization and opening-receipt registries.  It never overwrites existing
authority, records its actual UTC creation time, and derives every ID and
digest through the canonical kernel.  ``verify`` re-validates the files.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys

from mmbu_phase1 import canonical, fields as f, paths, registries, status
from mmbu_phase1.contract_manifest import (
    EXPECTED_CONTRACT_REVISION,
    EXPECTED_MANIFEST_SHA256,
    verify_contract_manifest,
)

STATUS_PATH = "config/phase1/current-status.json"
AUTHORIZATION_REGISTRY_PATH = "config/phase1/authorization-registry.json"
OPENING_RECEIPT_REGISTRY_PATH = "config/phase1/opening-receipt-registry.json"
AUTHORITY_PATHS = (STATUS_PATH, AUTHORIZATION_REGISTRY_PATH, OPENING_RECEIPT_REGISTRY_PATH)
MANIFEST_PATH = "docs/phase1/contract-manifest.json"

# Bootstrap facts: everything not measured stays explicit and unclaimed.
BOOTSTRAP_FACTS = (
    ("account.gpu_allocation", "unknown",
     "No GPU was requested, allocated, or measured; Phase 1A is CPU-only and public GPU specifications cannot "
     "support an allocation fact."),
    ("account.mocs_account", "unknown",
     "No MOCS account, credential, or account receipt has been captured or verified."),
    ("account.mocs_allocation", "unknown",
     "No MOCS allocation or scheduler receipt exists; a public cluster specification cannot support this fact."),
    ("data.real_source_admission", "blocked_external",
     "No real biomedical source has acquisition authority, rights, grouping, QA, custody, or purpose "
     "authorization; the required human rights and review authority is external to Phase 1A."),
    ("runtime.b1_native_admission", "unknown",
     "B1 weights and the D1 runtime were not downloaded, installed, loaded, or executed; the B1 native "
     "admission gate in B1_RUNTIME_GATE.md is unexecuted."),
)


@dataclass(frozen=True)
class ContractPins:
    revision: str
    manifest_sha256: str
    official_source_hashes: dict


def contract_pins(root: Path) -> ContractPins:
    """Verify the exact nine-member contract, then return its pins."""
    root = Path(root)
    errors = verify_contract_manifest(root)
    if errors:
        f.fail("contract", "contract integrity failed: " + "; ".join(errors))
    raw = paths.member_bytes(root, MANIFEST_PATH)
    if canonical.raw_digest(raw) != EXPECTED_MANIFEST_SHA256:
        f.fail("contract", "contract manifest changed after verification")
    manifest = canonical.loads(raw)
    return ContractPins(EXPECTED_CONTRACT_REVISION, EXPECTED_MANIFEST_SHA256, dict(manifest["official_source_hashes"]))


def derived_id(schema_name: str, generation: int, created_at: str) -> str:
    seed = {"created_at": created_at, "generation": generation, "schema_id": f.SCHEMA_PREFIX + schema_name}
    return f"{schema_name}-g{generation}-{canonical.value_digest(seed)[:32]}"


def build_authority(pins: ContractPins, now: str) -> dict[str, dict]:
    f.timestamp(now, "now")
    current = canonical.seal({
        "schema_id": f.SCHEMA_PREFIX + "current_status",
        "schema_version": 1,
        "contract_revision": pins.revision,
        "contract_manifest_digest": pins.manifest_sha256,
        "official_source_hashes": dict(pins.official_source_hashes),
        "phase": "design_only",
        "facts": [
            {"fact_id": fact_id, "status": state, "value": None, "unit": None, "evidence_digests": [], "limitation": note}
            for fact_id, state, note in BOOTSTRAP_FACTS
        ],
        "updated_at": now,
    })
    authorization = canonical.seal({
        "schema_id": f.SCHEMA_PREFIX + "authorization_registry",
        "schema_version": 1,
        "registry_id": derived_id("authorization_registry", 0, now),
        "generation": 0,
        "supersedes_registry_digest": None,
        "acquisition_authorization_digests": [],
        "source_record_digests": [],
        "purpose_authorization_digests": [],
        "acquisition_heads": {},
        "source_heads": {},
        "authorization_heads": {},
        "revoked_digests": [],
        "as_of": now,
    })
    opening = canonical.seal({
        "schema_id": f.SCHEMA_PREFIX + "opening_receipt_registry",
        "schema_version": 1,
        "registry_id": derived_id("opening_receipt_registry", 0, now),
        "generation": 0,
        "supersedes_registry_digest": None,
        "heads": [],
        "created_at": now,
    })
    return {STATUS_PATH: current, AUTHORIZATION_REGISTRY_PATH: authorization, OPENING_RECEIPT_REGISTRY_PATH: opening}


def validate_authority_records(records: dict[str, dict], pins: ContractPins) -> None:
    status.validate_current_status(
        records[STATUS_PATH],
        contract_revision=pins.revision,
        contract_manifest_digest=pins.manifest_sha256,
        official_source_hashes=pins.official_source_hashes,
        path=STATUS_PATH,
    )
    registries.validate_authorization_registry(records[AUTHORIZATION_REGISTRY_PATH], AUTHORIZATION_REGISTRY_PATH)
    registries.validate_opening_receipt_registry(records[OPENING_RECEIPT_REGISTRY_PATH], OPENING_RECEIPT_REGISTRY_PATH)


def bootstrap(root: Path, now: str | None = None) -> dict[str, bytes]:
    """Create the three authorities; refuse to overwrite any existing path."""
    root = Path(root)
    pins = contract_pins(root)
    for relative in AUTHORITY_PATHS:
        if os.path.lexists(root / relative):
            f.fail(relative, "authority already exists; bootstrap never overwrites authority")
    records = build_authority(pins, now or f.utc_now())
    validate_authority_records(records, pins)
    payloads = {relative: canonical.dumps(record) for relative, record in records.items()}
    (root / "config/phase1").mkdir(parents=True, exist_ok=True)
    for relative, data in payloads.items():
        descriptor = os.open(root / relative, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
    return payloads


def load_authority(root: Path) -> dict[str, dict]:
    """Load and validate all three authorities as exact canonical bytes."""
    root = Path(root)
    pins = contract_pins(root)
    records: dict[str, dict] = {}
    for relative in AUTHORITY_PATHS:
        raw = paths.member_bytes(root, relative, relative)
        try:
            records[relative] = canonical.loads_canonical(raw)
        except canonical.CanonicalJSONError as exc:
            f.fail(relative, f"authority bytes are invalid or noncanonical: {exc}")
    validate_authority_records(records, pins)
    return records


def authority_errors(root: Path) -> list[str]:
    try:
        load_authority(root)
    except (f.ContractViolation, OSError) as exc:
        return [f"Phase 1 authority: {exc}"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m mmbu_phase1.authority", description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("bootstrap", "verify"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        if args.command == "bootstrap":
            written = bootstrap(args.root)
            for relative, data in written.items():
                print(f"wrote {relative} ({len(data)} bytes, sha256 {canonical.raw_digest(data)})")
        else:
            for relative in load_authority(args.root):
                print(f"verified {relative}")
    except (f.ContractViolation, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
