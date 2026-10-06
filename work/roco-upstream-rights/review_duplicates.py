from pathlib import Path
import collections,copy,hashlib,json,os,subprocess,sys,tempfile
from unittest.mock import patch
from PIL import Image,PngImagePlugin
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'outputs/mmbu-precompute';sys.path.insert(0,str(P/'src'))
import mmbu_prep.duplicates as D
results=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def add(root,name,image,split='train',pnginfo=None):
    p=root/(name+'.png');image.save(p,pnginfo=pnginfo) if pnginfo else image.save(p)
    return {'record_id':name,'source_id':'original-synthetic-fixture','split':split,'image_path':p.name,'image_sha256':digest(p)}
def image_bits(bits):
    values=[]
    for y in range(8):
        row=[128]
        for bit in bits[y*8:y*8+8]:row.append(row[-1]-1 if bit else row[-1]+1)
        values.extend(row)
    image=Image.new('L',(9,8));image.putdata(values);return image

def reject(fn):
    try:fn()
    except ValueError as exc:return str(exc)
    raise AssertionError('Expected rejection')
with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    first=[False]*64;first[0]=True;last=[False]*64;last[-1]=True
    rows=[add(root,'first-bit',image_bits(first)),add(root,'last-bit',image_bits(last))]
    out=D.triage_duplicates(rows,image_root=root,max_distance=2)
    assert [x['dhash64'] for x in out['images']]==['8000000000000000','0000000000000001']
    assert out['candidates'][0]['hamming_distance']==2 and out['candidates'][0]['reason']=='weak_hash_requires_review'
    assert D.triage_duplicates(rows,image_root=root,max_distance=1)['candidates']==[]
    results.append({'case':'strict_horizontal_order_and_hamming_boundary','status':'passed'})
    bits=[i%2==0 for i in range(64)];four=bits.copy();five=bits.copy()
    for i in range(4):four[i]=not four[i]
    for i in range(5):five[i]=not five[i]
    rows=[add(root,'base',image_bits(bits)),add(root,'flip4',image_bits(four)),add(root,'flip5',image_bits(five))]
    out=D.triage_duplicates(rows,image_root=root)
    pairs={tuple(x['record_ids']):x['hamming_distance'] for x in out['candidates']}
    assert pairs=={('base','flip4'):4,('flip4','flip5'):1}
    assert all(x['reason']=='perceptual_candidate_requires_review' for x in out['candidates'])
    results.append({'case':'default_distance_four_inclusive_five_excluded','status':'passed'})
    # Exactly 5% relative aspect difference: 19/20 versus 20/20.
    rows=[add(root,'aspect19',Image.new('L',(19,20),0)),add(root,'aspect20',Image.new('L',(20,20),255))]
    out=D.triage_duplicates(rows,image_root=root)
    results.append({'case':'aspect_exact_five_percent_inclusive','status':'passed' if len(out['candidates'])==1 else 'failed','candidate_count':len(out['candidates']),'expected_exact_relative_difference':0.05,'float_ratio_subtraction':abs(19/20-20/20)/max(19/20,20/20)})
    pnginfo=PngImagePlugin.PngInfo();pnginfo.add_text('encoding-only','different bytes')
    a=add(root,'same-pixels-a',image_bits(bits));b=add(root,'same-pixels-b',image_bits(bits),pnginfo=pnginfo)
    out=D.triage_duplicates([a,b],image_root=root);pair=out['candidates'][0]
    assert pair['exact_decoded_match'] and not pair['exact_raw_match'] and pair['reason']=='exact_decoded_match'
    b['split']='dev';error=reject(lambda:D.triage_duplicates([a,b],image_root=root));assert 'decoded_split_leakage' in error
    results.append({'case':'same_split_reencoding_and_cross_split_exact_prerequisite_failure','status':'passed'})
    # Prove the hash represents the same bytes that the inspection receipt names.
    a=add(root,'race',image_bits(bits));path=root/a['image_path'];original=path.read_bytes();real_inspect=D.inspect_images
    def changed_after_inspection(*args,**kwargs):
        inspected=real_inspect(*args,**kwargs);Image.new('L',(9,8),0).save(path);return inspected
    with patch.object(D,'inspect_images',side_effect=changed_after_inspection):
        try:out=D.triage_duplicates([a],image_root=root)
        except ValueError as exc:results.append({'case':'file_changed_after_inspection','status':'passed','rejection':str(exc)})
        else:results.append({'case':'file_changed_after_inspection','status':'failed','claimed_raw_sha256':out['images'][0]['raw_sha256'],'current_raw_sha256':digest(path),'fingerprint':out['images'][0]['dhash64'],'problem':'Fingerprint was calculated from replacement bytes but attributed to old inspection SHA.'})
    path.write_bytes(original)
    invalid_count=0
    for mode,value in [('I;16',256),('P',1),('RGBA',(1,2,3,255)),('LA',(1,255))]:
        row=add(root,'mode-'+mode.replace(';','-'),Image.new(mode,(9,8),value));reject(lambda:D.triage_duplicates([row],image_root=root));invalid_count+=1
    p=root/'orientation.png';exif=Image.Exif();exif[274]=6;Image.new('RGB',(9,8)).save(p,exif=exif);row={'record_id':'orientation','source_id':'fixture','split':'train','image_path':p.name,'image_sha256':digest(p)}
    reject(lambda:D.triage_duplicates([row],image_root=root));invalid_count+=1
    p=root/'transparent.png';Image.new('L',(9,8),0).save(p,transparency=0);row={'record_id':'transparency','source_id':'fixture','split':'train','image_path':p.name,'image_sha256':digest(p)}
    reject(lambda:D.triage_duplicates([row],image_root=root));invalid_count+=1
    for options in ({'max_distance':True},{'max_distance':-1},{'max_distance':65},{'max_aspect_ratio_difference':True},{'max_aspect_ratio_difference':float('inf')},{'max_aspect_ratio_difference':float('nan')},{'max_images':True},{'max_images':1001}):reject(lambda:D.triage_duplicates([],image_root=root,**options));invalid_count+=1
    reject(lambda:D.triage_duplicates([a]*1001,image_root=root));invalid_count+=1
    altered=copy.deepcopy(a);altered['image_path']='../outside.png';reject(lambda:D.triage_duplicates([altered],image_root=root));invalid_count+=1
    results.append({'case':'input_type_depth_alpha_orientation_path_and_bound_guards','status':'passed','rejections':invalid_count})
    manifest=root/'manifest.jsonl';manifest.write_text(json.dumps(a)+'\n'+json.dumps(b)+'\n')
    # Use two exactly matching pixels across train/dev and require CLI failure.
    a['image_path']='same-pixels-a.png';a['image_sha256']=digest(root/a['image_path']);a['record_id']='same-pixels-a'
    manifest.write_text(json.dumps(a)+'\n'+json.dumps(b)+'\n')
    env={**os.environ,'PYTHONPATH':str(P/'src')}
    cli=subprocess.run([sys.executable,'-m','mmbu_prep','near-duplicates',str(manifest),'--image-root',str(root)],env=env,text=True,capture_output=True)
    assert cli.returncode==2 and not cli.stdout and 'decoded_split_leakage' in cli.stderr
    results.append({'case':'cli_cross_split_exact_error','status':'passed','exit_code':cli.returncode})
