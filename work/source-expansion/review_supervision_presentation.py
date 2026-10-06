"""Independent read-only probes; generated original fixtures live in a temp directory."""
from pathlib import Path
import argparse, hashlib, json, os, struct, sys, tempfile
ROOT=Path(__file__).resolve().parents[2]
PKG=ROOT/'outputs/mmbu-precompute'
sys.path.insert(0,str(PKG/'src'))
from mmbu_prep.supervision import assistant_labels, pad_supervised_batch
from mmbu_prep.presentation import present_image

results=[]
def check(name,fn):
    try:
        details=fn();results.append({'name':name,'status':'passed','details':details})
    except Exception as exc:
        results.append({'name':name,'status':'failed','exception':type(exc).__name__,'message':str(exc)})

def rejected(fn):
    try:fn()
    except (ValueError, FileExistsError):return
    raise AssertionError('Unexpected acceptance')

def supervision_values():
    trials=0
    for values in (None,(),[],[True],[1.2],[-1],['1']):
        rejected(lambda:assistant_labels(values,[1,2],forbidden_target_ids=set(),max_length=3));trials+=1
        rejected(lambda:assistant_labels([1],values,forbidden_target_ids=set(),max_length=3));trials+=1
    for forbidden in (None,False,{True},{-1},{1.5}):
        rejected(lambda:assistant_labels([1],[1,2],forbidden_target_ids=forbidden,max_length=3));trials+=1
    for maximum in (True,0,-1,2.5,None):
        rejected(lambda:assistant_labels([1],[1,2],forbidden_target_ids=set(),max_length=maximum));trials+=1
    for prompt,full in (([1,2],[1,2]),([1,2,3],[1,2]),([1,2],[1,9,1,2,3]),([1,2],[1,3,2])):
        rejected(lambda:assistant_labels(prompt,full,forbidden_target_ids=set(),max_length=99));trials+=1
    prompt=[7,0,7];full=prompt+[0,9,0]
    labels=assistant_labels(prompt,full,forbidden_target_ids={17},max_length=6)
    assert labels==[-100,-100,-100,0,9,0]
    assert prompt==[7,0,7] and full==[7,0,7,0,9,0]
    rejected(lambda:assistant_labels(prompt,full,forbidden_target_ids={0},max_length=6));trials+=1
    rejected(lambda:assistant_labels(prompt,full,forbidden_target_ids=set(),max_length=5));trials+=1
    out=pad_supervised_batch([{'input_ids':full,'labels':labels},{'input_ids':[0,9],'labels':[-100,9]}],pad_token_id=9,max_length=8,pad_to_multiple_of=4)
    assert out['supervised_tokens']==4
    assert out['attention_mask']==[[1]*6+[0]*2,[1]*2+[0]*6]
    assert out['labels'][0]==labels+[-100]*2 and out['labels'][1]==[-100,9]+[-100]*6
    assert out['input_ids'][1]==[0,9]+[9]*6
    rejected(lambda:pad_supervised_batch([{'input_ids':full,'labels':labels}],pad_token_id=9,max_length=7,pad_to_multiple_of=4));trials+=1
    for ids,labels in (([7,9],[7,-100]),([7],[7]),([7,9],[7,9]),([7],[-100])):
        rejected(lambda:pad_supervised_batch([{'input_ids':ids,'labels':labels}],pad_token_id=0,max_length=2));trials+=1
    return {'adversarial_rejections':trials,'eos_equal_pad_and_token_zero_preserved':True,'input_lists_unchanged':True}

