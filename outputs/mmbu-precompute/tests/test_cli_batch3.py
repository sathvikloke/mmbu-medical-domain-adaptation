import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class Batch3CliTests(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-m','mmbu_prep',*args],cwd=ROOT,
            env={**os.environ,'PYTHONPATH':str(ROOT/'src')},text=True,capture_output=True,timeout=30)

    def test_diagnostics_keep_partial_coverage_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            full=json.loads((ROOT/'examples/candidate-grades-toy.json').read_text())
            partial={name:[r for r in rows if r['task']=='global_classification'] for name,rows in full.items()}
            path=Path(d)/'partial.json';path.write_text(json.dumps(partial))
            out=self.run_cli('diagnose',str(path),'--bootstrap','10')
        self.assertEqual(out.returncode,0,out.stderr)
        result=json.loads(out.stdout)
        self.assertFalse(result['official_evaluation'])
        self.assertFalse(result['full_task_coverage'])
        self.assertEqual(set(result['scenarios']),{'natural'})

    def test_calibration_keeps_selected_disagreements_out_of_random_summary(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'grades.json';p.write_text(json.dumps([
                dict(case_id='a',sampling='random',stratum='counting',human_grade=1,judge_grade=1),
                dict(case_id='b',sampling='targeted_disagreement',stratum='counting',human_grade=1,judge_grade=0)]))
            out=self.run_cli('calibrate',str(p));self.assertEqual(out.returncode,0,out.stderr)
            self.assertEqual(json.loads(out.stdout)['by_sampling']['random']['agreement'],1)

    def test_bad_calibration_is_structured_error(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json';p.write_text('[{"case_id":"a"}]')
            out=self.run_cli('calibrate',str(p));self.assertEqual(out.returncode,2)
            self.assertIn('error',json.loads(out.stderr))

    def test_artifact_receipt_cli_detects_local_drift(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'input.txt').write_text('original')
            receipt=root/'receipt.json'
            made=self.run_cli('receipt-create','--artifact-root',str(root),'--select','input.txt','--output',str(receipt))
            self.assertEqual(made.returncode,0,made.stderr)
            anchor=json.loads(made.stdout)['receipt_sha256']
            good=self.run_cli('receipt-verify',str(receipt),'--artifact-root',str(root),'--expected-sha256',anchor)
            self.assertEqual(good.returncode,0,good.stderr)
            (root/'input.txt').write_text('drift')
            bad=self.run_cli('receipt-verify',str(receipt),'--artifact-root',str(root),'--expected-sha256',anchor)
            self.assertEqual(bad.returncode,2)
            self.assertEqual(json.loads(bad.stdout)['changed'],['input.txt'])

    def test_synthetic_confirmation_cli_lifecycle_and_retained_anchors(self):
        from test_experiments import fixture
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);record=fixture(root);path=root/'record.json';path.write_text(json.dumps(record))
            valid=self.run_cli('experiment-validate',str(path),'--artifact-root',str(root))
            self.assertEqual(valid.returncode,0,valid.stderr)
            frozen=self.run_cli('confirmation-freeze',str(path),'--artifact-root',str(root),'--store',str(root/'ledgers'),'--time','2026-10-04T10:01:00Z')
            self.assertEqual(frozen.returncode,0,frozen.stderr)
            f=json.loads(frozen.stdout);ledger=f['ledger_path'];anchor=f['event_sha256']
            opened=self.run_cli('confirmation-open',ledger,'--artifact-root',str(root),'--freeze-sha256',anchor,'--latest-sha256',anchor,'--time','2026-10-04T10:02:00Z')
            self.assertEqual(opened.returncode,0,opened.stderr)
            current=json.loads(opened.stdout)['event_sha256']
            (root/'result.json').write_text('{"synthetic_only":true}')
            saved=self.run_cli('confirmation-result',ledger,'result.json','--artifact-root',str(root),'--freeze-sha256',anchor,'--latest-sha256',current,'--time','2026-10-04T10:03:00Z')
            self.assertEqual(saved.returncode,0,saved.stderr)
            current=json.loads(saved.stdout)['event_sha256']
            checked=self.run_cli('confirmation-verify',ledger,'--artifact-root',str(root),'--freeze-sha256',anchor,'--latest-sha256',current)
            self.assertEqual(checked.returncode,0,checked.stderr)
            retired=self.run_cli('confirmation-retire',ledger,'--freeze-sha256',anchor,'--latest-sha256',current,'--reason','Synthetic test of result-informed retirement','--time','2026-10-04T10:04:00Z')
            self.assertEqual(retired.returncode,0,retired.stderr)
            self.assertEqual(json.loads(retired.stdout)['status'],'retired_to_development')
