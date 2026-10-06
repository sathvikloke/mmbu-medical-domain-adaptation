from pathlib import Path
import urllib.request,json,hashlib,datetime
root=Path('work/protocol-recheck-2026-10-04');root.mkdir(exist_ok=True)
urls={'challenge.html':'https://akiranishii.github.io/mmbu-challenge/','public-api.json':'https://huggingface.co/api/datasets/mmbu/mmbu-public','public-card.html':'https://huggingface.co/datasets/mmbu/mmbu-public','github-issues.json':'https://api.github.com/repos/akiranishii/mmbu-challenge/issues?state=open&per_page=100'}
result=[]
for name,url in urls.items():
    item={'url':url,'path':str(root/name),'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'MMBU-research-preparation/0.3'}),timeout=30) as response:
            body=response.read(3_000_001)
            if len(body)>3_000_000:raise ValueError('Response cap exceeded')
            item.update(status=response.status,final_url=response.url,bytes=len(body),sha256=hashlib.sha256(body).hexdigest())
        (root/name).write_bytes(body)
        if name=='public-api.json':
            data=json.loads(body);item.update(revision=data.get('sha'),lastModified=data.get('lastModified'),gated=data.get('gated'))
        if name=='github-issues.json':item['open_issue_count_first_page']=len(json.loads(body))
    except Exception as error:item.update(error_type=type(error).__name__,error=str(error))
    result.append(item)
Path('outputs/mmbu-precompute/evidence/protocol-recheck-2026-10-04.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