def presentation_values():
    from PIL import Image
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);totals=[]
        values=list(range(65536))
        windows=[(0,65535),(1234,54321),(32767,32769),(0,1),(1,2),(100,103)]
        for mode,endian in [('I;16','<'),('I;16B','>')]:
            src=p/(mode.replace(';','-')+'.tif')
            Image.frombytes(mode,(256,256),struct.pack(endian+'65536H',*values)).save(src)
            before=src.read_bytes()
            for black,white in windows:
                out=p/(mode.replace(';','-')+f'-{black}-{white}.png')
                r=present_image(src,out,window=(black,white));span=white-black
                expected=[0 if v<=black else 255 if v>=white else (2*(v-black)*255+span)//(2*span) for v in values]
                with Image.open(out) as im:
                    assert im.mode=='RGB' and im.size==(256,256)
                    assert list(im.get_flattened_data())==[(v,v,v) for v in expected]
                assert r['clipped_low_pixels']==black and r['clipped_high_pixels']==65535-white
                assert r['coordinate_transform']=='identity'
                assert r['parent_image_sha256']==hashlib.sha256(before).hexdigest()
                assert r['image_sha256']==hashlib.sha256(out.read_bytes()).hexdigest()
                assert src.read_bytes()==before
                totals.append({'mode':mode,'window':[black,white],'checked_pixels':65536})
        for mode in ('RGB','L'):
            src=p/(mode+'.png');im=Image.new(mode,(7,5))
            seq=[(i*3%256,i*7%256,i*11%256) for i in range(35)] if mode=='RGB' else list(range(35))
            im.putdata(seq);im.save(src);old=src.read_bytes();out=p/(mode+'-result.png')
            r=present_image(src,out)
            with Image.open(out) as image:assert list(image.get_flattened_data())==(seq if mode=='RGB' else [(v,v,v) for v in seq])
            assert src.read_bytes()==old and r['width']==7 and r['height']==5
            rejected(lambda:present_image(src,src))
            rejected(lambda:present_image(src,out))
            rejected(lambda:present_image(src,p/'bad-window.png',window=(0,255)))
        return {'uint16_cases':totals,'numeric_pixel_checks':len(totals)*65536,'asymmetric_rgb_and_gray_frames_preserved':True,'source_bytes_unchanged':True}

def presentation_guards():
    from PIL import Image
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);files=[]
        for mode,value in [('F',float('nan')),('I',-1),('RGBA',(1,2,3,255)),('LA',(1,255)),('P',1),('CMYK',(0,1,2,3))]:
            name=p/(mode+'.tif');Image.new(mode,(3,2),value).save(name);files.append(name)
        for orientation in range(2,9):
            exif=Image.Exif();exif[274]=orientation
            name=p/f'orientation-{orientation}.png';Image.new('RGB',(3,2),(1,2,3)).save(name,exif=exif);files.append(name)
        for mode,key in [('RGB',(1,2,3)),('L',1)]:
            name=p/(mode+'-transparent.png');Image.new(mode,(3,2),key).save(name,transparency=key);files.append(name)
        name=p/'animation.gif';Image.new('RGB',(3,2),'black').save(name,save_all=True,append_images=[Image.new('RGB',(3,2),'white')]);files.append(name)
        # RGB16 PNG would otherwise decode to RGB8 and lose precision.
        import zlib
        def chunk(kind,b):return struct.pack('>I',len(b))+kind+b+struct.pack('>I',zlib.crc32(kind+b)&0xffffffff)
        name=p/'rgb16.png';name.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,16,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'+struct.pack('>3H',256,257,65535)))+chunk(b'IEND',b''));files.append(name)
        for name in files:
            rejected(lambda:present_image(name,p/'never.png',window=(0,65535)))
            assert not (p/'never.png').exists()
        raw=p/'valid.tif';Image.new('I;16',(3,2),1024).save(raw)
        for window in (None,[],[0],(0,65536),(65535,65535),(-1,5),(True,5),(1,False),(0,2.0),'0,65535'):
            rejected(lambda:present_image(raw,p/'never.png',window=window));assert not (p/'never.png').exists()
        # A dangling output symlink must not be followed or replace its target.
        symlink=p/'dangling.png';symlink.symlink_to(p/'nonexistent.png')
        rejected(lambda:present_image(raw,symlink,window=(0,65535)));assert not (p/'nonexistent.png').exists()
        outside=p/'outside';outside.mkdir();source=outside/'valid.png';Image.new('RGB',(2,2)).save(source)
        sandbox=p/'sandbox';sandbox.mkdir();link=sandbox/'input-link.png';link.symlink_to(source)
        rejected(lambda:present_image(link,p/'never.png'));assert not (p/'never.png').exists()
        return {'unsupported_dtype_alpha_orientation_depth_or_frame_rejections':len(files),'bad_window_rejections':10,'symlink_probes':2,'no_failed_probe_published_output':True}

