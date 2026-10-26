import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.external_trust import verify_external_authority


OPENSSL = shutil.which("openssl")


@unittest.skipUnless(OPENSSL, "OpenSSL is required for the external-trust verifier test")
class ExternalTrustTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.private_key = self.root / "private.pem"
        self.public_key = self.root / "public.pem"
        subprocess.run(
            [OPENSSL, "genpkey", "-algorithm", "ED25519", "-out", str(self.private_key)],
            check=True, capture_output=True,
        )
        subprocess.run(
            [OPENSSL, "pkey", "-in", str(self.private_key), "-pubout", "-out", str(self.public_key)],
            check=True, capture_output=True,
        )
        self.subject = canonical.seal({
            "schema_id": "mmbu.phase1.synthetic_external_subject",
            "schema_version": 1,
            "operation": "protected_opening",
            "source_id": "synthetic-source",
        })
        self.namespace = "mmbu.phase1.protected-opening.v1"
        self.principal = "synthetic-reviewer@example.invalid"
        self.role = "data-rights-authority"
        self.envelope = canonical.dumps({
            "namespace": self.namespace,
            "principal": self.principal,
            "role": self.role,
            "signed_at": "2026-10-26T13:30:00Z",
            "subject": self.subject,
        })
        self.envelope_path = self.root / "subject.json"
        self.signature_path = self.root / "signature.bin"
        self.envelope_path.write_bytes(self.envelope)
        subprocess.run(
            [OPENSSL, "pkeyutl", "-sign", "-inkey", str(self.private_key), "-rawin",
             "-in", str(self.envelope_path), "-out", str(self.signature_path)],
            check=True, capture_output=True,
        )
        self.openssl_bytes = Path(OPENSSL).read_bytes()
        self.public_key_bytes = self.public_key.read_bytes()
        self.revocation = canonical.dumps(canonical.seal({
            "schema_id": "mmbu.phase1.external_revocation_snapshot",
            "schema_version": 1,
            "key_sha256": hashlib.sha256(self.public_key_bytes).hexdigest(),
            "status": "active",
            "observed_at": "2026-10-26T13:00:00Z",
            "expires_at": "2026-10-27T13:00:00Z",
        }))
        self.policy = canonical.dumps(canonical.seal({
            "schema_id": "mmbu.phase1.external_signer_policy",
            "schema_version": 1,
            "namespace": self.namespace,
            "principal": self.principal,
            "role": self.role,
            "key_sha256": hashlib.sha256(self.public_key_bytes).hexdigest(),
            "verifier_sha256": hashlib.sha256(self.openssl_bytes).hexdigest(),
            "valid_from": "2026-10-26T12:00:00Z",
            "valid_until": "2026-10-27T12:00:00Z",
        }))

    def tearDown(self):
        self.tempdir.cleanup()

    def kwargs(self):
        return {
            "policy_bytes": self.policy,
            "policy_pin_sha256": hashlib.sha256(self.policy).hexdigest(),
            "public_key_bytes": self.public_key_bytes,
            "public_key_pin_sha256": hashlib.sha256(self.public_key_bytes).hexdigest(),
            "revocation_bytes": self.revocation,
            "revocation_pin_sha256": hashlib.sha256(self.revocation).hexdigest(),
            "signature_bytes": self.signature_path.read_bytes(),
            "subject": self.subject,
            "namespace": self.namespace,
            "principal": self.principal,
            "role": self.role,
            "signed_at": "2026-10-26T13:30:00Z",
            "verified_at": "2026-10-26T13:31:00Z",
            "verifier_path": Path(OPENSSL),
            "verifier_pin_sha256": hashlib.sha256(self.openssl_bytes).hexdigest(),
        }

    def test_pinned_external_signature_constructs_private_capability(self):
        capability = verify_external_authority(**self.kwargs())
        self.assertEqual(capability.namespace, self.namespace)
        self.assertEqual(capability.subject_digest, canonical.value_digest(self.subject))
        self.assertEqual(capability.principal, self.principal)
        self.assertEqual(capability.role, self.role)
        self.assertTrue(capability.verifier_version.startswith("OpenSSL "))

    def test_self_created_replacement_replay_and_revocation_fail_closed(self):
        changed = self.kwargs()
        changed["public_key_pin_sha256"] = "0" * 64
        with self.assertRaises(ContractViolation):
            verify_external_authority(**changed)

        changed = self.kwargs()
        changed["namespace"] = "mmbu.phase1.source-admission.v1"
        with self.assertRaises(ContractViolation):
            verify_external_authority(**changed)

        revoked = canonical.loads(self.revocation)
        revoked["status"] = "revoked"
        revoked = canonical.dumps(canonical.seal({k: v for k, v in revoked.items() if k != "record_digest"}))
        changed = self.kwargs()
        changed["revocation_bytes"] = revoked
        changed["revocation_pin_sha256"] = hashlib.sha256(revoked).hexdigest()
        with self.assertRaises(ContractViolation):
            verify_external_authority(**changed)


if __name__ == "__main__":
    unittest.main()
