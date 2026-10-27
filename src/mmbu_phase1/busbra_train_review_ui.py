"""Build a receipt-bound, self-contained BUS-BRA train review interface.

The generated page is a human-review aid only.  It never grants source
admission, training, model-use, release, upload, submission, or clinical
authority.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile

from .busbra_train_qa import VISUAL_FIELDS, _canonical_digest, _safe_relative
from .busbra_train_qa_validation import (
    DISPOSITIONS,
    SHORTCUTS,
    TARGETS,
    YES_NO,
    YES_NO_UNCERTAIN,
    _verify_packet,
)


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REVIEW_FIELDS = VISUAL_FIELDS[6:]


def _safe_json(value: object) -> str:
    """Serialize JSON so untrusted strings cannot terminate the script element."""
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")


def _asset(packet_dir: Path, relative_value: object, bound_paths: set[str], label: str) -> str:
    relative = _safe_relative(relative_value, label)
    relative_text = relative.as_posix()
    if relative_text not in bound_paths:
        raise ValueError(f"{label} is not bound by the packet receipt")
    path = packet_dir.joinpath(*relative.parts)
    if path.is_symlink():
        raise ValueError(f"{label} may not be a symbolic link")
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"{label} is unreadable") from exc
    if not payload.startswith(PNG_SIGNATURE):
        raise ValueError(f"{label} does not have a PNG signature")
    return "data:image/png;base64," + base64.b64encode(payload).decode("ascii")


def _bootstrap(packet_dir: Path, receipt: dict, manifest: dict) -> dict:
    members = receipt.get("members")
    if not isinstance(members, list):
        raise ValueError("packet receipt members are missing")
    bound_paths = {
        row.get("path") for row in members if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    records = manifest.get("records")
    if not isinstance(records, list):
        raise ValueError("train-QA records are missing")
    rendered = []
    seen = set()
    required = {
        "record_id", "case_id", "selection_role", "mandatory_reasons", "image_path", "mask_path",
    }
    for index, row in enumerate(records):
        if not isinstance(row, dict) or not required <= set(row):
            raise ValueError(f"train-QA record[{index}] is incomplete")
        record_id = row["record_id"]
        if not isinstance(record_id, str) or not record_id or record_id in seen:
            raise ValueError("train-QA record IDs must be unique nonblank strings")
        seen.add(record_id)
        if row["selection_role"] not in {"mandatory", "routine"}:
            raise ValueError(f"record {record_id}.selection_role is invalid")
        reasons = row["mandatory_reasons"]
        if not isinstance(reasons, list) or any(not isinstance(value, str) for value in reasons):
            raise ValueError(f"record {record_id}.mandatory_reasons is invalid")
        rendered.append({
            "record_id": record_id,
            "case_id": row["case_id"],
            "selection_role": row["selection_role"],
            "mandatory_reasons": reasons,
            "image_path": row["image_path"],
            "mask_path": row["mask_path"],
            "pathology": row.get("pathology"),
            "birads": row.get("birads"),
            "decoded_width": row.get("decoded_width"),
            "decoded_height": row.get("decoded_height"),
            "mask_derived_bbox_xywh": row.get("mask_derived_bbox_xywh"),
            "image_data_uri": _asset(
                packet_dir, row["image_path"], bound_paths, f"record {record_id}.image_path",
            ),
            "mask_data_uri": _asset(
                packet_dir, row["mask_path"], bound_paths, f"record {record_id}.mask_path",
            ),
        })
    return {
        "schema": "mmbu.busbra.train_review_ui_bootstrap.v1",
        "draftSchema": "mmbu.busbra.train_review_draft.v1",
        "receiptDigest": receipt["receipt_digest"],
        "visualFields": list(VISUAL_FIELDS),
        "reviewFields": list(REVIEW_FIELDS),
        "vocabularies": {
            "yesNo": sorted(YES_NO),
            "yesNoUncertain": sorted(YES_NO_UNCERTAIN),
            "shortcuts": sorted(SHORTCUTS),
            "targets": sorted(TARGETS),
            "dispositions": sorted(DISPOSITIONS),
        },
        "records": rendered,
        "authority": {
            "review_complete": False,
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "release_authorized": False,
            "upload_authorized": False,
            "submission_authorized": False,
        },
    }


def _html(bootstrap: dict) -> bytes:
    data = _safe_json(bootstrap)
    # All source-controlled markup is static. Frozen packet strings are emitted
    # only inside safe JSON and later assigned with textContent or DOM properties.
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'nonce-mmbu-review'; base-uri 'none'; form-action 'none'">
<title>BUS-BRA train-only visual review</title>
<style>
:root {{ color-scheme: light; font: 15px/1.45 system-ui,sans-serif; background:#f4f6f8; color:#172033; }}
body {{ margin:0; }} header,main {{ max-width:1180px; margin:auto; padding:18px; }}
header {{ background:#102a43; color:white; max-width:none; }} header>div {{ max-width:1180px; margin:auto; }}
.boundary {{ background:#fff4d6; color:#5c4100; border:2px solid #d99b00; padding:12px; font-weight:700; }}
.controls,.record {{ background:white; border:1px solid #cbd5e1; border-radius:10px; padding:16px; margin:14px 0; }}
.grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }}
.images img {{ width:100%; max-height:420px; object-fit:contain; background:#0b1320; }}
label {{ display:block; margin:.6rem 0; font-weight:650; }} select,input,textarea,button {{ font:inherit; }}
select,input[type=text],input[type=datetime-local],textarea {{ box-sizing:border-box; width:100%; padding:7px; }}
textarea {{ min-height:70px; }} button {{ padding:9px 13px; margin:4px; cursor:pointer; }}
.targets label {{ display:inline-block; margin-right:14px; font-weight:500; }}
.error {{ color:#9b1c1c; font-weight:700; white-space:pre-wrap; }} .ok {{ color:#176b39; font-weight:700; }}
.meta {{ color:#45566c; white-space:pre-wrap; }} .record[data-invalid=true] {{ border:3px solid #b91c1c; }}
@media(max-width:760px) {{ .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header><div><h1>BUS-BRA train-only visual review</h1><p>Offline, receipt-bound human review workspace</p></div></header>
<main>
<p class="boundary">No source admission, training, model-use, release, upload, or submission authority. This page only helps an accountable human produce evidence for the separate validator.</p>
<section class="controls">
  <div id="identity"></div>
  <label>Reviewer ID <input id="reviewer-id" type="text" autocomplete="off"></label>
  <label>Reviewed at (UTC) <input id="reviewed-at" type="text" placeholder="YYYY-MM-DDTHH:MM:SSZ" autocomplete="off"></label>
  <input id="draft-file" type="file" accept="application/json,.json">
  <button id="save-draft" type="button">Save JSON draft</button>
  <button id="load-draft" type="button">Load selected draft</button>
  <button id="export-csv" type="button">Validate and export CSV</button>
  <p id="status" aria-live="polite"></p>
</section>
<div id="records"></div>
</main>
<script id="bootstrap" type="application/json">{data}</script>
<script nonce="mmbu-review">
"use strict";
const model = JSON.parse(document.getElementById("bootstrap").textContent);
const answers = Object.fromEntries(model.records.map(r => [r.record_id, {{}}]));
const byId = id => document.getElementById(id);
const status = (message, good=false) => {{ const el=byId("status"); el.textContent=message; el.className=good?"ok":"error"; }};
const text = (tag, value, cls="") => {{ const el=document.createElement(tag); el.textContent=value == null ? "" : String(value); if(cls)el.className=cls; return el; }};
const select = (recordId, name, options) => {{
  const wrapper=document.createElement("label"); wrapper.append(name.replaceAll("_"," ")+" ");
  const el=document.createElement("select"); el.dataset.record=recordId; el.dataset.field=name;
  el.append(new Option("— choose —", "")); options.forEach(v=>el.append(new Option(v,v)));
  el.addEventListener("change",()=>{{answers[recordId][name]=el.value;}}); wrapper.append(el); return wrapper;
}};
function render() {{
  byId("identity").textContent=`Packet receipt: ${{model.receiptDigest}} · ${{model.records.length}} frozen records`;
  const root=byId("records");
  model.records.forEach((record,index)=>{{
    const card=document.createElement("section"); card.className="record"; card.id=`record-${{index}}`; card.dataset.record=record.record_id;
    card.append(text("h2",`${{index+1}}. ${{record.record_id}}`));
    card.append(text("p",`Case ${{record.case_id}} · ${{record.selection_role}} · reasons: ${{record.mandatory_reasons.join("|")||"none"}}`,"meta"));
    const images=document.createElement("div"); images.className="grid images";
    [["Source image",record.image_data_uri],["Annotation mask",record.mask_data_uri]].forEach(([label,src])=>{{
      const box=document.createElement("figure"); const img=document.createElement("img"); img.src=src; img.alt=label+" for "+record.record_id; box.append(img,text("figcaption",label)); images.append(box);
    }}); card.append(images);
    const form=document.createElement("div"); form.className="grid";
    [["asset_match",model.vocabularies.yesNo],["image_interpretable",model.vocabularies.yesNo],["modality_body_part_supported",model.vocabularies.yesNoUncertain],["mask_alignment",model.vocabularies.yesNoUncertain],["annotation_completeness_concern",model.vocabularies.yesNoUncertain],["shortcut_artifact",model.vocabularies.shortcuts],["final_disposition",model.vocabularies.dispositions]].forEach(([name,vocab])=>form.append(select(record.record_id,name,vocab)));
    card.append(form);
    const targets=document.createElement("fieldset"); targets.className="targets"; targets.append(text("legend","Permitted training targets"));
    model.vocabularies.targets.forEach(target=>{{ const label=document.createElement("label"); const box=document.createElement("input"); box.type="checkbox"; box.dataset.record=record.record_id; box.dataset.target=target; box.addEventListener("change",()=>{{answers[record.record_id].permitted_training_targets=[...targets.querySelectorAll("input:checked")].map(x=>x.dataset.target).sort();}}); label.append(box," "+target); targets.append(label); }}); card.append(targets);
    const notes=document.createElement("label"); notes.append("Notes "); const area=document.createElement("textarea"); area.dataset.record=record.record_id; area.dataset.field="notes"; area.addEventListener("input",()=>{{answers[record.record_id].notes=area.value;}}); notes.append(area); card.append(notes);
    card.append(text("p","","error")); root.append(card);
  }});
}}
function needsNotes(row) {{ return row.asset_match==="no" || row.image_interpretable==="no" || row.modality_body_part_supported!=="yes" || row.mask_alignment!=="yes" || row.annotation_completeness_concern!=="no" || row.shortcut_artifact!=="none" || row.final_disposition!=="eligible"; }}
function validateRow(record,row) {{
  const vocab={{asset_match:model.vocabularies.yesNo,image_interpretable:model.vocabularies.yesNo,modality_body_part_supported:model.vocabularies.yesNoUncertain,mask_alignment:model.vocabularies.yesNoUncertain,annotation_completeness_concern:model.vocabularies.yesNoUncertain,shortcut_artifact:model.vocabularies.shortcuts,final_disposition:model.vocabularies.dispositions}};
  const missing=Object.keys(vocab).filter(k=>!row[k]);
  if(missing.length) return "Missing: "+missing.join(", ");
  const invalid=Object.keys(vocab).filter(k=>!vocab[k].includes(row[k])); if(invalid.length) return "Invalid closed-vocabulary value: "+invalid.join(", ");
  const targets=row.permitted_training_targets||[];
  if(!Array.isArray(targets) || JSON.stringify(targets)!==JSON.stringify([...new Set(targets)].sort()) || targets.some(target=>!model.vocabularies.targets.includes(target))) return "Invalid or noncanonical training targets";
  if(row.final_disposition==="eligible" && !targets.length) return "Eligible records require at least one training target";
  if(row.final_disposition==="eligible" && (row.asset_match!=="yes" || row.image_interpretable!=="yes" || row.modality_body_part_supported!=="yes")) return "Eligible records require usable image and modality evidence";
  if(row.final_disposition==="exclude" && targets.length) return "Excluded records may not retain training targets";
  if(targets.includes("mask_context") && (row.mask_alignment!=="yes" || row.annotation_completeness_concern!=="no")) return "mask_context requires aligned, complete annotation";
  if(needsNotes(row) && !(row.notes||"").trim()) return "Notes are required for adverse, uncertain, excluded, or escalated findings";
  return "";
}}
function validateForExport() {{
  const reviewer=byId("reviewer-id").value.trim(), reviewedAt=byId("reviewed-at").value.trim();
  const errors=[]; if(!reviewer) errors.push("Reviewer ID is required"); if(!/^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}Z$/.test(reviewedAt)) errors.push("Reviewed at must be UTC: YYYY-MM-DDTHH:MM:SSZ");
  model.records.forEach((record,index)=>{{ const message=validateRow(record,answers[record.record_id]); const card=byId(`record-${{index}}`); card.dataset.invalid=Boolean(message); card.querySelector(":scope > p.error").textContent=message; if(message)errors.push(record.record_id+": "+message); }});
  return {{errors,reviewer,reviewedAt}};
}}
function draftObject() {{ return {{schema:model.draftSchema,packet_receipt_digest:model.receiptDigest,reviewer_id:byId("reviewer-id").value,reviewed_at:byId("reviewed-at").value,answers:model.records.map(r=>({{record_id:r.record_id,...answers[r.record_id]}})),review_complete:false,source_admission_authorized:false,training_ready:false,model_use_authorized:false}}; }}
function validateDraft(draft) {{
  if(!draft || draft.schema!==model.draftSchema || draft.packet_receipt_digest!==model.receiptDigest || !Array.isArray(draft.answers)) throw new Error("Foreign or incomplete draft: schema or receipt mismatch");
  const expected=model.records.map(r=>r.record_id).sort(), actual=draft.answers.map(r=>r&&r.record_id).sort();
  if(JSON.stringify(expected)!==JSON.stringify(actual) || new Set(actual).size!==actual.length) throw new Error("Foreign or incomplete draft: record population mismatch");
  const allowed=new Set(["record_id",...model.reviewFields]); if(draft.answers.some(row=>!row || typeof row!=="object" || Object.keys(row).some(key=>!allowed.has(key)))) throw new Error("Foreign or incomplete draft: unknown answer field");
  if(["review_complete","source_admission_authorized","training_ready","model_use_authorized"].some(k=>draft[k]!==false)) throw new Error("Foreign or incomplete draft: authority fields must remain false");
}}
function applyDraft(draft) {{
  validateDraft(draft); byId("reviewer-id").value=draft.reviewer_id||""; byId("reviewed-at").value=draft.reviewed_at||"";
  draft.answers.forEach(source=>{{ const id=source.record_id; answers[id]={{...source}}; delete answers[id].record_id; document.querySelectorAll(`[data-record="${{CSS.escape(id)}}"][data-field]`).forEach(el=>{{el.value=answers[id][el.dataset.field]||"";}}); document.querySelectorAll(`[data-record="${{CSS.escape(id)}}"][data-target]`).forEach(el=>{{el.checked=(answers[id].permitted_training_targets||[]).includes(el.dataset.target);}}); }});
}}
function download(name,type,payload) {{ const blob=new Blob([payload],{{type}}), url=URL.createObjectURL(blob), a=document.createElement("a"); a.href=url; a.download=name; a.click(); setTimeout(()=>URL.revokeObjectURL(url),0); }}
function csvCell(value) {{ const text=String(value??""); return /[",\\r\\n]/.test(text) ? `"${{text.replaceAll('"','""')}}"` : text; }}
function exportCsv() {{
  const check=validateForExport(); if(check.errors.length){{status(check.errors.join("\\n"));return;}}
  const lines=[model.visualFields.map(csvCell).join(",")]; model.records.forEach(record=>{{ const row={{record_id:record.record_id,case_id:record.case_id,selection_role:record.selection_role,mandatory_reasons:record.mandatory_reasons.join("|"),image_path:record.image_path,mask_path:record.mask_path,reviewer_id:check.reviewer,reviewed_at:check.reviewedAt,...answers[record.record_id]}}; row.permitted_training_targets=(row.permitted_training_targets||[]).sort().join("|"); lines.push(model.visualFields.map(field=>csvCell(row[field])).join(",")); }}); download("visual-review-completed.csv","text/csv;charset=utf-8",lines.join("\\n")+"\\n"); status("Validated CSV export created. Run the separate Python validator before any downstream decision.",true);
}}
byId("save-draft").addEventListener("click",()=>download("busbra-review-draft.json","application/json",JSON.stringify(draftObject(),null,2)+"\\n"));
byId("load-draft").addEventListener("click",async()=>{{ try{{const file=byId("draft-file").files[0]; if(!file)throw new Error("Choose a JSON draft first"); applyDraft(JSON.parse(await file.text())); status("Draft loaded and receipt identity verified.",true);}}catch(error){{status(error.message);}} }});
byId("export-csv").addEventListener("click",exportCsv);
render();
</script>
</body>
</html>
"""
    return document.encode("utf-8")


