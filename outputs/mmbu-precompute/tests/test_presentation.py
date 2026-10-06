import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


def api():
    from mmbu_prep.presentation import present_image
    return present_image


@unittest.skipUnless(importlib.util.find_spec('PIL'),'optional Pillow unavailable')
class PresentationTests(unittest.TestCase):
    def test_16bit_requires_explicit_window_then_maps_without_changing_frame(self):
        from PIL import Image
        import struct
        present=api()
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);raw=d/'raw.tif';out=d/'rgb.png'
            Image.frombytes('I;16',(5,1),struct.pack('<5H',0,256,512,1023,65535)).save(raw)
            old=hashlib.sha256(raw.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):present(raw,out)
            self.assertFalse(out.exists())
            receipt=present(raw,out,window=(0,1023))
            with Image.open(out) as im:
                self.assertEqual(im.mode,'RGB');self.assertEqual(im.size,(5,1))
                self.assertEqual(list(im.get_flattened_data()),[(0,0,0),(64,64,64),(128,128,128),(255,255,255),(255,255,255)])
            self.assertEqual(receipt['clipped_high_pixels'],1)
            self.assertEqual(receipt['parent_image_sha256'],old)
            self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),old)
            with self.assertRaises(FileExistsError):present(raw,out,window=(0,1023))

    def test_rgb_sample_values_survive_png_output(self):
        from PIL import Image
        present=api()
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);Image.new('RGB',(2,2),(3,5,7)).save(d/'raw.png')
            receipt=present(d/'raw.png',d/'out.png')
            with Image.open(d/'out.png') as im:self.assertEqual(im.getpixel((0,0)),(3,5,7))
            self.assertEqual(receipt['coordinate_transform'],'identity')

    def test_float_orientation_transparency_and_bad_windows_rejected(self):
        from PIL import Image
        present=api()
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);Image.new('F',(2,2),.5).save(d/'float.tif')
            Image.new('RGBA',(2,2),(1,2,3,0)).save(d/'alpha.png')
            Image.new('I;16',(2,2),100).save(d/'int.tif')
            im=Image.new('RGB',(2,2));exif=Image.Exif();exif[274]=6;im.save(d/'orient.png',exif=exif)
            for name in ('float.tif','alpha.png','orient.png'):
                with self.assertRaises(ValueError):present(d/name,d/'out.png')
            for window in ((0,0),(-1,4),(0,65536),(True,400),(0,4.5)):
                with self.assertRaises(ValueError):present(d/'int.tif',d/'out.png',window=window)