prepared=ROOT/'work/roco-quarantine/prepared';manifest=prepared/'pending-manifest.jsonl';rows=[json.loads(x) for x in manifest.read_text().splitlines()];before=copy.deepcopy(rows);files={x['image_path']:digest(prepared/x['image_path']) for x in rows}
real=D.triage_duplicates(rows,image_root=prepared);saved=json.loads((P/'evidence/roco-duplicate-triage.json').read_text());assert real==saved and rows==before and files=={x['image_path']:digest(prepared/x['image_path']) for x in rows}
cli=subprocess.run([sys.executable,'-m','mmbu_prep','near-duplicates',str(manifest),'--image-root',str(prepared)],env={**os.environ,'PYTHONPATH':str(P/'src')},text=True,capture_output=True);assert cli.returncode==0 and json.loads(cli.stdout)==real
results.append({'case':'real_24_image_replay_and_cli','status':'passed','images':len(real['images']),'candidates':len(real['candidates']),'exact_saved_json_reproduction':True,'input_records_and_files_unchanged':True,'cli_exit_code':cli.returncode})
report={'schema_version':1,'results':results,'production_sha256':digest(P/'src/mmbu_prep/duplicates.py'),'cli_sha256':digest(P/'src/mmbu_prep/__main__.py'),'saved_triage_sha256':digest(P/'evidence/roco-duplicate-triage.json'),'script_sha256':digest(Path(__file__)),'production_modified':False,'network_requests':0,'model_use_approval':False}
(P/'evidence/duplicates-independent-probes.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));sys.exit(0 if all(x['status']=='passed' for x in results) else 1)
