from pathlib import Path
import argparse, contextlib, copy, hashlib, importlib.util, io, json, math, os, socket, sys, tempfile, urllib.request
from fractions import Fraction
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'outputs/mmbu-precompute';sys.path[:0]=[str(P/'tools'),str(P/'src')]
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
import source_processor_probe as S
from mmbu_prep.contracts import build_task_input
report_path=P/'evidence/source-processor-final-v2.json'
r=json.loads(report_path.read_text());manifest=ROOT/'work/roco-quarantine/prepared/pending-manifest.jsonl';image_root=manifest.parent
rows=[json.loads(x) for x in manifest.read_text().splitlines()];by_id={x['record_id']:x for x in rows};checks=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def file_sha(p):return sha(p.read_bytes())
assert len(rows)==len(by_id)==r['record_count']==24 and r['status']=='passed'
assert r['manifest_sha256']==file_sha(manifest)
assert r['registry_sha256']==file_sha(P/'evidence/source-processor-registry.json')
for path,digest in r['code_sha256'].items():assert file_sha(P/path)==digest,(path,'stale code')
assert r['network_guards']['attempted_calls']==0 and r['input_manifest_registry_and_png_bytes_unchanged']
for key in ('model_executed','optimization_performed','evaluation_performed','source_use_approved','source_status_changed','gpu_used'):assert r[key] is False
checks.append({'case':'report_code_input_pins_and_status_scope','status':'passed'})
from PIL import Image
actual={}
for row in rows:
 path=image_root/row['image_path'];payload=path.read_bytes();assert sha(payload)==row['image_sha256']
 with Image.open(io.BytesIO(payload)) as im:
  assert im.mode=='RGB' and im.format=='PNG' and getattr(im,'n_frames',1)==1 and im.getexif().get(274) in (None,1) and 'transparency' not in im.info
  header={'version':'pillow-decoded-representation-v1','width':im.width,'height':im.height,'mode':'RGB','bands':['R','G','B'],'storage_order':'mode-defined','palette':None,'transparency':{'type':'NoneType','value':None}}
  parts=[json.dumps(header,sort_keys=True,separators=(',',':')).encode(),b'',im.tobytes()]
  pixel=sha(b''.join(len(part).to_bytes(8,'big')+part for part in parts))
  actual[row['record_id']]={'raw':sha(payload),'pixel':pixel,'hw':[im.height,im.width]}
