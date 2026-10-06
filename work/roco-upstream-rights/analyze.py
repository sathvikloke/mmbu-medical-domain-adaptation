"""Extract primary JATS rights and exact normalized caption provenance, without approval."""
from pathlib import Path
import collections,hashlib,json,re,unicodedata,urllib.parse,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[2];WORK=Path(__file__).resolve().parent;PKG=ROOT/'outputs/mmbu-precompute'
SHORT=PKG/'evidence/roco-shortlist.json';selected=json.loads(SHORT.read_text());ledger=json.loads((WORK/'retrievals.json').read_text())

def local(tag):return tag.rsplit('}',1)[-1]
def children(node,name):return [x for x in node if local(x.tag)==name]
def nodes(node,name):return [x for x in node.iter() if local(x.tag)==name]
def plain(node):return ''.join(node.itertext())
def norm(value):return re.sub(r'\s+',' ',unicodedata.normalize('NFC',value)).strip()
def sha(value):return hashlib.sha256(value if isinstance(value,bytes) else value.encode('utf-8')).hexdigest()
def href(node):return next((v for k,v in node.attrib.items() if local(k)=='href'),None)
def public_receipt(record):
    allowed={'date','content-type','content-encoding','content-length','last-modified','etag'}
    return {**record,'headers':{k:v for k,v in record.get('headers',{}).items() if k.lower() in allowed}}
def uri_details(uri):
    if not uri:return None
    parsed=urllib.parse.urlparse(uri)
    match=re.fullmatch(r'/licenses/([a-z-]+)/([0-9]+\.[0-9]+)/?',parsed.path)
    if parsed.hostname not in ('creativecommons.org','www.creativecommons.org') or not match:return None
    return {'license_code':match[1],'version':match[2],'canonical_uri':f'https://creativecommons.org/licenses/{match[1]}/{match[2]}/'}
def license_details(license_node):
    links=[]
    for node in license_node.iter():
        link=href(node)
        if link:links.append({'uri':link,'location':'license/'+local(node.tag)+'/@xlink:href','attributes':dict(node.attrib)})
        if local(node.tag)=='license_ref':links.append({'uri':norm(plain(node)),'location':'license/ali:license_ref/text()','attributes':dict(node.attrib)})
    direct=href(license_node)
    refs=[x for x in links if x['location']=='license/ali:license_ref/text()']
    candidates=([{'uri':direct,'location':'article-meta/permissions/license/@xlink:href'}] if direct else [])+refs
    if not candidates:candidates=[x for x in links if uri_details(x['uri'])]
    primary=candidates[0] if candidates else None
    versions={tuple(sorted(uri_details(x['uri']).items())) for x in candidates if uri_details(x['uri'])}
    return {'attributes':dict(license_node.attrib),'primary_license_uri':primary['uri'] if primary else None,'primary_uri_locator':primary['location'] if primary else None,'parsed_primary_license':uri_details(primary['uri']) if primary else None,'primary_uri_candidates_agree':len(versions)<=1,'uri_evidence':links,'license_text_sha256':sha(norm(plain(license_node))),'serialized_license_element_sha256':sha(ET.tostring(license_node)),'separate_data_waiver_uri_present':any('/publicdomain/zero/' in x['uri'] for x in links),'scope':'article-meta/permissions; not an independent figure-specific rights clearance'}
