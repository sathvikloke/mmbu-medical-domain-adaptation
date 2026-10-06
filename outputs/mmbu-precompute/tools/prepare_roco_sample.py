#!/usr/bin/env python3
"""Reproduce the fixed 24-image ROCO quarantine sample, without granting use."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from mmbu_prep.images import inspect_images
from mmbu_prep.presentation import present_image
from mmbu_prep.roco import build_roco_inventory


def prepare(metadata, acquired, receipt, output):
    acquired, output = Path(acquired).resolve(), Path(output)
    if output.exists():
        raise FileExistsError(str(output))
    expected_receipt = {
        'schema_version': 1, 'source_id': 'rocov2', 'source_version': '2.0.1',
        'source_partition': 'train', 'selected_images': 24,
        'source_url': 'https://zenodo.org/api/records/10821435/files/train_images.zip/content',
        'expected_archive_bytes': 4611440786,
        'publisher_expected_archive_md5': 'cd5f5fdb73f24cf6a7473319116a84cc',
        'shortlist_sha256': 'd815b2238224f8e92cf5f321aba387e9a4ca3686bfd4dab13bf1c3b4377b9014',
        'selected_member_crc_verified': True, 'whole_archive_checksum_verified': False,
        'model_use_approved': False,
    }
    if not isinstance(receipt, dict) or any(
        type(receipt.get(key)) is not type(value) or receipt.get(key) != value
        for key, value in expected_receipt.items()
    ):
        raise ValueError('Receipt identity or fixed sample declarations differ from the pinned intake')
    inventory, audit = build_roco_inventory(metadata, per_modality=4, seed=1729)
    if not audit['release_integrity_verified']:
        raise ValueError('Metadata differs from the pinned publisher files')
    by_id = {r['source_image_id']: r for r in inventory}
    selected = [by_id[x] for x in audit['shortlist_source_image_ids']]
    if len(selected) != 24 or len({r['group_id'] for r in selected}) != 24:
        raise ValueError('Expected fixed 24-image, 24-article sample')
    expected = {'train/' + r['source_image_id'] + '.jpg' for r in selected}
    if not isinstance(receipt, dict) or not isinstance(receipt.get('members'), list):
        raise ValueError('Acquisition member receipt required')
    entries = receipt['members']
    if len(entries) != 24 or {r.get('member') for r in entries} != expected:
        raise ValueError('Acquisition receipt differs from the fixed sample')
    for entry in entries:
        path = acquired / entry['member']
        if path.is_symlink() or not path.resolve().is_relative_to(acquired) or not path.is_file():
            raise ValueError('Unsafe or missing source image')
        if type(entry.get('bytes')) is not int or not 0 < entry['bytes'] <= 8_388_608:
            raise ValueError('Invalid or excessive source image length')
        if path.stat().st_size != entry['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != entry.get('sha256'):
            raise ValueError('Acquired image differs from receipt')
    entries = {r['member']: r for r in entries}
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.roco-prepare-', dir=output.parent))
    try:
        rows, presentations, sidecars = [], [], []
        (stage / 'raw').mkdir()
        for item in selected:
            sid = item['source_image_id']
            if not re.fullmatch(r'ROCOv2_2023_train_[0-9]{6}', sid):
                raise ValueError('Unexpected source identifier')
            source = acquired / 'train' / (sid + '.jpg')
            raw = stage / 'raw' / (sid + '.jpg')
            shutil.copyfile(source, raw)
            if hashlib.sha256(raw.read_bytes()).hexdigest() != entries['train/' + sid + '.jpg']['sha256']:
                raise ValueError('Source changed during copy')
            presentation = present_image(raw, stage / 'images' / (sid + '.png'))
            presentation.update(source_image_id=sid, output_path='images/' + sid + '.png', source_path='raw/' + sid + '.jpg')
            presentations.append(presentation)
            rows.append(dict(schema_version=1, record_id=item['metadata_record_id'], source_id='rocov2', source_version='2.0.1', source_family='pmc-literature', split='train', source_partition='train', image_path=presentation['output_path'], image_sha256=presentation['image_sha256'], parent_image_sha256=presentation['parent_image_sha256'], image_width=presentation['width'], image_height=presentation['height'], group_id=item['group_id'], task='global_classification', question=item['proposed_question'], answer=item['proposed_answer'], context={}, annotation_origin='source-manual-concepts', conversion_version='rocov2-manual-modality-image-sample-v1', review_status='pending', synthetic=False, source_image_id=sid, pmcid=item['pmcid'], original_figure_id=None, source_metadata_path='source-metadata.json', allowed_purposes=[]))
            sidecars.append(item)
        inspection = inspect_images(rows, image_root=stage)
        if not inspection['ok']:
            raise ValueError('Presentation inspection failed: ' + str(inspection['errors']))
        (stage / 'pending-manifest.jsonl').write_text(''.join(json.dumps(r, sort_keys=True, allow_nan=False) + '\n' for r in rows))
        for name, data in [('source-metadata.json', sidecars), ('presentations.json', presentations), ('image-inspection.json', inspection), ('metadata-audit.json', audit)]:
            (stage / name).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
        if output.exists():
            raise FileExistsError(str(output))
        stage.rename(output)
        return {'records': len(rows), 'articles': len({r['group_id'] for r in rows}), 'all_review_status_pending': True, 'model_use_approved': False, 'source_partition': 'train', 'output': str(output)}
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--acquired', required=True)
    parser.add_argument('--receipt', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = prepare(args.metadata, args.acquired, json.loads(Path(args.receipt).read_text()), args.output)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
