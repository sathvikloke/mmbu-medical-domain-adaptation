import importlib.util
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class Batch2CliTests(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-m','mmbu_prep',*args],cwd=ROOT,
            env={**os.environ,'PYTHONPATH':str(ROOT/'src')},text=True,capture_output=True,timeout=30)

    def test_compare_aligned_supplied_grades_and_no_winner_claim(self):
        rows=[json.loads(x) for x in (ROOT/'examples/pregraded-toy.jsonl').read_text().splitlines()]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'candidates.json';p.write_text(json.dumps({'a':rows,'b':list(reversed(rows))}))
            out=self.run_cli('compare',str(p),'--bootstrap','200','--seed','9')
            self.assertEqual(out.returncode,0,out.stderr)
            result=json.loads(out.stdout)
            self.assertFalse(result['official_evaluation'])
            self.assertEqual(result['comparison']['pairwise'][0]['delta_S'],0)
            self.assertEqual(result['comparison']['pairwise'][0]['interval'],[0,0])

    def test_bad_comparison_alignment_returns_json_error(self):
        rows=[json.loads(x) for x in (ROOT/'examples/pregraded-toy.jsonl').read_text().splitlines()]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'candidates.json';p.write_text(json.dumps({'a':rows,'b':rows[:-1]}))
            out=self.run_cli('compare',str(p))
            self.assertEqual(out.returncode,2)
            self.assertIn('error',json.loads(out.stderr))

    @unittest.skipUnless(importlib.util.find_spec('PIL'), 'optional Pillow unavailable')
    def test_images_decodes_shipped_fixtures(self):
        out=self.run_cli('inspect-images','examples/engineering-manifest.jsonl','--image-root','examples')
        self.assertEqual(out.returncode,0,out.stdout+out.stderr)
        self.assertTrue(json.loads(out.stdout)['ok'])

    def test_missing_intake_archive_returns_json_error(self):
        with tempfile.TemporaryDirectory() as d:
            out=self.run_cli('prepare-bbbc039',str(Path(d)/'missing'),'--output',str(Path(d)/'result'))
            self.assertEqual(out.returncode,2)
            self.assertIn('error',json.loads(out.stderr))
            self.assertFalse((Path(d)/'result').exists())
