import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

HAS_PIL = importlib.util.find_spec('PIL') is not None


def api():
    from mmbu_prep.bbbc039 import decode_instances, read_metadata, prepare_quarantine
    return decode_instances, read_metadata, prepare_quarantine


def zwrite(path, members):
    with zipfile.ZipFile(path, 'w') as z:
        for name, content in members.items():
            z.writestr(name, content)


class DecoderTests(unittest.TestCase):
    def test_equal_value_connectivity_not_unique_color_or_binary_foreground(self):
        decode, _, _ = api()
        # Two diagonal 1s join (8-connectivity); adjacent 2 stays distinct;
        # disconnected second 2 creates another instance. Zero is background.
        out = decode([[1, 2, 0, 2], [0, 1, 0, 0]])
        self.assertEqual(out['count'], 3)
        self.assertEqual(out['instances'], [
            {'instance_id': 1, 'red_value': 1, 'area_pixels': 2, 'bbox_xywh': [0, 0, 2, 2], 'touches_border': True},
            {'instance_id': 2, 'red_value': 2, 'area_pixels': 1, 'bbox_xywh': [1, 0, 1, 1], 'touches_border': True},
            {'instance_id': 3, 'red_value': 2, 'area_pixels': 1, 'bbox_xywh': [3, 0, 1, 1], 'touches_border': True}])

    def test_background_and_interior_boxes(self):
        decode, _, _ = api()
        self.assertEqual(decode([[0, 0]])['count'], 0)
        self.assertEqual(decode([[0,0,0],[0,7,0],[0,0,0]])['instances'][0],
            {'instance_id':1,'red_value':7,'area_pixels':1,'bbox_xywh':[1,1,1,1],'touches_border':False})

    def test_bad_planes_rejected(self):
        decode, _, _ = api()
        for plane in ([], [[]], [[1],[1,2]], [[-1]], [[256]], [[True]], [[1.5]]):
            with self.subTest(plane=plane), self.assertRaises(ValueError): decode(plane)


class MetadataTests(unittest.TestCase):
    def members(self):
        return {'metadata/training.txt':'a.png\n', 'metadata/validation.txt':'b.png\n',
                'metadata/test.txt':'c.png\n', 'metadata/filenames_and_plates.csv':'a.png,10\rb.png,10\rc.png,11\r'}

    def test_preserves_original_split_and_plate_mapping(self):
        _, read, _ = api()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.zip'; zwrite(p,self.members()); out=read(p)
        self.assertEqual(out['splits'],{'training':['a.png'],'validation':['b.png'],'test':['c.png']})
        self.assertEqual(out['plates'],{'a.png':'10','b.png':'10','c.png':'11'})
        self.assertEqual(out['plates_shared_across_splits'],['10'])

    def test_duplicate_overlap_paths_or_missing_plate_rejected(self):
        _, read, _ = api()
        variants=[]
        for key, value in [('metadata/training.txt','a.png\na.png\n'),('metadata/validation.txt','a.png\n'),
                           ('metadata/training.txt','../a.png\n'),('metadata/filenames_and_plates.csv','a.png,10\nb.png,10\n')]:
            m=self.members();m[key]=value;variants.append(m)
        with tempfile.TemporaryDirectory() as d:
            for m in variants:
                p=Path(d)/'m.zip';zwrite(p,m)
                with self.assertRaises(ValueError):read(p)

    def test_unsafe_archive_member_or_duplicate_member_rejected(self):
        _, read, _ = api()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'m.zip';m=self.members();m['../outside']='bad';zwrite(p,m)
            with self.assertRaises(ValueError):read(p)
            zwrite(p,self.members())
            with zipfile.ZipFile(p,'a') as z:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore');z.writestr('metadata/training.txt','a.png')
            with self.assertRaises(ValueError):read(p)


