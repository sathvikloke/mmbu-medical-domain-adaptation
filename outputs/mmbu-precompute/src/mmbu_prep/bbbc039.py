"""Quarantined BBBC039 source-training inspection; never grants model-use approval."""

from collections import deque
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import zipfile

CONVERSION = 'bbbc039-red-equal-8-v1'


def _archive(path):
    archive = zipfile.ZipFile(path)
    try:
        seen = set()
        total = 0
        for member in archive.infolist():
            p = PurePosixPath(member.filename)
            if (p.is_absolute() or '..' in p.parts or '\\' in member.filename or
                    member.filename in seen or stat.S_ISLNK(member.external_attr >> 16) or member.flag_bits & 1):
                raise ValueError('Unsafe, encrypted, or duplicate archive member')
            seen.add(member.filename)
            total += member.file_size
            if member.file_size > 16_000_000 or total > 300_000_000 or len(seen) > 2000:
                raise ValueError('Archive exceeds bounded BBBC039 intake limits')
        return archive
    except BaseException:
        archive.close()
        raise


def _filename(value):
    if not isinstance(value,str) or not value or Path(value).name != value or '/' in value or '\\' in value or not value.endswith('.png'):
        raise ValueError('Metadata image names must be plain PNG basenames')
    return value


def read_metadata(path):
    """Read split names and plate identifiers; never read held-out image/mask data."""
    with _archive(path) as archive:
        splits = {}
        union = set()
        for split in ('training', 'validation', 'test'):
            names = [_filename(x.strip()) for x in archive.read('metadata/'+split+'.txt').decode('utf-8').splitlines() if x.strip()]
            if not names or len(set(names)) != len(names) or union.intersection(names):
                raise ValueError('Source splits must be nonempty, unique, and disjoint')
            union.update(names)
            splits[split] = sorted(names)
        plates = {}
        for row in csv.reader(io.StringIO(archive.read('metadata/filenames_and_plates.csv').decode('utf-8'),newline='')):
            if len(row)!=2 or not row[1].isdigit() or row[0] in plates:
                raise ValueError('Plate mapping is missing, duplicate, or malformed')
            plates[_filename(row[0])] = row[1]
        if set(plates) != union:
            raise ValueError('Split files and plate mapping must cover exactly the same images')
    plate_splits = {}
    for split,names in splits.items():
        for name in names: plate_splits.setdefault(plates[name],set()).add(split)
    return {'splits':splits,'plates':plates,'plates_shared_across_splits':sorted(p for p,s in plate_splits.items() if len(s)>1)}


def decode_instances(red_plane):
    """Label equal nonzero red values connected by any of eight neighbors.

    Independent implementation of the connected-component semantics referenced
    by the source decoder; no smoothing, object merging, or size filtering.
    Pixel-edge xywh includes each extreme pixel, so width/height use +1.
    """
    if not isinstance(red_plane,list) or not red_plane or not isinstance(red_plane[0],list) or not red_plane[0]:
        raise ValueError('Expected nonempty rectangular integer red plane')
    height,width=len(red_plane),len(red_plane[0])
    if height*width > 4_000_000:
        raise ValueError('Mask exceeds supported pixel ceiling')
    if any(not isinstance(row,list) or len(row)!=width or any(type(v) is not int or not 0<=v<=255 for v in row) for row in red_plane):
        raise ValueError('Red plane must be rectangular uint8 integers')
    seen=bytearray(width*height)
    instances=[]
    for y,row in enumerate(red_plane):
        for x,value in enumerate(row):
            index=y*width+x
            if not value or seen[index]: continue
            seen[index]=1
            pending=deque([(x,y)])
            minx=maxx=x;miny=maxy=y;area=0
            while pending:
                px,py=pending.popleft();area+=1
                minx=min(minx,px);maxx=max(maxx,px);miny=min(miny,py);maxy=max(maxy,py)
                for ny in range(max(0,py-1),min(height,py+2)):
                    for nx in range(max(0,px-1),min(width,px+2)):
                        i=ny*width+nx
                        if not seen[i] and red_plane[ny][nx]==value:
                            seen[i]=1;pending.append((nx,ny))
            instances.append({'instance_id':len(instances)+1,'red_value':value,'area_pixels':area,
                'bbox_xywh':[minx,miny,maxx-minx+1,maxy-miny+1],
                'touches_border':minx==0 or miny==0 or maxx==width-1 or maxy==height-1})
    return {'count':len(instances),'width':width,'height':height,'instances':instances,
            'decoder':CONVERSION,'connectivity':8,'background_red_value':0}


