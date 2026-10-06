import datetime, hashlib, json, sys, traceback
from pathlib import Path
sys.path.insert(0,str(Path('outputs/mmbu-precompute/src').resolve()))
from mmbu_prep.acquisition import HTTPRangeReader,copy_zip_members
package=Path('outputs/mmbu-precompute')
shortlist=json.loads((package/'evidence/roco-shortlist.json').read_text())
reader=HTTPRangeReader('https://zenodo.org/api/records/10821435/files/train_images.zip/content',4611440786,block_size=262144,max_transfer_bytes=40*1024*1024,cache_blocks=32,timeout=60)
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
    result=copy_zip_members(reader,['train/'+r['source_image_id']+'.jpg' for r in shortlist],Path('work/roco-quarantine/acquired'))
    result.update(schema_version=1,retrieved_at_utc=start,completed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_id='rocov2',source_version='2.0.1',source_partition='train',selected_images=24,model_use_approved=False,publisher_expected_archive_md5='cd5f5fdb73f24cf6a7473319116a84cc',shortlist_sha256=hashlib.sha256((package/'evidence/roco-shortlist.json').read_bytes()).hexdigest(),acquisition_script_sha256=hashlib.sha256((package/'src/mmbu_prep/acquisition.py').read_bytes()).hexdigest())
    with (package/'evidence/roco-image-acquisition.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps({'members':len(result['members']),'http_bytes_received':reader.transferred_bytes,'payload_bytes':sum(x['bytes'] for x in result['members'])}),flush=True)
except Exception as e:
    failure={'started_at_utc':start,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error_type':type(e).__name__,'error':str(e),'completed_range_bytes':reader.transferred_bytes,'completed_ranges':reader.ranges,'partial_failed_range_bytes_unknown':True,'model_use_approved':False}
    with (package/'evidence/roco-image-acquisition-attempt2-failure.json').open('x') as f:json.dump(failure,f,indent=2)
    traceback.print_exc();sys.exit(1)
