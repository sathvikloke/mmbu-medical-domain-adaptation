"""Focused guards for bounded/offline processor-artifact handling; no network."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / 'tools' / 'processor_probe.py'
spec = importlib.util.spec_from_file_location('processor_probe', MODULE_PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ArtifactGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.model = {'model_id': 'example/test', 'revision': 'a' * 40}
        self.directory = self.root / 'example--test' / ('a' * 40)
        self.directory.mkdir(parents=True)
        self.records = []
        for name in probe.REQUIRED | {'chat_template.jinja'}:
            data = b'{}'
            (self.directory / name).write_bytes(data)
            self.records.append({'filename': name, 'status': 'downloaded', 'bytes': len(data), 'sha256': probe.sha256(data)})
        self.manifest = dict(self.model, files=self.records)
        self.save()

    def save(self):
        probe.dump(self.directory / 'artifact-manifest.json', self.manifest)

    def test_offline_never_fetches_and_validates_snapshot(self):
        with patch.object(probe.urllib.request, 'urlopen', side_effect=AssertionError('network forbidden')):
            directory, manifest = probe.artifacts(self.model, self.root, False)
        self.assertEqual(directory, self.directory)
        self.assertEqual(manifest['revision'], self.model['revision'])

    def test_offline_detects_tampering(self):
        (self.directory / 'tokenizer.json').write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'hash/size mismatch'):
            probe.artifacts(self.model, self.root, False)

    def test_offline_refuses_weight_file(self):
        (self.directory / 'model.safetensors').write_bytes(b'not actual weights')
        with self.assertRaisesRegex(ValueError, 'unexpected files'):
            probe.artifacts(self.model, self.root, False)

    def test_offline_refuses_unmanifested_optional_artifact(self):
        (self.directory / "special_tokens_map.json").write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "unexpected files"):
            probe.artifacts(self.model, self.root, False)

    def test_offline_refuses_identity_change(self):
        self.manifest['revision'] = 'b' * 40
        self.save()
        with self.assertRaisesRegex(ValueError, 'identity disagrees'):
            probe.artifacts(self.model, self.root, False)

    def test_manifest_cannot_add_arbitrary_file(self):
        self.records.append({'filename': '../arbitrary.py', 'status': 'http_404'})
        self.save()
        with self.assertRaisesRegex(ValueError, 'unexpected or duplicate'):
            probe.artifacts(self.model, self.root, False)

    def test_mutable_revision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'full lowercase'):
            probe.validate_identity('example/test', 'main')

    def test_oversize_download_fails_before_write(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit): return b'x' * limit
        with patch.object(probe, 'MAX_FILE_BYTES', 4), patch.object(probe.urllib.request, 'urlopen', return_value=Response()):
            with self.assertRaisesRegex(ValueError, 'exceeds'):
                probe.artifacts(self.model, self.root, True)
        self.assertEqual((self.directory / 'config.json').read_bytes(), b'{}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
