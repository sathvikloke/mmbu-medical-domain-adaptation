import hashlib
import os
from pathlib import Path
import tempfile
import unittest

from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.protected_io import open_authorized_artifact
from tests.phase1.test_busi_whu_authority import ReviewAuthorityWorld, t


class ProtectedArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        (self.root / "busi-whu").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def capability(self, relative="busi-whu/archive.zip", payload=b"authorized artifact"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        artifacts = [{
            "logical_path": relative,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }]
        world = ReviewAuthorityWorld(input_root=str(self.root), artifacts=artifacts)
        capability = world.store(), world
        return (
            __import__("mmbu_phase1.busi_whu_authority", fromlist=["validate_busi_whu_review_opening"])
            .validate_busi_whu_review_opening(
                capability[0], world.authorization["record_digest"],
                world.world.digest("review_opening"), t("09:10:02"),
            ),
            path,
        )

    def test_reads_and_hashes_the_retained_descriptor(self):
        capability, path = self.capability(payload=b"same descriptor bytes")
        with open_authorized_artifact(capability, "busi-whu/archive.zip", "archive") as artifact:
            self.assertEqual(artifact.read(), b"same descriptor bytes")
            self.assertEqual(artifact.sha256, hashlib.sha256(b"same descriptor bytes").hexdigest())
            self.assertEqual(artifact.size, path.stat().st_size)
            self.assertEqual(artifact.pre_stat.identity, artifact.post_stat.identity)

    def test_unknown_path_and_wrong_role_reject_before_open(self):
        capability, _ = self.capability()
        with self.assertRaises(ContractViolation):
            open_authorized_artifact(capability, "busi-whu/not-authorized.zip", "archive")
        with self.assertRaises(ContractViolation):
            open_authorized_artifact(capability, "busi-whu/archive.zip", "metadata")

    def test_symlink_file_symlink_ancestor_and_hardlink_reject(self):
        capability, path = self.capability()
        real = path.with_name("real.zip")
        path.rename(real)
        path.symlink_to(real)
        with self.assertRaises((ContractViolation, OSError)):
            open_authorized_artifact(capability, "busi-whu/archive.zip", "archive")

        path.unlink()
        real.rename(path)
        hardlink = path.with_name("hardlink.zip")
        os.link(path, hardlink)
        with self.assertRaises(ContractViolation):
            open_authorized_artifact(capability, "busi-whu/archive.zip", "archive")
        hardlink.unlink()

        actual_root = self.root / "actual"
        actual_root.mkdir()
        (actual_root / "archive.zip").write_bytes(b"authorized artifact")
        alias = self.root / "alias"
        alias.symlink_to(actual_root, target_is_directory=True)
        artifacts = [{
            "logical_path": "archive.zip", "bytes": len(b"authorized artifact"),
            "sha256": hashlib.sha256(b"authorized artifact").hexdigest(),
        }]
        world = ReviewAuthorityWorld(input_root=str(alias), artifacts=artifacts)
        from mmbu_phase1.busi_whu_authority import validate_busi_whu_review_opening
        cap = validate_busi_whu_review_opening(
            world.store(), world.authorization["record_digest"],
            world.world.digest("review_opening"), t("09:10:02"),
        )
        with self.assertRaises(ContractViolation):
            open_authorized_artifact(cap, "archive.zip", "archive")

    def test_path_substitution_after_open_rejects(self):
        capability, path = self.capability(payload=b"first immutable bytes")
        with open_authorized_artifact(capability, "busi-whu/archive.zip", "archive") as artifact:
            original = path.with_name("preserved.zip")
            path.rename(original)
            path.write_bytes(b"first immutable bytes")
            with self.assertRaises(ContractViolation):
                artifact.read()

    def test_descriptor_mutation_after_open_rejects(self):
        capability, path = self.capability(payload=b"first immutable bytes")
        with open_authorized_artifact(capability, "busi-whu/archive.zip", "archive") as artifact:
            with path.open("r+b") as stream:
                stream.seek(0)
                stream.write(b"changed")
                stream.flush()
                os.fsync(stream.fileno())
            with self.assertRaises(ContractViolation):
                artifact.read()

    def test_stream_context_verifies_before_returning_control(self):
        capability, path = self.capability(payload=b"first immutable bytes")
        with open_authorized_artifact(capability, "busi-whu/archive.zip", "archive") as artifact:
            with self.assertRaises(ContractViolation):
                with artifact.stream() as stream:
                    self.assertEqual(stream.read(), b"first immutable bytes")
                    replacement = path.with_name("replacement.zip")
                    path.rename(replacement)
                    path.write_bytes(b"first immutable bytes")

    def test_size_and_hash_mismatch_reject(self):
        capability, path = self.capability(payload=b"first immutable bytes")
        path.write_bytes(b"different bytes")
        with self.assertRaises(ContractViolation):
            open_authorized_artifact(capability, "busi-whu/archive.zip", "archive")


if __name__ == "__main__":
    unittest.main()
