"""Conservative perceptual candidate triage, never automatic deduplication."""
import hashlib
from io import BytesIO
import math
from pathlib import Path
from .images import inspect_images


def triage_duplicates(records, *, image_root, max_distance=4, max_aspect_ratio_difference=0.05, max_images=1000):
    """Compare versioned 64-bit horizontal luminance difference hashes.

    Only inspected RGB8/L8 presentations are accepted. Similar hashes are weak
    structural evidence, not identity, patient linkage, or absence-of-leakage
    certification. No images, records, split assignments or groups are changed.
    """
    if type(max_distance) is not int or not 0 <= max_distance <= 64:
        raise ValueError('max_distance must be an integer in [0,64]')
    if type(max_aspect_ratio_difference) not in (int,float) or not math.isfinite(max_aspect_ratio_difference) or not 0 <= max_aspect_ratio_difference <= 1:
        raise ValueError('max_aspect_ratio_difference must be finite in [0,1]')
    if type(max_images) is not int or not 1 <= max_images <= 1000:
        raise ValueError('max_images must be an integer in [1,1000]')
    if not isinstance(records,list) or len(records) > max_images:
        raise ValueError('Expected a bounded list of image records')
    inspection=inspect_images(records,image_root=image_root)
    if not inspection['ok']:
        raise ValueError('Image inspection failed: '+str(inspection['errors']))
    from PIL import Image
    fingerprints=[]
    root=Path(image_root)
    for row,info in zip(records,inspection['images']):
        if info['mode'] not in ('RGB','L') or info['decoded_bits_per_sample'] != 8 or info['orientation_requires_transform']:
            raise ValueError('Triage requires explicitly presented RGB8 or L8 in identity orientation')
        with (root/row['image_path']).open('rb') as stream:
            payload=stream.read(67_108_865)
        if len(payload)>67_108_864 or hashlib.sha256(payload).hexdigest()!=info['raw_sha256']:
            raise ValueError('Image changed after inspection')
        with Image.open(BytesIO(payload)) as image:
            if 'transparency' in image.info:
                raise ValueError('Transparent images require an explicit presentation policy')
            gray=image.convert('L').resize((9,8),Image.Resampling.BILINEAR)
            pixels=list(gray.get_flattened_data())
        bits=[pixels[y*9+x] > pixels[y*9+x+1] for y in range(8) for x in range(8)]
        value=sum(int(bit) << (63-i) for i,bit in enumerate(bits))
        fingerprints.append({'record_id':row['record_id'],'source_id':row['source_id'],'split':row['split'],
            'width':info['width'],'height':info['height'],'raw_sha256':info['raw_sha256'],
            'pixel_sha256':info['pixel_sha256'],'dhash64':f'{value:016x}',
            'low_information_hash':sum(bits) <= 2 or sum(bits) >= 62,'thumbnail_range':max(pixels)-min(pixels)})
    candidates=[]
    for i,a in enumerate(fingerprints):
        for b in fingerprints[i+1:]:
            cross1=a['width']*b['height'];cross2=b['width']*a['height']
            aspect=abs(cross1-cross2)/max(cross1,cross2)
            distance=(int(a['dhash64'],16)^int(b['dhash64'],16)).bit_count()
            if distance <= max_distance and aspect <= max_aspect_ratio_difference:
                exact=a['pixel_sha256']==b['pixel_sha256']
                candidates.append({'record_ids':[a['record_id'],b['record_id']], 'hamming_distance':distance,
                    'relative_aspect_difference':aspect,'cross_split':a['split']!=b['split'],
                    'exact_raw_match':a['raw_sha256']==b['raw_sha256'],'exact_decoded_match':exact,
                    'reason':'exact_decoded_match' if exact else 'weak_hash_requires_review' if a['low_information_hash'] or b['low_information_hash'] else 'perceptual_candidate_requires_review'})
    return {'schema_version':1,'algorithm':'pillow-gray8-bilinear-9x8-horizontal-strict-greater-msb-first-v1',
        'max_distance':max_distance,'max_aspect_ratio_difference':max_aspect_ratio_difference,
        'images':fingerprints,'candidates':candidates,'automatic_merge_or_exclusion':False,
        'absence_of_near_duplicates_certified':False,
        'limitations':['Color is discarded; flat/monotonic images can collide.','Crops, flips, overlays and changed panels may escape this hash.','Thresholds are engineering settings, not medically calibrated decision rules.','Candidates require side-by-side review before any provenance or split decision.']}