results=[]
for item in selected:
    pmcid=item['pmcid'];path=WORK/(pmcid+'.xml');base={'source_image_id':item['source_image_id'],'pmcid':pmcid,'source_caption_sha256':sha(item['raw_caption']),'source_attribution':item['raw_attribution'],'aggregate_roco_license':'CC-BY-NC-4.0','model_use_approved':False,'original_figure_id':None,'graphic_references':[]}
    retrieval=next((r for r in reversed(ledger) if r.get('path')==str(path.relative_to(ROOT))),None)
    base['retrieval']=public_receipt(retrieval) if retrieval else None
    if not retrieval or retrieval.get('exit_code')!=0 or not path.exists():base.update(status='unavailable',reason='No successful public XML retrieval');results.append(base);continue
    data=path.read_bytes();assert sha(data)==retrieval['sha256'];root=ET.fromstring(data)
    errors=nodes(root,'error')
    if errors:base.update(status='api_error',errors=[{'code':x.get('code'),'text':norm(plain(x))} for x in errors]);results.append(base);continue
    article_nodes=nodes(root,'article');assert len(article_nodes)==1
    article=article_nodes[0];front=children(article,'front')[0];meta=children(front,'article-meta')[0]
    article_ids={x.get('pub-id-type'):norm(plain(x)) for x in children(meta,'article-id')}
    assert article_ids.get('pmcid')==pmcid
    permissions=children(meta,'permissions');article_licenses=[license_details(l) for p in permissions for l in children(p,'license')]
    base.update(status='retrieved',article_ids=article_ids,oai_datestamp=norm(plain(nodes(root,'datestamp')[0])),article_licenses=article_licenses)
    captions=[]
    for fig in nodes(article,'fig'):
        caps=children(fig,'caption')
        if len(caps)!=1:continue
        caption=caps[0];text=plain(caption);normalized=norm(text)
        figs={'figure_id':fig.get('id'),'label':norm(plain(children(fig,'label')[0])) if children(fig,'label') else None,'normalized_caption_sha256':sha(normalized),'source_caption_exact_normalized_match':normalized==norm(item['raw_caption']),'graphic_references':[{'element':local(g.tag),'href':href(g)} for g in fig.iter() if local(g.tag) in ('graphic','inline-graphic','media') and href(g)],'figure_permissions':[license_details(l) for p in nodes(fig,'permissions') for l in nodes(p,'license')],'figure_attribution_text_sha256':[sha(norm(plain(a))) for a in nodes(fig,'attrib')],'figure_attribution_count':len(nodes(fig,'attrib')),'caption_rights_credit_marker_detected':bool(re.search(r'\b(reproduc\w*|permission|courtesy|adapted|copyright|licen[cs]\w*)\b|©',normalized,re.I))}
        captions.append(figs)
    matched=[fig for fig in captions if fig['source_caption_exact_normalized_match']]
    base['article_figure_count']=len(captions);base['caption_candidate_matches']=matched
    base['source_caption_normalized_sha256']=sha(norm(item['raw_caption']))
    if len(matched)==1 and matched[0]['figure_id']:
        match=matched[0];base.update(figure_match_status='unique_exact_normalized_caption',original_figure_id=match['figure_id'],graphic_references=match['graphic_references'],figure_permissions=match['figure_permissions'],figure_attribution_count=match['figure_attribution_count'],caption_rights_credit_marker_detected=match['caption_rights_credit_marker_detected'])
    elif len(matched)>1:base.update(figure_match_status='ambiguous_caption',figure_match_reason='More than one article figure has the same normalized caption')
    else:base.update(figure_match_status='no_unique_exact_caption',figure_match_reason='No figure matches under NFC plus Unicode-whitespace collapse; no fuzzy matching used')
    base['source_image_bytes_compared_to_upstream_graphic']=False
    base['figure_match_limit']='Caption linkage only: does not establish source-image byte identity, panel cropping, or figure-specific legal clearance.'
    results.append(base)
assert len(results)==24
version_counts=collections.Counter()
for result in results:
    licenses=result.get('article_licenses',[])
    for license_ in licenses:
        parsed=license_['parsed_primary_license']
        version_counts[(parsed['license_code']+'-'+parsed['version']) if parsed else 'unresolved']+=1
report={'schema_version':1,'scope':'24 deterministic shortlisted ROCO source-training articles only; article licensing/provenance evidence, no legal or model-use approval','shortlist_sha256':sha(SHORT.read_bytes()),'normalization':'XML parser resolves entities; concatenate caption itertext in document order; NFC Unicode normalization; collapse Unicode whitespace runs to one ASCII space; strip outer whitespace; preserve case, punctuation, hyphens, spelling and words. No label stripping, fuzzy matching, token reordering or medical interpretation.','summary':{'articles':24,'retrieved_xml':sum(x['status']=='retrieved' for x in results),'article_license_versions':dict(sorted(version_counts.items())),'figure_match_status':dict(collections.Counter(x.get('figure_match_status','unavailable') for x in results)),'transfer_bytes':sum(x.get('transfer_bytes',0) for x in ledger),'decoded_bytes':sum(x.get('decoded_bytes',0) for x in ledger),'images_downloaded':0,'model_use_approvals':0},'results':results,'documentation_retrievals':[public_receipt(r) for r in ledger if r['path'].endswith('.html')],'input_hashes':{'shortlist':sha(SHORT.read_bytes()),'retrievals':sha((WORK/'retrievals.json').read_bytes()),'analysis_script':sha(Path(__file__).read_bytes()),'acquisition_script':sha((WORK/'acquire.py').read_bytes())},'analysis_exit_code':0}
(PKG/'evidence/roco-upstream-rights.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['summary'],indent=2))
for item in results:print(item['source_image_id'],item['pmcid'],[(l['primary_license_uri'],l['primary_uri_locator']) for l in item.get('article_licenses',[])],item.get('figure_match_status'),item.get('original_figure_id'))
