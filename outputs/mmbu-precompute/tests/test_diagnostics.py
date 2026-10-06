import copy
import unittest
from mmbu_prep.metrics import TASKS


def api():
    from mmbu_prep.diagnostics import diagnose_candidates, calibration_report
    return diagnose_candidates, calibration_report


def candidates():
    rows=[]
    for task in TASKS:
        for n in range(10 if task==TASKS[0] else 2):
            rows.append(dict(record_id=f'{task}-{n}',source_id=task,group_id=str(n),task=task,
                base_correct=0,adapted_correct=int(task==TASKS[0]),context_correct={'modality':1}))
    b=copy.deepcopy(rows)
    for r in b:r['adapted_correct']=1-r['adapted_correct']
    return {'A':rows,'B':b}


class DiagnosticTests(unittest.TestCase):
    def test_reweighting_can_reverse_order_without_declaring_winner(self):
        diagnose,_=api();cs=candidates();original=copy.deepcopy(cs)
        result=diagnose(cs,iterations=200,seed=19)
        scenarios=result['scenarios']
        self.assertAlmostEqual(scenarios['natural']['pairwise'][0]['delta_S'],.25)
        self.assertAlmostEqual(scenarios['balanced']['pairwise'][0]['delta_S'],-.5)
        self.assertEqual(len(scenarios),6)
        self.assertEqual(result['rank_reversals'][0]['left'],'A')
        self.assertEqual(result['rank_reversals'][0]['right'],'B')
        self.assertEqual(result['by_task'][TASKS[0]]['A']['n_examples'],10)
        self.assertEqual(result['by_source'][TASKS[0]]['A']['T'],1)
        self.assertNotIn('winner',result);self.assertEqual(cs,original)

    def test_missing_task_groups_give_partial_diagnostics_not_fake_balanced_score(self):
        diagnose,_=api();cs={k:[r for r in rows if r['task']==TASKS[0]] for k,rows in candidates().items()}
        out=diagnose(cs,iterations=10)
        self.assertEqual(list(out['scenarios']),['natural'])
        self.assertFalse(out['full_task_coverage'])
        self.assertEqual(out['missing_task_groups'],list(TASKS[1:]))

    def test_misaligned_candidates_fail_before_subgroup_intersection(self):
        diagnose,_=api();cs=candidates();cs['B'].pop()
        with self.assertRaises(ValueError):diagnose(cs,iterations=10)

    def test_counting_groups_with_global_but_stays_separate_diagnostic(self):
        diagnose,_=api();cs=candidates()
        for rows in cs.values():rows[0]['task']='counting'
        out=diagnose(cs,iterations=10)
        self.assertTrue(out['full_task_coverage'])
        self.assertEqual(out['by_task']['counting']['A']['n_examples'],1)


class CalibrationTests(unittest.TestCase):
    def test_random_and_targeted_samples_are_not_pooled(self):
        _,calibrate=api()
        rows=[{'case_id':'r1','sampling':'random','stratum':'synonym','human_grade':1,'judge_grade':1},
              {'case_id':'r2','sampling':'random','stratum':'synonym','human_grade':0,'judge_grade':1},
              {'case_id':'r3','sampling':'random','stratum':'counting','human_grade':1,'judge_grade':0},
              {'case_id':'r4','sampling':'random','stratum':'counting','human_grade':0,'judge_grade':0},
              {'case_id':'t1','sampling':'targeted_disagreement','stratum':'counting','human_grade':1,'judge_grade':0}]
        out=calibrate(rows)
        self.assertEqual(out['by_sampling']['random']['agreement'],.5)
        self.assertEqual(out['by_sampling']['random']['confusion'],{'true_positive':1,'false_positive':1,'true_negative':1,'false_negative':1})
        self.assertEqual(out['by_sampling']['targeted_disagreement']['agreement'],0)
        self.assertEqual(out['by_sampling']['random']['sensitivity'],.5)
        self.assertEqual(out['by_sampling']['random']['specificity'],.5)
        self.assertNotIn('overall_agreement',out)

    def test_undefined_denominators_are_null(self):
        _,calibrate=api()
        out=calibrate([{'case_id':'a','sampling':'random','stratum':'label','human_grade':1,'judge_grade':1}])
        self.assertIsNone(out['by_sampling']['random']['specificity'])
        self.assertEqual(out['by_sampling']['random']['positive_predictive_value'],1)

    def test_bad_or_missing_grades_duplicate_ids_sampling_rejected(self):
        _,calibrate=api();row={'case_id':'a','sampling':'random','stratum':'label','human_grade':1,'judge_grade':1}
        for patch in ({'human_grade':None},{'judge_grade':True},{'sampling':'unknown'},{'stratum':''},{'judge_grade':float('nan')}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):calibrate([{**row,**patch}])
        for rows in ([],[row,row]):
            with self.assertRaises(ValueError):calibrate(rows)
