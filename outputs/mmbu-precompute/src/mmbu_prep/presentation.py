"""Explicit native-frame RGB presentation; never chooses a medical display policy."""
import hashlib
from io import BytesIO
from pathlib import Path


def present_image(input_path, output_path, *, window=None):
    """Create a new RGB PNG with an auditable intensity recipe and identity frame.

    RGB8/L8 are preserved/replicated. Native uint16 grayscale requires an explicit
    integer [black,white] window; floats, transparency and orientation transforms
    are rejected. This helper does not approve a source or a window choice.
    """
    from .images import inspect_images
    input_path,output_path=Path(input_path),Path(output_path)
    if output_path.exists():raise FileExistsError(str(output_path))
    if input_path.stat().st_size>67_108_864:raise ValueError('Input exceeds encoded image byte ceiling')
    raw=input_path.read_bytes();parent=hashlib.sha256(raw).hexdigest()
    check=inspect_images([{'record_id':'presentation','source_id':'caller','split':'engineering',
        'image_path':input_path.name,'image_sha256':parent}],image_root=input_path.parent)
    if not check['ok']:raise ValueError('Source image inspection failed: '+str(check['errors']))
    info=check['images'][0]
    if info['orientation_requires_transform']:raise ValueError('Nonidentity orientation needs separately reviewed coordinate conversion')
    from PIL import Image
    with Image.open(BytesIO(raw)) as image:
        if 'transparency' in image.info:raise ValueError('Image transparency needs an explicit compositing policy')
        mode=image.mode;size=image.size;image.load();low=high=0
        if mode in ('RGB','L'):
            if window is not None:raise ValueError('Intensity window applies only to native uint16 grayscale')
            rendered=image.convert('RGB');recipe='rgb8_identity' if mode=='RGB' else 'gray8_channel_replication'
        elif mode in ('I;16','I;16L','I;16B'):
            if not isinstance(window,(tuple,list)) or len(window)!=2 or any(type(x) is not int for x in window) or not 0<=window[0]<window[1]<=65535:
                raise ValueError('Native uint16 requires explicit integer window 0<=black<white<=65535')
            black,white=window;values=list(image.convert('I').get_flattened_data())
            low=sum(v<black for v in values);high=sum(v>white for v in values);span=white-black
            mapped=[0 if v<=black else 255 if v>=white else ((v-black)*255+span//2)//span for v in values]
            gray=Image.new('L',size);gray.putdata(mapped);rendered=gray.convert('RGB');recipe='uint16_explicit_linear_window_round_half_up'
        else:raise ValueError('Only RGB8, grayscale8 or explicitly windowed native uint16 is supported')
    encoded=BytesIO();rendered.save(encoded,format='PNG',compress_level=9);payload=encoded.getvalue()
    output_path.parent.mkdir(parents=True,exist_ok=True)
    with output_path.open('xb') as stream:stream.write(payload)
    return {'parent_image_sha256':parent,'image_sha256':hashlib.sha256(payload).hexdigest(),
            'source_mode':mode,'output_mode':'RGB','width':size[0],'height':size[1],
            'coordinate_transform':'identity','recipe':recipe,'window':list(window) if window is not None else None,
            'clipped_low_pixels':low,'clipped_high_pixels':high,'pixels':size[0]*size[1],
            'source_or_presentation_approved':False,'output_path':str(output_path)}
