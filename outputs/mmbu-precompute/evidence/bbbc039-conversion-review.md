# Independent BBBC039 conversion review

Status: **PASS for the bounded quarantine conversion, after three repairs.** This is not model-use approval, medical annotation validation, or a 16-pass scientific audit. The reviewer did not author or edit `bbbc039.py` or its tests. Review covered that module, its targeted tests, real source-training conversions, and associated metadata/QA flags. CLI/model-config behavior is outside this review.

The independent oracle uses horizontal runs and disjoint-set union, rather than the production breadth-first pixel flood fill. It imports neither the production decoder nor any other production code. It opened exactly the 100 filenames in the official source-training list; source validation/test image and mask contents were never opened. Notebook/source semantics are documented in [the source audit](../docs/bbbc039-source-audit.md).

## Findings and closure

| ID | Initial severity / confidence | Concrete original failure | Minimal repair and independently verified closure |
| --- | --- | --- | --- |
| BBBC039-CONV-01 | P2 / high | An RGB PNG carrying `tRNS` transparency stayed in Pillow mode `RGB`; the old RGBA-only opacity check accepted it. A transparent `(9,8,7)` pixel produced one instance and published output. | Reject transparency metadata before channel decoding. An independent replay now raises `ValueError: Annotation mask carries transparency metadata` and publishes no output. Closed. |
| BBBC039-CONV-02 | P2 / high | A valid 16-bit RGB PNG with adjacent red values 256 and 257 was decoded by Pillow into byte values 1 and 1; the intake silently merged them and published one instance. This violates the converter's uint8 input contract. | Inspect raw PNG IHDR before Pillow conversion: require 8-bit RGB/RGBA color type. Independent replay now raises the precision-loss rejection and publishes no output. Closed. |
| BBBC039-CONV-03 | P3 / high | A valid big-endian uint16 TIFF passed the advertised `I;16B` mode check, then failed `getextrema()` with `ValueError: image has wrong mode`. Its little-endian equivalent succeeded. | Compute statistics through lossless `convert('I')`, retaining the native mode and original bytes. Independent replay now accepts `I;16B`, reports extrema `[0,65535]`, and preserves raw bytes exactly. Closed. |

The first two findings were acceptance/interpretation risks; the third was a compatibility failure. All real source-training masks were opaque 8-bit RGBA, and the real TIFFs passed the original path. No misconverted real record was found. Repairs are at the final `prepare_quarantine` image-statistics and PNG-header/transparency checks, approximately lines 134–149. Root's preserved red logs are `bbbc039-transparency-red.txt`, `bbbc039-mask-depth-red.txt`, and `bbbc039-endian-red.txt`; this reviewer also independently reproduced all three original counterexamples and replayed all three after repair.

Final targeted command, run from `outputs/mmbu-precompute`:

```sh
PYTHONPATH=src /Users/sathvikloke/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest discover -s tests -p test_bbbc039.py -v
```

Result: exit 0, **13 tests passed**. A prior intermediate run, while the newly added endian regression was red, had 13 tests / one endian error; this was superseded by the final run, not discarded as a pass. Independent synthetic fixtures additionally rejected traversal, backslash paths, absolute paths, symlink entries, a member over 16,000,000 bytes, and excess member count. Little-endian native uint16 preserved extrema `[0,65535]`; an 8-bit TIFF was rejected. The final three repair replays ran against an unchanged source hash before/after execution.

## Real conversion evidence

- 100 source-training images and masks; all 696×520 in x/y order.
- **11,999 decoded instances**, **1,997 border-touching instances**, and **7,181,074 nonzero first-channel pixels**.
- Exact agreement for every instance ID, red value, area, xywh box, and border flag. The oracle derives extrema from pixel runs, independently checking the inclusive-pixel to half-open box `+1` rule and x/y ordering.
- Exact source-archive-member versus prepared-file byte equality for every training TIFF and mask; matching SHA256 provenance, plate identity, source split, dimensions, and native extrema.
- 198 pending records: 100 counts and 98 box lists. Each remains real (`synthetic:false`), `source_split:training`, `split:engineering`, and `review_status:pending`. No heldout file appears among prepared images, masks, or annotation sidecars.
- The two empty masks are fields `IXMtest_F13_s7_w13C1B1D8C-293E-454F-B0FD-6C2C3F9F5173` and `IXMtest_L01_s2_w1E5038251-DBA3-44D0-BC37-E43E2FC8C174`. Their QA rows explicitly say `empty_mask_requires_review` and remain pending. Zero decoded components are **not validated negative examples**. Detection records are omitted, and the pending count-zero rows remain blocked from model use.

