from pathlib import Path
import hashlib, json, re, shutil, zipfile, collections
ROOT=Path.cwd(); REPO=ROOT/'team-repo'; PAYLOAD=ROOT/'work/github-delivery/payload'
sha=lambda b:hashlib.sha256(b).hexdigest()
def record(name, original, published, reason):
    return {'path':name,'original_bytes':len(original),'original_sha256':sha(original),'published_bytes':len(published),'published_sha256':sha(published),'reason':reason}
transforms=[]
pattern=re.compile(rb'("set-cookie"\s*:\s*)"(?:[^"\\]|\\.)*"', re.I)
for name in ['outputs/mmbu-precompute/evidence/source-expansion.json','work/source-expansion/retrieval-ledger.json']:
    original=(ROOT/name).read_bytes()
    published,count=pattern.subn(lambda m:m[1]+b'"[REDACTED: response cookie omitted from team export]"', original)
    assert count==5,(name,count)
    json.loads(published)
    dest=(REPO if name.startswith('outputs/') else PAYLOAD)/name
    dest.parent.mkdir(parents=True, exist_ok=True);dest.write_bytes(published)
    transforms.append(record(name,original,published,'Removed five Set-Cookie response-header values, including four unexpired opaque Zenodo session handles; research content unchanged.'))
name='outputs/mmbu-precompute/evidence/bundle-manifest.json'; original=(ROOT/name).read_bytes(); data=json.loads(original)
source=REPO/'outputs/mmbu-precompute/evidence/source-expansion.json'
data['files']['evidence/source-expansion.json']={'sha256':sha(source.read_bytes()),'bytes':source.stat().st_size}
published=(json.dumps(data,indent=2)+'\n').encode(); (REPO/name).write_bytes(published)
(REPO/'research/original-bundle-manifest-v0.3.json').write_bytes(original)
transforms.append(record(name,original,published,'Updated only the source-expansion.json content hash/size after transport-cookie redaction. Original manifest retained at research/original-bundle-manifest-v0.3.json.'))
name='outputs/mmbu-precompute-v0.3.zip'; original=(ROOT/name).read_bytes()
with zipfile.ZipFile(ROOT/name) as source,zipfile.ZipFile(REPO/name,'w') as dest:
    for info in source.infolist():
        contents=source.read(info)
        if info.filename in ['mmbu-precompute/evidence/source-expansion.json','mmbu-precompute/evidence/bundle-manifest.json']:
            contents=(REPO/'outputs'/info.filename).read_bytes()
        dest.writestr(info,contents)
published=(REPO/name).read_bytes()
transforms.append(record(name,original,published,'Repacked v0.3 with only its source-expansion.json and bundle-manifest.json transformed; other members unchanged. Historical original ZIP receipt retained.'))
(REPO/'research/publication-redactions.json').write_text(json.dumps({'schema_version':1,'scope':'Private team publication, 2026-10-05. Original user workspace files were not modified. Original historical receipt hashes describe originals; exported hashes describe shared files.','transformations':transforms},indent=2)+'\n')
print(json.dumps({'transformed_paths':[{k:v for k,v in x.items() if k!='reason'} for x in transforms]},indent=2))
