from pathlib import Path
import collections,copy,hashlib,importlib.util,json,shutil,sys,tempfile,zlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'outputs/mmbu-precompute';sys.path.insert(0,str(P/'src'))
from mmbu_prep.data import validate_manifest
SPEC=importlib.util.spec_from_file_location('sample_coordinator',P/'tools/prepare_roco_sample.py');M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
metadata=ROOT/'work/source-expansion';acquired=ROOT/'work/roco-quarantine/acquired';prepared=ROOT/'work/roco-quarantine/prepared'
receipt_path=P/'evidence/roco-image-acquisition.json';receipt=json.loads(receipt_path.read_text());short=json.loads((P/'evidence/roco-shortlist.json').read_text());results=[]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def hashes(folder):return {str(x.relative_to(folder)):sha(x) for x in sorted(folder.rglob('*')) if x.is_file()}
def rejected(name,fn,out):
    try:fn()
    except (ValueError,FileExistsError) as exc:
        assert not out.exists();results.append({'case':name,'status':'passed','rejection':str(exc)});return
    raise AssertionError('Unexpected acceptance: '+name)
before=hashes(acquired);prepared_before=hashes(prepared)
with tempfile.TemporaryDirectory() as temporary:
    temp=Path(temporary)
    replay=temp/'replay';summary=M.prepare(metadata,acquired,receipt,replay);replayed=hashes(replay)
    assert all(prepared_before.get(path)==digest for path,digest in replayed.items())
    rows=[json.loads(line) for line in (replay/'pending-manifest.jsonl').read_text().splitlines()]
    side=json.loads((replay/'source-metadata.json').read_text());side={r['source_image_id']:r for r in side}
    presentations=json.loads((replay/'presentations.json').read_text());presentations={r['source_image_id']:r for r in presentations}
    entries={r['member']:r for r in receipt['members']};by_short={r['source_image_id']:r for r in short}
    modes=collections.Counter()
    assert len(rows)==len(side)==len(presentations)==len(entries)==24
    for row in rows:
        sid=row['source_image_id'];raw=replay/'raw'/(sid+'.jpg');output=replay/row['image_path'];member=entries['train/'+sid+'.jpg'];pres=presentations[sid]
        assert row['source_partition']==row['split']=='train' and row['review_status']=='pending' and row['allowed_purposes']==[]
        assert row['group_id']==by_short[sid]['group_id'] and row['pmcid']==by_short[sid]['pmcid']
        assert row['answer']==by_short[sid]['modality_label'] and row['question']==by_short[sid]['proposed_question']
        assert side[sid]==by_short[sid] and side[sid]['metadata_only'] and 'image_not_acquired' in side[sid]['review_flags']
        assert raw.read_bytes()==(acquired/member['member']).read_bytes()
        assert len(raw.read_bytes())==member['bytes'] and sha(raw)==member['sha256']==pres['parent_image_sha256']==row['parent_image_sha256']
        assert f'{zlib.crc32(raw.read_bytes())&0xffffffff:08x}'==member['zip_crc32']
        assert sha(output)==pres['image_sha256']==row['image_sha256'] and pres['coordinate_transform']=='identity'
        with Image.open(raw) as source,Image.open(output) as result:
            modes[source.mode]+=1
            assert source.size==result.size==(row['image_width'],row['image_height'])
            assert result.mode=='RGB' and result.tobytes()==source.convert('RGB').tobytes()
        assert row['original_figure_id'] is None and row['source_metadata_path']=='source-metadata.json'
    gate=validate_manifest(rows,json.loads((P/'configs/source-registry.json').read_text()),image_root=replay,purpose='train')
    assert not gate['ok']
    gate_codes=dict(collections.Counter(x['code'] for x in gate['errors']))
    results.append({'case':'real_sample_replay_and_consistency','status':'passed','files_reproduced_identically':len(replayed),'records':24,'article_groups':len({r['group_id'] for r in rows}),'raw_modes':dict(modes),'model_use_gate_error_codes':gate_codes})
    bad=copy.deepcopy(receipt);bad['members'][0]['sha256']='0'*64;out=temp/'bad-hash'
    rejected('changed_member_hash',lambda:M.prepare(metadata,acquired,bad,out),out)
    bad=copy.deepcopy(receipt);bad['members'].pop();out=temp/'missing-receipt-member'
    rejected('missing_receipt_member',lambda:M.prepare(metadata,acquired,bad,out),out)
    bad=copy.deepcopy(receipt);bad['members'][1]=copy.deepcopy(bad['members'][0]);out=temp/'duplicate-receipt-member'
    rejected('duplicated_receipt_member',lambda:M.prepare(metadata,acquired,bad,out),out)
    try:M.prepare(metadata,acquired,receipt,prepared)
    except FileExistsError:results.append({'case':'existing_output_preserved','status':'passed'})
    else:raise AssertionError('Existing output not rejected')
    local=temp/'acquired';shutil.copytree(acquired,local);target=local/receipt['members'][0]['member'];source_bytes=target.read_bytes();target.unlink();out=temp/'missing-file'
    rejected('missing_acquired_file',lambda:M.prepare(metadata,local,receipt,out),out);target.write_bytes(source_bytes)
    target.write_bytes(b'X'+source_bytes[1:]);out=temp/'changed-file'
    rejected('changed_acquired_bytes',lambda:M.prepare(metadata,local,receipt,out),out);target.write_bytes(source_bytes)
    target.unlink();target.symlink_to(acquired/receipt['members'][0]['member']);out=temp/'source-symlink'
    rejected('source_member_symlink',lambda:M.prepare(metadata,local,receipt,out),out);target.unlink();target.write_bytes(source_bytes)
    Image.new('RGBA',(3,2),(1,2,3,255)).save(target,format='PNG');bad=copy.deepcopy(receipt);bad['members'][0]['bytes']=target.stat().st_size;bad['members'][0]['sha256']=sha(target);out=temp/'decode-failure'
    rejected('unsupported_presentation_after_staging',lambda:M.prepare(metadata,local,bad,out),out)
    assert not list(temp.glob('.roco-prepare-*'))
    target.write_bytes(source_bytes)
    altered=temp/'metadata';altered.mkdir()
    for name in ('train_concepts_manual.csv','train_captions.csv','license_information.csv','cui_mapping.csv'):shutil.copyfile(metadata/('roco-'+name),altered/name)
    with (altered/'train_captions.csv').open('a') as f:f.write('\n')
    out=temp/'metadata-change';rejected('changed_pinned_metadata_bytes',lambda:M.prepare(altered,acquired,receipt,out),out)
    # Contradictory high-level acquisition provenance must not be silently trusted.
    bad=copy.deepcopy(receipt);bad.update(source_id='different-source',source_version='99',source_partition='test',shortlist_sha256='0'*64,source_url='https://invalid.example/foreign.zip')
    out=temp/'contradictory-receipt'
    try:M.prepare(metadata,acquired,bad,out)
    except ValueError as exc:results.append({'case':'contradictory_receipt_provenance','status':'passed','rejection':str(exc)})
    else:raise AssertionError('Contradictory receipt provenance accepted')
    mutations={'schema_version':True,'source_id':'other','source_version':'99','source_partition':'test','selected_images':True,'source_url':'https://invalid.example/foreign.zip','expected_archive_bytes':True,'publisher_expected_archive_md5':'0'*32,'shortlist_sha256':'0'*64,'selected_member_crc_verified':1,'whole_archive_checksum_verified':0,'model_use_approved':0}
    for key,value in mutations.items():
        bad=copy.deepcopy(receipt);bad[key]=value;out=temp/('receipt-field-'+key)
        rejected('contradictory_or_wrong_type_receipt_'+key,lambda:M.prepare(metadata,acquired,bad,out),out)
assert hashes(acquired)==before and hashes(prepared)==prepared_before
report={'schema_version':1,'results':results,'sources_and_existing_output_unchanged':True,'coordinator_sha256':sha(P/'tools/prepare_roco_sample.py'),'acquisition_receipt_sha256':sha(receipt_path),'shortlist_sha256':sha(P/'evidence/roco-shortlist.json'),'script_sha256':sha(Path(__file__)),'production_code_modified':False,'model_use_approval':False,'network_requests':0}
(P/'evidence/roco-sample-independent-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
