"""Executable verification of externally pinned human authority.

This module deliberately does not contain a repository key, default policy, or
fallback approval path.  Every policy, key, revocation snapshot, and verifier
binary must match a separately supplied SHA-256 pin before a detached Ed25519
signature can produce a capability.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from mmbu_phase1 import canonical, fields as f


_POLICY_KEYS = (
    "schema_id", "schema_version", "namespace", "principal", "role",
    "key_sha256", "verifier_sha256", "valid_from", "valid_until", "record_digest",
)
_REVOCATION_KEYS = (
    "schema_id", "schema_version", "key_sha256", "status", "observed_at",
    "expires_at", "record_digest",
)
_CAPABILITY_TOKEN = object()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_record(payload: bytes, schema: str, keys: tuple[str, ...], path: str) -> dict:
    try:
        value = canonical.loads_canonical(payload)
    except (canonical.CanonicalJSONError, UnicodeError) as exc:
        f.fail(path, f"must be exact canonical JSON: {exc}")
    return f.record(value, schema, keys, path)


def _instant(value: Any, path: str) -> int:
    return f.timestamp(value, path)


class ExternalAuthorityCapability:
    """Opaque proof returned only after all external checks succeed."""

    __slots__ = (
        "namespace", "principal", "role", "subject_digest", "policy_sha256",
        "public_key_sha256", "revocation_sha256", "signature_sha256",
        "signed_at", "verifier_sha256", "verifier_version", "verified_at",
        "verification_evidence_digest",
    )

    def __init__(
        self, token: object, *, namespace: str, principal: str, role: str,
        subject_digest: str, policy_sha256: str, public_key_sha256: str,
        revocation_sha256: str, signature_sha256: str, verifier_sha256: str,
        verifier_version: str, signed_at: str, verified_at: str,
    ) -> None:
        if token is not _CAPABILITY_TOKEN:
            raise TypeError("ExternalAuthorityCapability has no public constructor")
        for name, value in locals().copy().items():
            if name not in {"self", "token"}:
                object.__setattr__(self, name, value)
        evidence = {
            "namespace": namespace,
            "policy_sha256": policy_sha256,
            "principal": principal,
            "public_key_sha256": public_key_sha256,
            "revocation_sha256": revocation_sha256,
            "role": role,
            "signature_sha256": signature_sha256,
            "signed_at": signed_at,
            "subject_digest": subject_digest,
            "verified_at": verified_at,
            "verifier_sha256": verifier_sha256,
            "verifier_version": verifier_version,
        }
        object.__setattr__(self, "verification_evidence_digest", canonical.value_digest(evidence))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("ExternalAuthorityCapability is immutable")


def verify_external_authority(
    *,
    policy_bytes: bytes,
    policy_pin_sha256: str,
    public_key_bytes: bytes,
    public_key_pin_sha256: str,
    revocation_bytes: bytes,
    revocation_pin_sha256: str,
    signature_bytes: bytes,
    subject: Any,
    namespace: str,
    principal: str,
    role: str,
    signed_at: str,
    verified_at: str,
    verifier_path: Path,
    verifier_pin_sha256: str,
) -> ExternalAuthorityCapability:
    """Verify an externally pinned Ed25519 authority envelope with OpenSSL."""
    for label, value in (
        ("policy_pin_sha256", policy_pin_sha256),
        ("public_key_pin_sha256", public_key_pin_sha256),
        ("revocation_pin_sha256", revocation_pin_sha256),
        ("verifier_pin_sha256", verifier_pin_sha256),
    ):
        f.digest(value, f"external_trust.{label}")
    f.require(type(policy_bytes) is bytes, "external_trust.policy", "must be bytes")
    f.require(type(public_key_bytes) is bytes and public_key_bytes,
              "external_trust.public_key", "must be nonempty bytes")
    f.require(type(revocation_bytes) is bytes, "external_trust.revocation", "must be bytes")
    f.require(type(signature_bytes) is bytes and 0 < len(signature_bytes) <= 4096,
              "external_trust.signature", "must be bounded nonempty bytes")
    f.require(_sha256(policy_bytes) == policy_pin_sha256,
              "external_trust.policy", "does not match the out-of-band policy pin")
    f.require(_sha256(public_key_bytes) == public_key_pin_sha256,
              "external_trust.public_key", "does not match the out-of-band key pin")
    f.require(_sha256(revocation_bytes) == revocation_pin_sha256,
              "external_trust.revocation", "does not match the out-of-band revocation pin")

    policy = _canonical_record(policy_bytes, "external_signer_policy", _POLICY_KEYS,
                               "external_trust.policy")
    revocation = _canonical_record(
        revocation_bytes, "external_revocation_snapshot", _REVOCATION_KEYS,
        "external_trust.revocation",
    )
    for label, supplied, recorded in (
        ("namespace", namespace, policy["namespace"]),
        ("principal", principal, policy["principal"]),
        ("role", role, policy["role"]),
    ):
        f.text(supplied, f"external_trust.{label}")
        f.literal(supplied, f"external_trust.{label}", recorded)
    f.literal(policy["key_sha256"], "external_trust.policy.key_sha256", public_key_pin_sha256)
    f.literal(policy["verifier_sha256"], "external_trust.policy.verifier_sha256", verifier_pin_sha256)
    f.literal(revocation["key_sha256"], "external_trust.revocation.key_sha256", public_key_pin_sha256)
    f.literal(revocation["status"], "external_trust.revocation.status", "active")

    signed = _instant(signed_at, "external_trust.signed_at")
    verified = _instant(verified_at, "external_trust.verified_at")
    valid_from = _instant(policy["valid_from"], "external_trust.policy.valid_from")
    valid_until = _instant(policy["valid_until"], "external_trust.policy.valid_until")
    observed = _instant(revocation["observed_at"], "external_trust.revocation.observed_at")
    expires = _instant(revocation["expires_at"], "external_trust.revocation.expires_at")
    f.require(valid_from <= signed <= valid_until, "external_trust.signed_at",
              "must fall within the independently pinned signer validity interval")
    f.require(signed <= verified, "external_trust.verified_at", "cannot precede signing")
    f.require(observed <= verified <= expires, "external_trust.revocation",
              "snapshot must be current at verification")

    f.require(type(subject) is dict, "external_trust.subject", "must be a sealed record")
    f.sealed(subject, "external_trust.subject")
    envelope = canonical.dumps({
        "namespace": namespace,
        "principal": principal,
        "role": role,
        "signed_at": signed_at,
        "subject": subject,
    })

    verifier_path = Path(verifier_path)
    try:
        resolved_verifier = verifier_path.resolve(strict=True)
        before_stat = resolved_verifier.stat()
        verifier_bytes = resolved_verifier.read_bytes()
    except OSError as exc:
        f.fail("external_trust.verifier", f"cannot read pinned verifier: {exc}")
    f.require(resolved_verifier.is_file(), "external_trust.verifier", "must be a regular file")
    f.require(_sha256(verifier_bytes) == verifier_pin_sha256,
              "external_trust.verifier", "does not match the out-of-band verifier pin")

    with tempfile.TemporaryDirectory(prefix="mmbu-external-trust-") as temporary:
        root = Path(temporary)
        key_path = root / "public.pem"
        subject_path = root / "subject.json"
        signature_path = root / "signature.bin"
        verifier_copy = root / "pinned-verifier"
        key_path.write_bytes(public_key_bytes)
        subject_path.write_bytes(envelope)
        signature_path.write_bytes(signature_bytes)
        verifier_copy.write_bytes(verifier_bytes)
        verifier_copy.chmod(0o500)
        try:
            version_result = subprocess.run(
                [str(verifier_copy), "version"], stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False,
                env={"LC_ALL": "C", "PATH": ""},
            )
            result = subprocess.run(
                [str(verifier_copy), "pkeyutl", "-verify", "-pubin", "-inkey", str(key_path),
                 "-rawin", "-in", str(subject_path), "-sigfile", str(signature_path)],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                timeout=30, check=False, env={"LC_ALL": "C", "PATH": ""},
            )
        except (OSError, subprocess.SubprocessError) as exc:
            f.fail("external_trust.signature", f"pinned verifier failed: {exc}")
    f.require(version_result.returncode == 0, "external_trust.verifier", "version query failed")
    try:
        verifier_version = version_result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError:
        f.fail("external_trust.verifier", "version output must be UTF-8")
    f.text(verifier_version, "external_trust.verifier_version")
    f.require(len(verifier_version) <= 256, "external_trust.verifier_version", "is too long")
    try:
        after_stat = resolved_verifier.stat()
        after_digest = _sha256(resolved_verifier.read_bytes())
    except OSError as exc:
        f.fail("external_trust.verifier", f"cannot revalidate pinned verifier: {exc}")
    f.require(
        (before_stat.st_dev, before_stat.st_ino, before_stat.st_size, before_stat.st_mtime_ns)
        == (after_stat.st_dev, after_stat.st_ino, after_stat.st_size, after_stat.st_mtime_ns)
        and after_digest == verifier_pin_sha256,
        "external_trust.verifier", "changed during signature verification",
    )
    f.require(result.returncode == 0, "external_trust.signature", "detached signature verification failed")

    return ExternalAuthorityCapability(
        _CAPABILITY_TOKEN,
        namespace=namespace,
        principal=principal,
        role=role,
        subject_digest=canonical.value_digest(subject),
        policy_sha256=policy_pin_sha256,
        public_key_sha256=public_key_pin_sha256,
        revocation_sha256=revocation_pin_sha256,
        signature_sha256=_sha256(signature_bytes),
        signed_at=signed_at,
        verifier_sha256=verifier_pin_sha256,
        verifier_version=verifier_version,
        verified_at=verified_at,
    )


__all__ = ["ExternalAuthorityCapability", "verify_external_authority"]
