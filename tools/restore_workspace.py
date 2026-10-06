#!/usr/bin/env python3
"""Restore the private handoff's checksummed research files without overwriting changes."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tempfile
import unicodedata
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate manifest key')
            result[key] = value
        return result
    data = json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON value')))
    if not isinstance(data, dict):
        raise ValueError('Manifest must be an object')
    if type(data.get('schema_version')) is not int or data.get('schema_version') != 1 or data.get('repository') != 'sathvikloke/mmbu-medical-domain-adaptation':
        raise ValueError('Unexpected handoff manifest identity')
    if data.get('release_tag') != 'team-handoff-v0.3' or data.get('archive_name') != 'workspace-data.zip':
        raise ValueError('Unexpected release identity')
    if type(data.get('archive_bytes')) is not int or not 0 < data['archive_bytes'] <= 2_000_000_000:
        raise ValueError('Invalid archive byte count')
    if not re.fullmatch('[0-9a-f]{64}', str(data.get('archive_sha256', ''))):
        raise ValueError('Invalid archive digest')
    files = data.get('files')
    if not isinstance(files, dict) or not files or len(files) > 10000:
        raise ValueError('Expected bounded nonempty file map')
    seen = set()
    for name, item in files.items():
        path = PurePosixPath(name)
        key = unicodedata.normalize('NFC', name).casefold()
        if (path.as_posix() != name or path.is_absolute() or '..' in path.parts or
                not path.parts or path.parts[0] != 'work' or len(path.parts) < 2 or
                '\\' in name or '\0' in name or ':' in name or key in seen):
            raise ValueError('Unsafe or colliding manifest path')
        seen.add(key)
        if not isinstance(item, dict) or type(item.get('bytes')) is not int or not 0 <= item['bytes'] <= 100_000_000:
            raise ValueError('Invalid member byte count')
        if not re.fullmatch('[0-9a-f]{64}', str(item.get('sha256', ''))):
            raise ValueError('Invalid member digest')
    for name in files:
        parts = PurePosixPath(name).parts
        if any(unicodedata.normalize('NFC', '/'.join(parts[:i])).casefold() in seen for i in range(1, len(parts))):
            raise ValueError('Manifest file is also a parent directory')
    if sum(x['bytes'] for x in files.values()) > 2_000_000_000:
        raise ValueError('Expanded workspace exceeds limit')
    return data


def target_path(root, name):
    path = root
    parts = PurePosixPath(name).parts
    for index, part in enumerate(parts):
        path = path / part
        if path.is_symlink():
            raise ValueError('Refusing target symlink: ' + name)
        if index < len(parts)-1 and path.exists() and not path.is_dir():
            raise ValueError('Target parent is not a directory: ' + name)
    if not path.resolve().is_relative_to(root):
        raise ValueError('Target escaped workspace')
    return path


def restore(archive, manifest, target, *, dry_run=False):
    archive = Path(archive)
    root = Path(target).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Target must be an existing directory')
    if archive.stat().st_size != manifest['archive_bytes'] or digest(archive) != manifest['archive_sha256']:
        raise ValueError('Archive differs from the trusted repository manifest')
    files = manifest['files']
    existing = set()
    for name, item in files.items():
        dest = target_path(root, name)
        if dest.exists():
            if not dest.is_file() or dest.stat().st_size != item['bytes'] or digest(dest) != item['sha256']:
                raise ValueError('Existing file differs; nothing overwritten: ' + name)
            existing.add(name)
    with tempfile.TemporaryDirectory(prefix='.mmbu-restore-', dir=root) as temp:
        stage = Path(temp)
        with zipfile.ZipFile(archive) as z:
            members = z.infolist()
            if len(members) != len(files) or {x.filename for x in members} != set(files):
                raise ValueError('Archive member set differs from manifest')
            for info in members:
                expected = files[info.filename]
                if (info.is_dir() or info.flag_bits & 1 or (stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG))
                        or info.file_size != expected['bytes']):
                    raise ValueError('Unsupported or mis-sized archive member')
                path = stage / info.filename
                path.parent.mkdir(parents=True, exist_ok=True)
                h = hashlib.sha256(); count = 0
                with z.open(info) as source, path.open('xb') as dest:
                    for chunk in iter(lambda: source.read(1048576), b''):
                        count += len(chunk)
                        if count > expected['bytes']:
                            raise ValueError('Expanded member exceeds manifest size')
                        h.update(chunk); dest.write(chunk)
                if count != expected['bytes'] or h.hexdigest() != expected['sha256']:
                    raise ValueError('Member content digest mismatch')
        if not dry_run:
            for name in files:
                if name in existing:
                    continue
                dest = target_path(root, name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                target_path(root, name)
                # Exclusive atomic publication. Staging is on the target filesystem.
                os.link(stage / name, dest)
    return {'verified_files': len(files), 'existing_identical': len(existing),
            'restored_files': 0 if dry_run else len(files)-len(existing), 'dry_run': dry_run,
            'model_use_approved': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--archive', type=Path)
    source.add_argument('--download', action='store_true', help='Use authenticated gh to download the private release asset')
    parser.add_argument('--manifest', type=Path, default=ROOT/'research/workspace-data-manifest.json')
    parser.add_argument('--target', type=Path, default=ROOT)
    parser.add_argument('--dry-run', action='store_true', help='Verify all bytes and destination conflicts without restoring files')
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        if args.download:
            cache = ROOT/'.local'; cache.mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='download-', dir=cache) as temp:
                subprocess.run(['gh','release','download',manifest['release_tag'],'--repo',manifest['repository'],
                                '--pattern',manifest['archive_name'],'--dir',temp],check=True)
                result = restore(Path(temp)/manifest['archive_name'], manifest, args.target, dry_run=args.dry_run)
        else:
            result = restore(args.archive, manifest, args.target, dry_run=args.dry_run)
        print(json.dumps(result, indent=2)); return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print(json.dumps({'status':'failed','error':str(error)})); return 2


if __name__ == '__main__':
    raise SystemExit(main())