The official metadata was independently parsed as headerless CSV with `newline=''`. Original split names govern selection, not the misleading common `IXMtest` filename prefix. Plate grouping is conservative lineage information; all 20 training plates are also represented in another source split, so this review does not certify acquisition independence. Raw bytes stay separate from any future intensity preview or processor policy.

## Reproducible independent oracle

Run the following Python block with the bundled Python from the project root. It reads only source-training archive members. It checks the existing conversion without re-running or importing its implementation. The block was executed after writing this review and must produce the summary below with no assertion failure.

```python
from pathlib import Path
import csv, hashlib, io, json, zipfile
import numpy as np
from PIL import Image

base = Path('/Users/sathvikloke/Documents/Codex/2026-10-01/https-akiranishii-github-io-mmbu-challenge')
archives = base / 'work/bbbc039-quarantine/archives'
prepared = base / 'work/bbbc039-quarantine/prepared'
with zipfile.ZipFile(archives / 'metadata.zip') as archive:
    parts = {s: archive.read('metadata/' + s + '.txt').decode().splitlines()
             for s in ('training', 'validation', 'test')}
    plates = dict(csv.reader(io.StringIO(archive.read(
        'metadata/filenames_and_plates.csv').decode(), newline='')))
training = set(parts['training'])
assert len(training) == 100
assert not training.intersection(parts['validation'] + parts['test'])
for folder, suffix in (('images', '.tif'), ('masks', '.png'), ('annotations', '.json')):
    assert {p.stem + '.png' for p in (prepared / folder).iterdir()} == training

def oracle(red):
    height, width = red.shape
    parent, runs, previous = [], [], []
    def root(i):
        while i != parent[i]:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for y, row in enumerate(red):
        edges = np.r_[0, np.flatnonzero(row[1:] != row[:-1]) + 1, width]
        current = []
        for left, right in zip(edges[:-1], edges[1:]):
            left, right = int(left), int(right)
            value = int(row[left])
            if value == 0:
                continue
            index = len(runs)
            parent.append(index)
            runs.append((y, left, right, value))
            current.append((left, right, value, index))
        first = 0
        for left, right, value, index in current:
            while first < len(previous) and previous[first][1] < left:
                first += 1
            other = first
            while other < len(previous) and previous[other][0] <= right:
                _, _, prior_value, prior_index = previous[other]
                if prior_value == value:
                    a, b = root(index), root(prior_index)
                    if a != b:
                        parent[max(a, b)] = min(a, b)
                other += 1
        previous = current
    groups = {}
    for index, (y, left, right, value) in enumerate(runs):
        key = root(index)
        if key not in groups:
            groups[key] = dict(first=(y, left), value=value, area=0,
                               left=left, right=right, top=y, bottom=y+1)
        group = groups[key]
        group['area'] += right - left
        group['left'] = min(group['left'], left)
        group['right'] = max(group['right'], right)
        group['top'] = min(group['top'], y)
        group['bottom'] = max(group['bottom'], y+1)
    result = []
    for index, group in enumerate(sorted(groups.values(), key=lambda g: g['first']), 1):
        result.append(dict(instance_id=index, red_value=group['value'],
            area_pixels=group['area'], bbox_xywh=[group['left'], group['top'],
            group['right']-group['left'], group['bottom']-group['top']],
            touches_border=(group['left']==0 or group['top']==0 or
                            group['right']==width or group['bottom']==height)))
    return result

sha = lambda b: hashlib.sha256(b).hexdigest()
records = [json.loads(line) for line in (prepared/'pending-records.jsonl').read_text().splitlines()]
by_id = {record['record_id']: record for record in records}
total = borders = foreground = 0
empty = []
with zipfile.ZipFile(archives/'images.zip') as images, zipfile.ZipFile(archives/'masks.zip') as masks:
    for name in sorted(training):
        stem = Path(name).stem
        image_name, mask_name = 'images/'+stem+'.tif', 'masks/'+name
        image_bytes, mask_bytes = images.read(image_name), masks.read(mask_name)
        assert image_bytes == (prepared/image_name).read_bytes()
        assert mask_bytes == (prepared/mask_name).read_bytes()
        assert mask_bytes[24:26] == bytes([8, 6])
        with Image.open(io.BytesIO(image_bytes)) as image:
            image.load()
            size, mode, extrema = image.size, image.mode, image.convert('I').getextrema()
            assert size == (696, 520) and image.getexif().get(274, 1) == 1
        with Image.open(io.BytesIO(mask_bytes)) as mask:
            mask.load()
            assert mask.mode == 'RGBA' and mask.size == size
            assert 'transparency' not in mask.info and mask.getexif().get(274, 1) == 1
            pixels = np.asarray(mask)
            assert np.all(pixels[:, :, 3] == 255)
            expected = oracle(pixels[:, :, 0])
            count_pixels = int(np.count_nonzero(pixels[:, :, 0]))
            assert sum(x['area_pixels'] for x in expected) == count_pixels
        annotation = json.loads((prepared/'annotations'/f'{stem}.json').read_text())
        assert annotation['instances'] == expected and annotation['count'] == len(expected)
        assert [annotation['width'], annotation['height']] == list(size)
        assert annotation['image_mode'] == mode and annotation['image_extrema'] == list(extrema)
        assert annotation['image_sha256'] == sha(image_bytes)
        assert annotation['mask_sha256'] == sha(mask_bytes)
        assert annotation['source_plate'] == plates[name]
        assert annotation['source_split'] == 'training' and annotation['review_status'] == 'pending'
        count_record = by_id[stem+':count']
        assert count_record['answer'] == len(expected)
        selected = [count_record]
        if expected:
            selected.append(by_id[stem+':boxes'])
            assert selected[-1]['answer'] == [x['bbox_xywh'] for x in expected]
        else:
            empty.append(stem)
            assert stem+':boxes' not in by_id
        for record in selected:
            assert record['source_split'] == 'training' and record['split'] == 'engineering'
            assert record['synthetic'] is False and record['review_status'] == 'pending'
            assert record['source_field_id'] == stem and record['group_id'] == 'plate:'+plates[name]
            assert record['image_sha256'] == sha(image_bytes) and record['mask_sha256'] == sha(mask_bytes)
            assert [record['image_width'], record['image_height']] == list(size)
        total += len(expected)
        borders += sum(x['touches_border'] for x in expected)
        foreground += count_pixels
report = json.loads((prepared/'intake-report.json').read_text())
assert (total, borders, len(records)) == (report['nucleus_instances'], report['border_touching_instances'], report['pending_records'])
print(json.dumps(dict(training_images=len(training), instances=total, border_instances=borders,
    foreground_pixels=foreground, pending_records=len(records), empty_masks=len(empty),
    heldout_image_or_mask_members_opened=0, exact_instance_and_raw_byte_match=True), indent=2))
```