checks.append({'case':'24_actual_png_and_independent_decoded_digest_checks','status':'passed','count':24})
summary_checks=0
for model in r['models']:
 assert model['status']=='passed'
 config=model['native_image_processor_config'];merge=config['merge_size'];patch_size=config['patch_size']
 assert set(model['policies'])=={'native_default','common_area_65536_262144'}
 for policy,data in model['policies'].items():
  assert data['status']=='passed' and len(data['records'])==24 and {x['record_id'] for x in data['records']}==set(by_id)
  assert data['summary']['expected_records']==data['summary']['success_count']==24 and data['summary']['failure_count']==0
  for entry in data['records']:
   row=by_id[entry['record_id']];a=actual[entry['record_id']]
   assert entry['status']=='passed' and entry['excluded_fields_invariant'] and all(entry['checks'].values())
   assert entry['image_path']==row['image_path'] and entry['actual_png_sha256']==a['raw'] and entry['pixel_sha256']==a['pixel'] and entry['original_hw']==a['hw']
   assert entry['review_status']=='pending' and entry['allowed_purposes']==[]
   n=sum(math.prod(grid)//merge**2 for grid in entry['image_grid_thw'])
   assert n==entry['image_token_count']==entry['grid_token_count']==entry['visual_tokens']
   assert entry['resized_hw_from_grid']==[[grid[1]*patch_size,grid[2]*patch_size] for grid in entry['image_grid_thw']]
   assert entry['input_tokens']==entry['arrays']['input_ids']['shape'][1] and entry['nonvisual_input_tokens_including_template']==entry['input_tokens']-n
   assert entry['arrays']['attention_mask']['min']==entry['arrays']['attention_mask']['max']==1
   rendered=data['rendered_prompts'][entry['rendered_prompt_sha256']];assert sha(rendered.encode())==entry['rendered_prompt_sha256']
   assert 'EXCLUDED_REFERENCE_SENTINEL_729' not in rendered and row['question'] in rendered
  for field in ('visual_tokens','input_tokens','nonvisual_input_tokens_including_template'):
   values=sorted(x[field] for x in data['records']);n=len(values);s=data['summary'][field]
   assert [s['n'],s['min'],s['max'],s['total']]==[n,values[0],values[-1],sum(values)]
   expected={'mean':Fraction(sum(values),n)}
   for name,q in [('p50',Fraction(1,2)),('p90',Fraction(9,10)),('p95',Fraction(19,20))]:
    index=(n-1)*q;low=index.numerator//index.denominator;high=math.ceil(index)
    expected[name]=values[low]+(values[high]-values[low])*(index-low)
   for key,val in expected.items():assert math.isclose(float(val),s[key],rel_tol=1e-14,abs_tol=1e-12),(field,key,val,s[key])
   summary_checks+=1
checks.append({'case':'144_record_grid_hash_and_18_exact_arithmetic_summary_checks','status':'passed','records':144,'summaries':summary_checks})
rejected=0
for text in ('{"a":1,"a":2}','{"n":NaN}','{"n":Infinity}','{"n":-Infinity}','{"n":1e309}','{"n":-1e309}'):
 try:S.strict_json(text)
 except ValueError:rejected+=1
 else:raise AssertionError('strict JSON accepted '+text)
assert S.strict_json('{"n":1e308}')['n']==1e308
checks.append({'case':'duplicate_keys_nonfinite_and_exponent_overflow','status':'passed','rejections':rejected})
class ObservedFile:
 def __init__(self,data):self.data=data;self.requested=[]
 def open(self,mode):
  assert mode=='rb'
  owner=self
  class Stream:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def read(self,n):owner.requested.append(n);return owner.data[:n]
  return Stream()
for size in (127,128,129,1000):
 fixture=ObservedFile(b'X'*size)
 try:payload=S.bounded_read(fixture,128)
 except ValueError:assert size>128
 else:assert size<=128 and payload==b'X'*size
 assert fixture.requested==[129]
checks.append({'case':'bounded_reader_limit_plus_one_and_inclusive_limit','status':'passed','fixtures':4})
with S.denied_network() as attempts:
 for fn in (lambda:socket.create_connection(('invalid.example',80)),lambda:socket.getaddrinfo('invalid.example',80),lambda:socket.socket().connect(('127.0.0.1',9)),lambda:socket.socket().connect_ex(('127.0.0.1',9)),lambda:urllib.request.urlopen('https://invalid.example')):
  try:fn()
  except RuntimeError:pass
  else:raise AssertionError('network hook did not deny')
 assert len(attempts)==5
checks.append({'case':'five_network_entrypoint_guards','status':'passed','blocked_calls':5})
# Native replay uses actual cached processors and direct calls, not encode_case.
with S.denied_network() as attempts:
 import torch
 from transformers import AutoProcessor
 torch.set_num_threads(1)
 native=[]
 for model in r['models']:
  directory=ROOT/'work/processor-probe/artifacts'/model['model_id'].replace('/','--')/model['revision']
  processor=AutoProcessor.from_pretrained(directory,local_files_only=True,trust_remote_code=False)
  row=rows[0];selected=build_task_input(row,S.SYSTEM_PROMPT)
  messages=S.helpers.make_messages(selected)
  prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
  poisoned=copy.deepcopy(row)
  for key in ('answer','options','context','caption','raw_caption','pmcid','source_id','source_image_id','record_id','history','messages','previous_prediction'):poisoned[key]={'hostile':'REFERENCE_EXCLUSION_PROBE'}
  assert processor.apply_chat_template(S.helpers.make_messages(build_task_input(poisoned,S.SYSTEM_PROMPT)),tokenize=False,add_generation_prompt=True)==prompt
  for policy,kwargs in r['policies'].items():
   ref=model['policies'][policy]['records'][0]
   with Image.open(image_root/row['image_path']) as im:
    enc=processor(text=[prompt],images=[im],return_tensors='pt',device='cpu',padding=False,truncation=False,**kwargs)
   assert set(enc)==set(ref['arrays'])
   for key,value in enc.items():
    arr=value.detach().cpu().numpy()
    assert str(value.device)=='cpu' and list(arr.shape)==ref['arrays'][key]['shape'] and str(arr.dtype)==ref['arrays'][key]['dtype'] and sha(arr.tobytes())==ref['arrays'][key]['sha256'],(model['model_id'],policy,key)
   native.append({'model':model['model_id'],'policy':policy,'input_tokens':int(enc['input_ids'].shape[1]),'all_tensor_hashes_equal':True})
 assert not attempts
checks.append({'case':'six_independent_cached_native_encodings_and_poisoned_input_invariance','status':'passed','replays':native,'network_attempts':0})
result={'schema_version':1,'status':'passed','checks':checks,'report_sha256':file_sha(report_path),'script_sha256':file_sha(Path(__file__)),'source_script_sha256':file_sha(P/'tools/source_processor_probe.py'),'manifest_sha256':file_sha(manifest),'production_modified':False,'model_execution':False,'gpu_used':False,'source_use_approval':False}
(P/'evidence/source-processor-independent-probes.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
