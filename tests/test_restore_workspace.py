"""Real ZIP/path regression tests for the private research handoff restorer."""
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('restore_workspace', Path(__file__).resolve().parents[1]/'tools/restore_workspace.py')
restore = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore)


def sha(data):
    return hashlib.sha256(data).hexdigest()


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root/'target'; self.target.mkdir()
        self.archive = self.root/'workspace-data.zip'
        self.members = {'work/a.txt':b'first\n', 'work/sub/b.txt':b'second\n'}
        self.make_archive()

    def make_archive(self, members=None):
        with zipfile.ZipFile(self.archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for name, data in (members or self.members).items():
                z.writestr(name,data)
        self.manifest = {'schema_version':1,'repository':'sathvikloke/mmbu-medical-domain-adaptation',
                         'release_tag':'team-handoff-v0.3','archive_name':'workspace-data.zip',
                         'archive_bytes':self.archive.stat().st_size,'archive_sha256':restore.digest(self.archive),
                         'files':{n:{'bytes':len(b),'sha256':sha(b)} for n,b in self.members.items()}}

    def validate(self):
        path=self.root/'manifest.json';path.write_text(json.dumps(self.manifest))
        return restore.load_manifest(path)

    def test_restore_then_idempotent_replay(self):
        result=restore.restore(self.archive,self.validate(),self.target)
        self.assertEqual(result['restored_files'],2)
        self.assertFalse(result['model_use_approved'])
        for name, data in self.members.items():
            self.assertEqual((self.target/name).read_bytes(),data)
        self.assertEqual(restore.restore(self.archive,self.validate(),self.target)['existing_identical'],2)

    def test_dry_run_checks_without_persistent_files(self):
        result=restore.restore(self.archive,self.validate(),self.target,dry_run=True)
        self.assertEqual(result['verified_files'],2)
        self.assertEqual(result['restored_files'],0)
        self.assertEqual(list(self.target.iterdir()),[])

    def test_archive_digest_failure_creates_nothing(self):
        self.archive.write_bytes(self.archive.read_bytes()+b'tampered')
        with self.assertRaisesRegex(ValueError,'Archive differs'):
            restore.restore(self.archive,self.validate(),self.target)
        self.assertEqual(list(self.target.iterdir()),[])

    def test_last_member_bad_hash_does_not_publish_first(self):
        self.manifest['files']['work/sub/b.txt']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'digest mismatch'):
            restore.restore(self.archive,self.validate(),self.target)
        self.assertEqual(list(self.target.iterdir()),[])

    def test_existing_conflict_preserved_and_new_file_not_published(self):
        dest=self.target/'work/sub/b.txt';dest.parent.mkdir(parents=True);dest.write_bytes(b'my work')
        with self.assertRaisesRegex(ValueError,'nothing overwritten'):
            restore.restore(self.archive,self.validate(),self.target)
        self.assertEqual(dest.read_bytes(),b'my work')
        self.assertFalse((self.target/'work/a.txt').exists())

    def test_symlink_parent_cannot_escape(self):
        outside=self.root/'outside';outside.mkdir();(self.target/'work').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):
            restore.restore(self.archive,self.validate(),self.target)
        self.assertEqual(list(outside.iterdir()),[])

    def test_existing_file_as_parent_preflight_blocks_all_publication(self):
        (self.target/'work').mkdir();(self.target/'work/sub').write_text('keep me')
        with self.assertRaisesRegex(ValueError,'parent is not a directory'):
            restore.restore(self.archive,self.validate(),self.target)
        self.assertFalse((self.target/'work/a.txt').exists())
        self.assertEqual((self.target/'work/sub').read_text(),'keep me')

    def test_unlisted_archive_member_rejected(self):
        self.make_archive({**self.members,'work/extra.txt':b'not declared'})
        with self.assertRaisesRegex(ValueError,'member set'):
            restore.restore(self.archive,self.validate(),self.target)
        self.assertEqual(list(self.target.iterdir()),[])

    def test_symlink_archive_member_rejected(self):
        with zipfile.ZipFile(self.archive,'w') as z:
            for name, data in self.members.items():
                info=zipfile.ZipInfo(name);info.create_system=3
                info.external_attr=(stat.S_IFLNK | 0o777)<<16
                z.writestr(info,data)
        self.manifest.update(archive_bytes=self.archive.stat().st_size,archive_sha256=restore.digest(self.archive))
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            restore.restore(self.archive,self.validate(),self.target)
        self.assertEqual(list(self.target.iterdir()),[])

    def test_unsafe_manifest_names_rejected(self):
        original=self.manifest['files']
        for name in ['../escape','work/../escape','/work/absolute','work//a','work/./a','work\\a','work/C:foo','work']:
            with self.subTest(name=name):
                self.manifest['files']={name:next(iter(original.values()))}
                with self.assertRaises(ValueError):self.validate()

    def test_case_collision_and_file_parent_rejected(self):
        entry=next(iter(self.manifest['files'].values()))
        for names in [('work/A','work/a'),('work/a','work/a/b'),('work/A','work/a/b')]:
            self.manifest['files']={n:entry for n in names}
            with self.assertRaises(ValueError):self.validate()

    def test_bool_version_and_nonfinite_and_duplicate_keys_rejected(self):
        self.manifest['schema_version']=True
        with self.assertRaises(ValueError):self.validate()
        self.manifest['schema_version']=1;self.manifest['extra']=float('nan')
        with self.assertRaises(ValueError):self.validate()
        path=self.root/'duplicates.json';path.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaisesRegex(ValueError,'Duplicate'):restore.load_manifest(path)


if __name__=='__main__':
    unittest.main()
