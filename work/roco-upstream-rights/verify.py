"""Offline cross-check directly against the captured JATS; no imports from extractor."""
from pathlib import Path
import collections,datetime,hashlib,json,re,unicodedata,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent;P=ROOT/'outputs/mmbu-precompute'
report=json.loads((P/'evidence/roco-upstream-rights.json').read_text());source=json.loads((P/'evidence/roco-shortlist.json').read_text());source={x['source_image_id']:x for x in source}
N={'j':'https://jats.nlm.nih.gov/ns/archiving/1.4/','o':'http://www.openarchives.org/OAI/2.0/','ali':'http://www.niso.org/schemas/ali/1.0/'};XL='{http://www.w3.org/1999/xlink}href'
def normal(s):return ' '.join(unicodedata.normalize('NFC',s).split())
assert normal('title.')!=normal('title') and normal('MR Image')!=normal('MR image')
assert normal('a\u00a0b')==normal('a b') and normal('cafe\u0301')==normal('café')
verified=[]
for result in report['results']:
    path=W/(result['pmcid']+'.xml');data=path.read_bytes();tree=E.fromstring(data)
    assert hashlib.sha256(data).hexdigest()==result['retrieval']['sha256']
    assert tree.find('.//o:identifier',N).text=='oai:pubmedcentral.nih.gov:'+result['pmcid'][3:]
    meta=tree.find('.//j:article/j:front/j:article-meta',N)
    assert meta.find("j:article-id[@pub-id-type='pmcid']",N).text==result['pmcid']
    licenses=meta.findall('j:permissions/j:license',N)
    assert len(licenses)==len(result['article_licenses'])==1
    for lic,claimed in zip(licenses,result['article_licenses']):
        if claimed['primary_uri_locator'].endswith('@xlink:href'):assert lic.get(XL)==claimed['primary_license_uri']
        else:
            refs=lic.findall('ali:license_ref',N)
            assert any(x.text==claimed['primary_license_uri'] and x.get('specific-use')=='textmining' for x in refs)
        assert claimed['parsed_primary_license']['license_code']=='by'
    raw=source[result['source_image_id']]['raw_caption'];want=normal(raw)
    matches=[]
    for figure in tree.findall('.//j:fig',N):
        caption=figure.find('j:caption',N)
        if caption is not None and normal(''.join(caption.itertext()))==want:matches.append(figure)
    if result['original_figure_id'] is None:assert len(matches)==0
    else:
        assert len(matches)==1 and matches[0].get('id')==result['original_figure_id']
        actual_graphics=[x.get(XL) for x in matches[0].findall('.//j:graphic',N)]
        assert actual_graphics==[x['href'] for x in result['graphic_references']]
    assert not result['model_use_approved'] and not result['source_image_bytes_compared_to_upstream_graphic']
    verified.append(result['source_image_id'])
ledger=json.loads((W/'retrievals.json').read_text());times=[datetime.datetime.fromisoformat(x['at_utc']) for x in ledger]
min_gap=min((b-a).total_seconds() for a,b in zip(times,times[1:]))
assert min_gap>=.6 and len(ledger)==26 and all(x['status']==200 and x['exit_code']==0 for x in ledger)
assert sum(x['transfer_bytes'] for x in ledger)<60_000_000
assert len(verified)==len(source)==24
out={'schema_version':1,'verification_exit_code':0,'records_verified':len(verified),'direct_jats_identity_license_caption_graphics_checks':True,'normalization_negative_and_equivalence_checks':4,'serialized_requests':len(ledger),'all_http_statuses_200':True,'minimum_request_start_gap_seconds':min_gap,'transfer_bytes':sum(x['transfer_bytes'] for x in ledger),'source_heldout_or_image_requests':0,'no_model_use_approval':True,'artifacts':[{'path':str(x.relative_to(ROOT)),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size} for x in [P/'evidence/roco-upstream-rights.json',W/'acquire.py',W/'analyze.py',Path(__file__),W/'retrievals.json']]}
(P/'evidence/roco-upstream-rights-verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