def native():
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_DATASETS_OFFLINE='1')
    import socket
    attempted=[]
    def deny(*args,**kwargs):attempted.append(str(args));raise RuntimeError('Independent probe forbids network access')
    socket.create_connection=deny;socket.socket.connect=deny
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    torch.set_num_threads(1)
    registry=json.loads((PKG/'configs/model-registry.json').read_text())['models']
    report=[]
    for model in registry:
        folder=ROOT/'work/processor-probe/artifacts'/model['model_id'].replace('/','--')/model['revision']
        manifest=json.loads((folder/'artifact-manifest.json').read_text())
        assert manifest['revision']==model['revision'] and manifest['model_id']==model['model_id']
        for entry in manifest['files']:
            if entry['status']=='downloaded':
                data=(folder/entry['filename']).read_bytes();assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
        assert not list(folder.glob('*.safetensors')) and not list(folder.glob('*.bin'))
        processor=AutoProcessor.from_pretrained(folder,local_files_only=True,trust_remote_code=False)
        forbidden={processor.tokenizer.convert_tokens_to_ids(token) for token in processor.tokenizer.all_special_tokens if any(key in token.lower() for key in ('image','video','vision','im_start'))}
        assert processor.image_token_id in forbidden
        variants=[('default',{})]
        if model['model_id']=='Qwen/Qwen3.5-9B':variants.append(('nonthinking',{'enable_thinking':False}))
        for variant,options in variants:
            expected_reject=model['model_id']=='Qwen/Qwen3.5-9B' and variant=='default'
            examples=[];cases=[]
            for number,(size,answer) in enumerate([((64,64),'{"answer": "5"}'),((301,199),'{"answer": "café → [7, 11, 19, 23]"}')]):
                image=Image.new('RGB',size,(11,73,139))
                messages=[{'role':'system','content':'Answer the image question.'},{'role':'user','content':[{'type':'image'},{'type':'text','text':'Return the requested answer. '+('Longer question ' * (number+1))}]}]
                prompt=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,**options)
                full=processor.apply_chat_template(messages+[{'role':'assistant','content':answer}],tokenize=False,add_generation_prompt=False,**options)
                p=processor(text=[prompt],images=[image],return_tensors='pt',device='cpu')
                f=processor(text=[full],images=[image],return_tensors='pt',device='cpu')
                assert all(str(v.device)=='cpu' for v in list(p.values())+list(f.values()))
                pids=p['input_ids'][0].tolist();fids=f['input_ids'][0].tolist()
                if expected_reject:
                    rejected(lambda:assistant_labels(pids,fids,forbidden_target_ids=forbidden,max_length=len(fids)))
                    assert fids[:len(pids)]!=pids
                    cases.append({'prompt_tokens':len(pids),'full_tokens':len(fids),'outcome':'rejected_prefix_mismatch'})
                else:
                    labels=assistant_labels(pids,fids,forbidden_target_ids=forbidden,max_length=len(fids))
                    assert labels[:len(pids)]==[-100]*len(pids) and labels[len(pids):]==fids[len(pids):]
                    assert len(labels)==len(fids) and processor.tokenizer.eos_token_id in labels[len(pids):]
                    rejected(lambda:assistant_labels(pids,fids,forbidden_target_ids=forbidden,max_length=len(fids)-1))
                    injected=fids+[processor.image_token_id]
                    rejected(lambda:assistant_labels(pids,injected,forbidden_target_ids=forbidden,max_length=len(injected)))
                    examples.append({'input_ids':fids,'labels':labels})
                    cases.append({'prompt_tokens':len(pids),'full_tokens':len(fids),'supervised_tokens':len(fids)-len(pids),'outcome':'accepted_exact_prefix','suffix_decoded':processor.tokenizer.decode(fids[len(pids):],skip_special_tokens=False)})
            if examples:
                cap=((max(len(row['input_ids']) for row in examples)+7)//8)*8
                batch=pad_supervised_batch(examples,pad_token_id=processor.tokenizer.pad_token_id,max_length=cap,pad_to_multiple_of=8)
                assert batch['supervised_tokens']==sum(c['supervised_tokens'] for c in cases)
                for i,example in enumerate(examples):
                    n=len(example['input_ids']);assert batch['input_ids'][i][:n]==example['input_ids'] and batch['labels'][i][:n]==example['labels']
                    assert batch['attention_mask'][i]==[1]*n+[0]*(cap-n)
                    assert batch['labels'][i][n:]==[-100]*(cap-n)
            report.append({'model':model['model_id'],'revision':model['revision'],'variant':variant,'forbidden_target_ids_derived_from_native_special_tokens':sorted(forbidden),'cases':cases,'batch_verified':bool(examples)})
    assert not attempted
    return {'variants':report,'network_connect_attempts':attempted,'model_weights_loaded':False,'model_forward_calls':0,'device':'cpu'}

parser=argparse.ArgumentParser();parser.add_argument('--native',action='store_true');args=parser.parse_args()
if args.native:check('native_processor_supervision_integration',native)
else:
    check('supervision_adversarial_values',supervision_values)
    check('presentation_full_uint16_domain',presentation_values)
    check('presentation_adversarial_images_and_paths',presentation_guards)
report={'python':sys.version,'results':results,'production_hashes':{name:hashlib.sha256((PKG/'src/mmbu_prep'/name).read_bytes()).hexdigest() for name in ('supervision.py','presentation.py','images.py')},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
print(json.dumps(report,indent=2));sys.exit(0 if all(row['status']=='passed' for row in results) else 1)