Observed replay summary: `training_images=100`, `instances=11999`, `border_instances=1997`, `foreground_pixels=7181074`, `pending_records=198`, `empty_masks=2`, `heldout_image_or_mask_members_opened=0`, exact instance and raw-byte match true. The first oracle run completed in about 1.36 seconds; timing is not a performance claim.

## Final snapshot and limits

| Artifact | SHA256 |
| --- | --- |
| `src/mmbu_prep/bbbc039.py` | `7aba9689dc44d0b6139d3eb8024efe31555802d6a6a23d69880696c38ab6438a` |
| `tests/test_bbbc039.py` | `ae386dd92b34014031c7a585529faa924838eb6503b96f7578c0a9a94fa46d6f` |
| `work/bbbc039-quarantine/prepared/pending-records.jsonl` | `61aa39297fe8dae88a56e264ee4c8d03f69dbcc31999019bddf6e3b21381cb85` |
| `work/bbbc039-quarantine/prepared/intake-report.json` | `e62982f4fbdd664df6a5ee0a8dd15675fd3a1c4f21e887cedb15cfa06c237801` |

No open defect remains in the reviewed scope. Archive guards and staged publication were checked for these concrete cases; this is not a general security certification or proof against every adversarial file. Oracle agreement establishes faithful conversion of first-channel connected components, not biological correctness of individual masks. No visual nucleus adjudication, clinical suitability, competition eligibility, absence of benchmark overlap, perceptual deduplication, source independence, or training benefit is claimed. Raw 16-bit preservation does not resolve the future display/model-processor policy. Eligibility, label review, and approval gates remain required before any model use.

Review recorded at 2026-10-04T05:16:11.253174+00:00.
