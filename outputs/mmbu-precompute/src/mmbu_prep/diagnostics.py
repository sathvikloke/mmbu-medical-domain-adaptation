"""Development diagnostics over caller-supplied grades, without model selection."""

from collections import defaultdict

from .comparison import compare_candidates
from .metrics import TASKS, score_rows, source_balanced_weights


def diagnose_candidates(candidates, *, iterations=1000, seed=0, confidence=.95):
    """Natural, balanced and four predeclared task-stress mixtures.

    Counting stays an explicit diagnostic task, but joins global classification
    for the balanced proxy. Every scenario uses the same grades/population;
    scenario weights are mapped by record ID. No subset is silently intersected.
    """
    settings=dict(iterations=iterations,seed=seed,confidence=confidence)
    natural=compare_candidates(candidates,**settings)
    reference=candidates[natural['candidate_names'][0]]
    present={'global_classification' if r['task']=='counting' else r['task'] for r in reference}
    missing=[task for task in TASKS if task not in present]
    scenarios={'natural':natural}
    if not missing:
        mixtures={'balanced':dict.fromkeys(TASKS,.25)}
        mixtures.update({'stress_'+task:{other:.4 if other==task else .2 for other in TASKS} for task in TASKS})
        for name,mixture in mixtures.items():
            weights=source_balanced_weights(reference,task_weights=mixture)
            scenarios[name]=compare_candidates(candidates,weights={row['record_id']:w for row,w in zip(reference,weights)},**settings)
    breakdowns={}
    for field,label in [('task','by_task'),('source_id','by_source')]:
        breakdowns[label]={key:{name:score_rows([r for r in candidates[name] if r[field]==key])
                                    for name in natural['candidate_names']}
                           for key in sorted({r[field] for r in reference})}
    reversals=[]
    for index,pair in enumerate(natural['pairwise']):
        deltas={name:result['pairwise'][index]['delta_S'] for name,result in scenarios.items()}
        if min(deltas.values())<0<max(deltas.values()):
            reversals.append({'left':pair['left'],'right':pair['right'],'scenario_differences':deltas})
    return {'official_evaluation':False,'inference':'exploratory_sensitivity_not_model_selection',
            'full_task_coverage':not missing,'missing_task_groups':missing,'scenarios':scenarios,
            'rank_reversals':reversals,**breakdowns,
            'limits':['These mixtures are development assumptions, not inferred hidden-set weights.',
                      'Per-source/task scores use natural weights within the named subset and are descriptive.',
                      'No multiplicity adjustment, semantic judging or automatic checkpoint selection is performed.',
                      'Absence of a point-rank reversal does not establish superiority.']}


def _calibration_summary(rows):
    counts={'true_positive':0,'false_positive':0,'true_negative':0,'false_negative':0}
    keys={(1,1):'true_positive',(0,1):'false_positive',(0,0):'true_negative',(1,0):'false_negative'}
    for row in rows:counts[keys[row['human_grade'],row['judge_grade']]]+=1
    tp,fp,tn,fn=(counts[k] for k in ('true_positive','false_positive','true_negative','false_negative'))
    divide=lambda a,b:a/b if b else None
    return {'n':len(rows),'confusion':counts,'agreement':(tp+tn)/len(rows),
            'sensitivity':divide(tp,tp+fn),'specificity':divide(tn,tn+fp),
            'positive_predictive_value':divide(tp,tp+fp),'negative_predictive_value':divide(tn,tn+fn)}


def calibration_report(rows):
    """Summarize judge agreement with supplied human grades by sampling frame.

    Random and deliberately selected disagreement cases never share a pooled
    population statistic. This validates arithmetic, not reviewer expertise,
    randomness, blindness, ground-truth correctness, or sampling independence.
    """
    if not isinstance(rows,list) or not rows:raise ValueError('A nonempty calibration row list is required')
    seen=set();sampling=defaultdict(list);strata=defaultdict(lambda:defaultdict(list))
    for row in rows:
        if not isinstance(row,dict):raise ValueError('Each calibration row must be an object')
        for key in ('case_id','stratum'):
            if not isinstance(row.get(key),str) or not row[key].strip():raise ValueError(f'Missing/non-string {key}')
        if row['case_id'] in seen:raise ValueError('Duplicate calibration case_id')
        seen.add(row['case_id'])
        if row.get('sampling') not in ('random','targeted_disagreement'):raise ValueError('Unknown calibration sampling frame')
        for key in ('human_grade','judge_grade'):
            if type(row.get(key)) is not int or row[key] not in (0,1):raise ValueError('Calibration grades must be explicit integer 0/1; missing decisions cannot be dropped')
        sampling[row['sampling']].append(row);strata[row['sampling']][row['stratum']].append(row)
    return {'official_evaluation':False,'reference':'supplied_human_grades_not_certified_truth',
            'by_sampling':{name:_calibration_summary(part) for name,part in sorted(sampling.items())},
            'by_stratum':{name:{s:_calibration_summary(part) for s,part in sorted(groups.items())} for name,groups in sorted(strata.items())},
            'limits':['Sampling labels are supplied by the caller and are not verified.',
                      'No pooled random/targeted accuracy or population inference is reported.',
                      'High agreement alone does not validate medical correctness or candidate ranking.',
                      'Correlated records, sampling uncertainty and reviewer disagreement require separate review.']}