@unittest.skipUnless(HAS_PIL, 'optional Pillow dependency unavailable')
class IntakeTests(unittest.TestCase):
    def setup_archives(self, root, mismatch=False, colored_zero=False, alpha=None, transparency=None, big_endian=False):
        from PIL import Image
        image=Image.new('I;16',(3,2),1000)
        if big_endian:
            import struct
            image=Image.frombytes('I;16B',(3,2),struct.pack('>6H',0,1,256,1000,32768,65535))
        out=io.BytesIO();image.save(out,format='TIFF');image_bytes=out.getvalue()
        mask=Image.new('RGB',(4 if mismatch else 3,2))
        mask.putpixel((0,0),(0,20,0) if colored_zero else (9,8,7))
        if alpha is not None: mask.putalpha(alpha)
        out=io.BytesIO();mask.save(out,format='PNG',**({'transparency':transparency} if transparency is not None else {}))
        root.mkdir()
        zwrite(root/'metadata.zip', MetadataTests().members())
        # Poisoned held-out image/mask bytes prove they are never decoded.
        zwrite(root/'images.zip',{'images/a.tif':image_bytes,'images/b.tif':b'poison','images/c.tif':b'poison'})
        zwrite(root/'masks.zip',{'masks/a.png':out.getvalue(),'masks/b.png':b'poison','masks/c.png':b'poison'})
        return image_bytes

    def test_only_source_training_is_copied_and_annotations_remain_quarantined(self):
        _, _, prep = api()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);raw=self.setup_archives(root/'archives');out=root/'result'
            report=prep(root/'archives',out)
            self.assertFalse(report['training_ready']);self.assertEqual(report['images_inspected'],1)
            self.assertEqual((out/'images/a.tif').read_bytes(),raw)
            self.assertFalse((out/'images/b.tif').exists())
            rows=[json.loads(x) for x in (out/'pending-records.jsonl').read_text().splitlines()]
            self.assertEqual(len(rows),2);self.assertEqual(rows[0]['answer'],1)
            self.assertEqual(rows[1]['answer'],[[0,0,1,1]])
            self.assertEqual(rows[0]['source_split'],'training');self.assertEqual(rows[0]['review_status'],'pending')
            self.assertEqual(rows[0]['group_id'],'plate:10')
            self.assertEqual(rows[0]['split'],'engineering')
            self.assertEqual(json.loads((out/'annotations/a.json').read_text())['instances'][0]['area_pixels'],1)
            with self.assertRaises(FileExistsError):prep(root/'archives',out)

    def test_mismatch_and_nonblack_red_zero_fail_without_publishing_result(self):
        _, _, prep = api()
        for opts in ({'mismatch':True},{'colored_zero':True}):
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);self.setup_archives(root/'archives',**opts)
                with self.assertRaises(ValueError):prep(root/'archives',root/'result')
                self.assertFalse((root/'result').exists())

    def test_opaque_rgba_mask_preserves_red_semantics(self):
        _, _, prep=api()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup_archives(root/'archives',alpha=255)
            self.assertEqual(prep(root/'archives',root/'result')['nucleus_instances'],1)

    def test_transparent_mask_fails_ambiguous_display(self):
        _, _, prep=api()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup_archives(root/'archives',alpha=0)
            with self.assertRaises(ValueError):prep(root/'archives',root/'result')

    def test_rgb_transparency_metadata_cannot_bypass_opacity_check(self):
        _, _, prep=api()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup_archives(root/'archives',transparency=(9,8,7))
            with self.assertRaises(ValueError):prep(root/'archives',root/'result')
            self.assertFalse((root/'result').exists())

    def test_16_bit_mask_is_rejected_before_lossy_pillow_decode(self):
        import struct,zlib
        _, _, prep=api()
        def chunk(name,payload):
            return struct.pack('>I',len(payload))+name+payload+struct.pack('>I',zlib.crc32(name+payload)&0xffffffff)
        raw=b'\0'+struct.pack('>9H',256,0,0,257,0,0,0,0,0)+b'\0'+struct.pack('>9H',*([0]*9))
        payload=(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',3,2,16,2,0,0,0))+
                 chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);self.setup_archives(root/'archives')
            zwrite(root/'archives/masks.zip',{'masks/a.png':payload,'masks/b.png':b'poison','masks/c.png':b'poison'})
            with self.assertRaises(ValueError):prep(root/'archives',root/'result')
            self.assertFalse((root/'result').exists())

    def test_big_endian_native_16bit_image_preserves_bytes_and_extrema(self):
        _, _, prep=api()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);raw=self.setup_archives(root/'archives',big_endian=True)
            prep(root/'archives',root/'result')
            self.assertEqual((root/'result/images/a.tif').read_bytes(),raw)
            a=json.loads((root/'result/annotations/a.json').read_text())
            self.assertEqual(a['image_extrema'],[0,65535])
            self.assertEqual(a['image_mode'],'I;16B')
