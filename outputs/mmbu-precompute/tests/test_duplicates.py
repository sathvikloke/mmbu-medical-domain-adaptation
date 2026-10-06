import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
try:
    from PIL import Image, ImageEnhance
except ImportError:
    Image = None
from mmbu_prep.duplicates import triage_duplicates

@unittest.skipIf(Image is None, 'Pillow is optional')
class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.rows=[]
    def tearDown(self):self.tmp.cleanup()
    def add(self,name,image,split='train'):
        p=self.root/(name+'.png');image.save(p)
        self.rows.append(dict(record_id=name,source_id='fixture',split=split,image_path=p.name,image_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    def shape(self):
        p=Image.new('L',(144,128));p.putdata([int((x//18%2)*120+y//2) for y in range(128) for x in range(144)]);return p
    def test_resize_brightness_candidates_without_merge(self):
        a=self.shape();self.add('a',a);self.add('b',ImageEnhance.Brightness(a.resize((288,256))).enhance(.8),'dev')
        r=triage_duplicates(self.rows,image_root=self.root)
        self.assertEqual(len(r['candidates']),1);self.assertTrue(r['candidates'][0]['cross_split']);self.assertFalse(r['automatic_merge_or_exclusion'])
    def test_uniform_hash_collision_is_marked_weak(self):
        self.add('black',Image.new('RGB',(32,32),'black'));self.add('white',Image.new('RGB',(32,32),'white'))
        r=triage_duplicates(self.rows,image_root=self.root)
        self.assertEqual(r['candidates'][0]['reason'],'weak_hash_requires_review');self.assertFalse(r['candidates'][0]['exact_raw_match'])
    def test_aspect_filter(self):
        self.add('a',self.shape());self.add('b',self.shape().resize((144,64)))
        self.assertEqual(triage_duplicates(self.rows,image_root=self.root)['candidates'],[])
    def test_inclusive_aspect_boundary(self):
        self.add('a',Image.new('L',(19,20),0));self.add('b',Image.new('L',(20,20),255))
        result=triage_duplicates(self.rows,image_root=self.root,max_aspect_ratio_difference=.05)
        self.assertEqual(len(result['candidates']),1)
        self.assertEqual(result['candidates'][0]['relative_aspect_difference'],.05)
    def test_native16_rejected(self):
        self.add('native',Image.new('I;16',(32,32),32768))
        with self.assertRaisesRegex(ValueError,'RGB8 or L8'):triage_duplicates(self.rows,image_root=self.root)
    def test_hash_tampering_fails(self):
        self.add('a',self.shape());self.rows[0]['image_sha256']='0'*64
        with self.assertRaises(ValueError):triage_duplicates(self.rows,image_root=self.root)
    def test_bounds(self):
        for kwargs in ({'max_distance':True},{'max_distance':65},{'max_aspect_ratio_difference':float('nan')},{'max_images':0}):
            with self.assertRaises(ValueError):triage_duplicates([],image_root=self.root,**kwargs)
    def test_readonly_deterministic(self):
        self.add('a',self.shape());before=repr(self.rows);a=triage_duplicates(self.rows,image_root=self.root);b=triage_duplicates(self.rows,image_root=self.root)
        self.assertEqual(a,b);self.assertEqual(before,repr(self.rows))
    def test_change_after_inspection_fails(self):
        from mmbu_prep.images import inspect_images
        self.add('a',self.shape())
        def changed(*args,**kwargs):
            result=inspect_images(*args,**kwargs)
            Image.new('L',(144,128),0).save(self.root/'a.png')
            return result
        with patch('mmbu_prep.duplicates.inspect_images',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'changed after inspection'):
                triage_duplicates(self.rows,image_root=self.root)