def prepare_quarantine(archives, output):
    """Inspect only the source training partition, publish unapproved sidecars.

    Raw bytes are preserved; no image normalization, resizing, or model prompt
    rendering is performed. The new output directory is published only after
    every selected file passes structural checks. Held-out bytes remain zipped.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError('Optional Pillow dependency is required for BBBC039 intake') from exc
    archives,output=Path(archives),Path(output)
    if output.exists(): raise FileExistsError(str(output))
    metadata=read_metadata(archives/'metadata.zip')
    output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.bbbc039-',dir=output.parent))
    digest=lambda b:hashlib.sha256(b).hexdigest()
    try:
        for sub in ('images','masks','annotations'): (staging/sub).mkdir()
        records=[];counts=[];borders=0
        with _archive(archives/'images.zip') as images, _archive(archives/'masks.zip') as masks:
            expected=set(metadata['plates'])
            for archive,folder,suffix in ((images,'images','.tif'),(masks,'masks','.png')):
                actual={Path(n).stem+'.png' for n in archive.namelist() if n.startswith(folder+'/') and n.endswith(suffix)}
                if actual!=expected: raise ValueError('Image/mask archive names disagree with metadata population')
            for filename in metadata['splits']['training']:
                stem=Path(filename).stem
                image_path='images/'+stem+'.tif';mask_path='masks/'+filename
                image_bytes=images.read(image_path);mask_bytes=masks.read(mask_path)
                with Image.open(io.BytesIO(image_bytes)) as image:
                    if image.format!='TIFF' or image.mode not in ('I;16','I;16L','I;16B') or getattr(image,'n_frames',1)!=1 or image.getexif().get(274,1)!=1:
                        raise ValueError('Source image must be a single native 16-bit TIFF with identity orientation')
                    if image.width*image.height>4_000_000: raise ValueError('Source image pixel ceiling exceeded')
                    image.load();size=image.size;extrema=image.convert('I').getextrema();mode=image.mode
                if (len(mask_bytes)<33 or mask_bytes[:8]!=b'\x89PNG\r\n\x1a\n' or
                        mask_bytes[8:16]!=b'\0\0\0\rIHDR' or mask_bytes[24]!=8 or mask_bytes[25] not in (2,6)):
                    raise ValueError('Source annotation must be an 8-bit RGB/RGBA PNG; reject precision loss')
                with Image.open(io.BytesIO(mask_bytes)) as mask:
                    if mask.format!='PNG' or mask.mode not in ('RGB','RGBA') or getattr(mask,'n_frames',1)!=1 or mask.size!=size or mask.getexif().get(274,1)!=1:
                        raise ValueError('Mask must be a same-frame RGB/RGBA PNG')
                    mask.load()
                    if 'transparency' in mask.info:
                        raise ValueError('Annotation mask carries transparency metadata')
                    if mask.mode=='RGBA' and mask.getchannel('A').getextrema()!=(255,255):
                        raise ValueError('Nonopaque annotation mask is ambiguous')
                    pixels=list(zip(*[mask.getchannel(channel).tobytes() for channel in ('R','G','B')]))
                    if any(r==0 and (g!=0 or b!=0) for r,g,b in pixels):
                        raise ValueError('Nonblack zero-red mask pixel makes source background interpretation ambiguous')
                    red=[r for r,g,b in pixels]
                    plane=[red[i:i+size[0]] for i in range(0,len(red),size[0])]
                annotations=decode_instances(plane)
                annotations.update({'image_sha256':digest(image_bytes),'mask_sha256':digest(mask_bytes),
                    'source_split':'training','source_plate':metadata['plates'][filename],
                    'image_mode':mode,'image_extrema':list(extrema),'review_status':'pending'})
                (staging/image_path).write_bytes(image_bytes);(staging/mask_path).write_bytes(mask_bytes)
                (staging/'annotations'/f'{stem}.json').write_text(json.dumps(annotations,indent=2)+'\n')
                counts.append(annotations['count']);borders+=sum(i['touches_border'] for i in annotations['instances'])
                common={'schema_version':1,'source_id':'bbbc039','source_version':'1','source_family':'bbbc',
                    'split':'engineering','source_split':'training','image_path':image_path,'image_sha256':digest(image_bytes),
                    'parent_image_sha256':None,'group_id':'plate:'+metadata['plates'][filename],
                    'image_width':size[0],'image_height':size[1],'context':{},
                    'annotation_origin':'source_RGB_mask_red_equal_8_connected_components',
                    'conversion_version':CONVERSION,'review_status':'pending','synthetic':False,
                    'mask_path':mask_path,'mask_sha256':digest(mask_bytes),'source_field_id':stem}
                records.append({**common,'record_id':stem+':count','task':'counting',
                    'question':'How many annotated nucleus instances are in this image?','answer':annotations['count']})
                if annotations['count']:
                    records.append({**common,'record_id':stem+':boxes','task':'detection',
                        'question':'Give tight xywh pixel boxes for all annotated nucleus instances in this image.',
                        'answer':[i['bbox_xywh'] for i in annotations['instances']]})
        report={'kind':'quarantined_source_training_conversion','training_ready':False,'model_executed':False,
            'images_inspected':len(counts),'pending_records':len(records),'nucleus_instances':sum(counts),
            'instance_count_range':[min(counts),max(counts)],'border_touching_instances':borders,
            'source_split_sizes':{k:len(v) for k,v in metadata['splits'].items()},
            'source_training_plates':len({metadata['plates'][n] for n in metadata['splits']['training']}),
            'plates_shared_across_source_splits':metadata['plates_shared_across_splits'],
            'decoder':CONVERSION,'heldout_image_and_mask_contents_opened':False,
            'archive_sha256':{name:digest((archives/name).read_bytes()) for name in ('images.zip','masks.zip','metadata.zip')},
            'remaining_checks':['MMBU source eligibility/overlap disposition','independent nucleus label review',
                '16-bit display/model processor policy','task and context ontology review','correlation-aware split design'],
            'warning':'Source plate groups are conservative lineage identifiers, not certified independent biological samples.'}
        (staging/'pending-records.jsonl').write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in records))
        (staging/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        (staging/'intake-report.json').write_text(json.dumps(report,indent=2)+'\n')
        if output.exists(): raise FileExistsError(str(output))
        staging.rename(output)
        return report
    finally:
        if staging.exists(): shutil.rmtree(staging)
