"""Bounded, serialized acquisition through the current official PMC OAI-PMH API."""
from pathlib import Path
import datetime,gzip,hashlib,io,json,time,urllib.error,urllib.parse,urllib.request,zlib
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
LIMIT=2_500_000;BUDGET=60_000_000
rows=json.loads((ROOT/'outputs/mmbu-precompute/evidence/roco-shortlist.json').read_text())
assert len(rows)==24 and len({r['pmcid'] for r in rows})==24
ledger=json.loads((OUT/'retrievals.json').read_text()) if (OUT/'retrievals.json').exists() else []
if any(r.get('status') in (401,403,429) for r in ledger):raise RuntimeError('Prior explicit access/rate denial remains recorded; do not retry or use an alternate path')
completed={r['path'] for r in ledger if r.get('exit_code')==0}
transferred=sum(r.get('transfer_bytes',0) for r in ledger)
requests=[{'pmcid':None,'source_image_id':None,'name':'oa-service-doc.html','url':'https://pmc.ncbi.nlm.nih.gov/tools/oa-service/'},{'pmcid':None,'source_image_id':None,'name':'oai-doc.html','url':'https://pmc.ncbi.nlm.nih.gov/tools/oai/'}]
requests += [{'pmcid':r['pmcid'],'source_image_id':r['source_image_id'],'name':r['pmcid']+'.xml','url':'https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/?'+urllib.parse.urlencode({'verb':'GetRecord','identifier':'oai:pubmedcentral.nih.gov:'+r['pmcid'][3:],'metadataPrefix':'pmc'})} for r in rows]
for row in requests:
    pmcid=row['pmcid'];name=row['name'];path=OUT/name;url=row['url']
    if str(path.relative_to(ROOT)) in completed:
        prior=next(r for r in ledger if r.get('path')==str(path.relative_to(ROOT)) and r.get('exit_code')==0)
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=prior['sha256']:raise RuntimeError('Cached response missing or changed; do not silently refresh')
        continue
    record={'pmcid':pmcid,'source_image_id':row['source_image_id'],'url':url,'path':str(path.relative_to(ROOT)),'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'GET','minimum_interrequest_delay_seconds':0.6}
    if transferred+LIMIT>BUDGET:raise RuntimeError('Total transfer budget would be exceeded')
    try:
        request=urllib.request.Request(url,headers={'User-Agent':'MMBUQuarantineProvenanceAudit/1.0','Accept-Encoding':'gzip, deflate'})
        with urllib.request.urlopen(request,timeout=45) as response:
            raw=response.read(LIMIT+1);transferred+=len(raw)
            record.update(status=response.status,final_url=response.url,headers=dict(response.headers),transfer_bytes=len(raw),transfer_sha256=hashlib.sha256(raw).hexdigest())
            if len(raw)>LIMIT:raise ValueError('Per-response transfer bound exceeded')
            encoding=response.headers.get('Content-Encoding','')
            if encoding=='gzip':
                with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:data=stream.read(LIMIT+1)
            elif encoding=='deflate':data=zlib.decompressobj().decompress(raw,LIMIT+1)
            else:data=raw
            if len(data)>LIMIT:raise ValueError('Per-response decoded XML bound exceeded')
            path.write_bytes(data);record.update(decoded_bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),exit_code=0)
    except urllib.error.HTTPError as error:
        record.update(status=error.code,headers=dict(error.headers),exit_code=1,error_type=type(error).__name__,error=str(error))
    except Exception as error:record.update(exit_code=1,error_type=type(error).__name__,error=str(error))
    ledger.append(record);(OUT/'retrievals.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print(pmcid,record.get('status'),record.get('decoded_bytes'),record.get('error',''),flush=True)
    if record.get('status') in (401,403,429):
        print('Explicit service access/rate denial: stop; no alternate path',flush=True);break
    time.sleep(.6)
