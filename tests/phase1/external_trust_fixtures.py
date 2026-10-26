import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.external_trust import verify_external_authority


OPENSSL = shutil.which("openssl")


def external_authority_for(
    subject: dict, *, namespace: str, principal: str, role: str,
    signed_at: str, verified_at: str,
):
    if OPENSSL is None:
        raise unittest.SkipTest("OpenSSL is required for external-authority fixtures")
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        private_key = root / "private.pem"
        public_key = root / "public.pem"
        envelope = root / "envelope.json"
        signature = root / "signature.bin"
        subprocess.run(
            [OPENSSL, "genpkey", "-algorithm", "ED25519", "-out", str(private_key)],
            check=True, capture_output=True,
        )
        subprocess.run(
            [OPENSSL, "pkey", "-in", str(private_key), "-pubout", "-out", str(public_key)],
            check=True, capture_output=True,
        )
        public_key_bytes = public_key.read_bytes()
        verifier_bytes = Path(OPENSSL).read_bytes()
        key_digest = hashlib.sha256(public_key_bytes).hexdigest()
        verifier_digest = hashlib.sha256(verifier_bytes).hexdigest()
        policy = canonical.dumps(canonical.seal({
            "schema_id": "mmbu.phase1.external_signer_policy", "schema_version": 1,
            "namespace": namespace, "principal": principal, "role": role,
            "key_sha256": key_digest, "verifier_sha256": verifier_digest,
            "valid_from": "2026-10-01T00:00:00Z", "valid_until": "2026-11-01T00:00:00Z",
        }))
        revocation = canonical.dumps(canonical.seal({
            "schema_id": "mmbu.phase1.external_revocation_snapshot", "schema_version": 1,
            "key_sha256": key_digest, "status": "active",
            "observed_at": "2026-10-01T00:00:00Z", "expires_at": "2026-11-01T00:00:00Z",
        }))
        envelope.write_bytes(canonical.dumps({
            "namespace": namespace, "principal": principal, "role": role,
            "signed_at": signed_at, "subject": subject,
        }))
        subprocess.run(
            [OPENSSL, "pkeyutl", "-sign", "-inkey", str(private_key), "-rawin",
             "-in", str(envelope), "-out", str(signature)],
            check=True, capture_output=True,
        )
        return verify_external_authority(
            policy_bytes=policy, policy_pin_sha256=hashlib.sha256(policy).hexdigest(),
            public_key_bytes=public_key_bytes, public_key_pin_sha256=key_digest,
            revocation_bytes=revocation,
            revocation_pin_sha256=hashlib.sha256(revocation).hexdigest(),
            signature_bytes=signature.read_bytes(), subject=subject, namespace=namespace,
            principal=principal, role=role, signed_at=signed_at, verified_at=verified_at,
            verifier_path=Path(OPENSSL), verifier_pin_sha256=verifier_digest,
        )
