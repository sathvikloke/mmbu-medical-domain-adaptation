from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import json,csv,hashlib,collections
package=Path('outputs/mmbu-precompute');root=Path('work/roco-quarantine/prepared');out=Path('work/roco-quarantine/qa');out.mkdir(exist_ok=True)
rows=[json.loads(line) for line in (root/'pending-manifest.jsonl').read_text().splitlines()]
canvas=Image.new('RGB',(1200,1620),'#e4e6e8');draw=ImageDraw.Draw(canvas)
for i,row in enumerate(rows):
    x,y=(i%4)*300,(i//4)*270
    with Image.open(root/row['image_path']) as picture:
        thumbnail=ImageOps.contain(picture,(288,212));canvas.paste(thumbnail,(x+(300-thumbnail.width)//2,y+4))
    draw.text((x+7,y+220),row['source_image_id'].replace('ROCOv2_2023_train_','train_'),fill='black')
    draw.text((x+7,y+236),row['answer'][:39],fill='black')
    draw.text((x+7,y+251),row['pmcid']+' | LABEL PENDING REVIEW',fill='black')
canvas.save(out/'contact-sheet.png')
fields=['source_image_id','pmcid','proposed_modality','width','height','image_path','reviewer','visually_supported','panel_ambiguity','annotation_problem','decision','notes']
with (package/'evidence/roco-review-queue.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
    for row in rows:writer.writerow(dict(source_image_id=row['source_image_id'],pmcid=row['pmcid'],proposed_modality=row['answer'],width=row['image_width'],height=row['image_height'],image_path=str((root/row['image_path']).resolve()),decision='pending'))
inspection=json.loads((root/'image-inspection.json').read_text())
report={'source_images':24,'pending_records':24,'articles':24,'modalities':dict(collections.Counter(r['answer'] for r in rows)),'inspection_ok':inspection['ok'],'exact_decoded_duplicate_groups':len(inspection['duplicate_groups']),'dimensions':{'min_width':min(r['image_width'] for r in rows),'max_width':max(r['image_width'] for r in rows),'min_height':min(r['image_height'] for r in rows),'max_height':max(r['image_height'] for r in rows)},'source_partition':'train','model_use_approved':False,'raw_bytes_preserved':True,'display_recipes':dict(collections.Counter(r['recipe'] for r in json.loads((root/'presentations.json').read_text()))),'prepared_file_hashes':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()},'contact_sheet':str(out/'contact-sheet.png'),'contact_sheet_sha256':hashlib.sha256((out/'contact-sheet.png').read_bytes()).hexdigest(),'medical_label_review_completed':False}
(package/'evidence/roco-sample-intake.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='prepared_file_hashes'},indent=2))