def _publish_no_replace(output: Path, payload: bytes) -> None:
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError(str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".busbra-review-ui-", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o444)
        os.link(temporary, output, follow_symlinks=False)
        directory_fd = os.open(output.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def build_review_ui(packet_dir: Path, expected_receipt_digest: str, output: Path) -> dict:
    """Verify ``packet_dir`` and exclusively publish its offline review page."""
    packet_dir = Path(packet_dir)
    output = Path(output)
    if not isinstance(expected_receipt_digest, str) or len(expected_receipt_digest) != 64:
        raise ValueError("expected receipt digest must be a SHA-256 hex string")
    receipt, manifest = _verify_packet(packet_dir, expected_receipt_digest)
    bootstrap = _bootstrap(packet_dir, receipt, manifest)
    payload = _html(bootstrap)
    _publish_no_replace(output, payload)
    result = {
        "schema": "mmbu.busbra.train_review_ui_receipt.v1",
        "source_id": "busbra",
        "source_version": "1.0",
        "purpose": "train-human-visual-review-aid",
        "packet_receipt_digest": receipt["receipt_digest"],
        "manifest_digest": manifest["manifest_digest"],
        "record_count": len(manifest["records"]),
        "output_path": output.name,
        "output_bytes": len(payload),
        "output_sha256": hashlib.sha256(payload).hexdigest(),
        "review_complete": False,
        "source_admission_authorized": False,
        "training_ready": False,
        "model_use_authorized": False,
        "release_authorized": False,
        "upload_authorized": False,
        "submission_authorized": False,
    }
    result["receipt_digest"] = _canonical_digest(result)
    return result
