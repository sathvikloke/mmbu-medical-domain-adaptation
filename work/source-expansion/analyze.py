"""Recompute bounded source metadata findings. Does not fetch images or emit model data."""
import collections
import csv
import hashlib
import io
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
PACKAGE = PROJECT / "outputs" / "mmbu-precompute"


def read_csv(name):
    with (HERE / name).open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        return reader.fieldnames, rows


def prefix_csv(name):
    """Retain complete parsed rows; never count the final range-cut record."""
    data = (HERE / name).read_bytes()
    data = data[:data.rfind(b"\n") + 1]
    reader = csv.DictReader(io.StringIO(data.decode("utf-8")), strict=True)
    rows = []
    try:
        for row in reader:
            if None not in row and all(v is not None for v in row.values()):
                rows.append(row)
    except csv.Error:
        pass  # Prefix can terminate within a quoted multiline record.
    return reader.fieldnames, rows


def counts(values):
    return dict(sorted(collections.Counter(values).items()))


def license_prefix(attribution):
    for prefix in ("CC BY-NC ", "CC BY ", "PUBLIC DOMAIN "):
        if attribution.startswith(prefix):
            return prefix.rstrip()
    return "other_exact_string_requires_review"


MODALITY = {
    "C0002978", "C0024485", "C0032743", "C0040405", "C0041618", "C1306645"
}
ANATOMY = {
    "C0000726", "C0006141", "C0023216", "C0030797", "C0037303", "C0037949",
    "C0817096", "C1140618"
}
DIRECTIONALITY = {"C0205106", "C0205129", "C1996865", "C1999039"}
schemas = {}
schemas["roco_license"], licenses = read_csv("roco-license_information.csv")
schemas["roco_train_manual"], manual = read_csv("roco-train_concepts_manual.csv")
schemas["roco_train_captions"], captions = read_csv("roco-train_captions.csv")
schemas["roco_cui_mapping"], mapping = read_csv("roco-cui_mapping.csv")
license_map = {row["ID"]: row for row in licenses}
cui_map = {row["CUI"]: row["Canonical name"] for row in mapping}
train_ids = {row["ID"] for row in manual}
train_licenses = [row for row in licenses if row["ID"] in train_ids]
partitions = collections.defaultdict(set)
partition_ids = collections.defaultdict(set)
for row in licenses:
    split = row["ID"].split("_")[2]
    partitions[split].add(row["PMCID"])
    partition_ids[split].add(row["ID"])
labels = {row["ID"]: set(filter(None, row["CUIs"].split(";"))) for row in manual}
concept_counts = collections.Counter(cui for values in labels.values() for cui in values)
category_sets = {"modality": MODALITY, "anatomy": ANATOMY, "directionality": DIRECTIONALITY}
roco = {
    "license_rows": len(licenses),
    "license_unique_ids": len(license_map),
    "train_manual_rows": len(manual),
    "train_manual_unique_ids": len(train_ids),
    "train_caption_rows": len(captions),
    "train_caption_unique_ids": len({r["ID"] for r in captions}),
    "train_id_sets_identical": train_ids == {r["ID"] for r in captions} == partition_ids["train"],
    "partition_image_counts_from_license_metadata": {k: len(v) for k, v in partition_ids.items()},
    "partition_article_counts_from_license_metadata": {k: len(v) for k, v in partitions.items()},
    "article_intersections_from_license_metadata": {
        a + "__" + b: len(partitions[a] & partitions[b])
        for a, b in (("train", "valid"), ("train", "test"), ("valid", "test"))
    },
    "training_license_assertion_prefixes": counts(license_prefix(r["Attribution"]) for r in train_licenses),
    "all_license_assertion_prefixes": counts(license_prefix(r["Attribution"]) for r in licenses),
    "unusual_training_license_assertions": [r for r in train_licenses if license_prefix(r["Attribution"]) not in {"CC BY", "CC BY-NC"}],
    "training_license_blank_fields": {k: sum(not r[k] for r in train_licenses) for k in schemas["roco_license"]},
    "empty_manual_concept_rows": sum(not x for x in labels.values()),
    "unknown_manual_cuis": sorted(set(concept_counts) - set(cui_map)),
    "manual_cuis_not_categorized": sorted(set(concept_counts) - MODALITY - ANATOMY - DIRECTIONALITY),
    "manual_label_repeats_within_row": sum(len([x for x in r["CUIs"].split(";") if x]) != len(labels[r["ID"]]) for r in manual),
    "category_label_count_distribution": {name: counts(str(len(value & members)) for value in labels.values()) for name, members in category_sets.items()},
    "anatomy_without_plain_xray": sum(bool(value & ANATOMY) and "C1306645" not in value for value in labels.values()),
    "directionality_without_plain_xray": sum(bool(value & DIRECTIONALITY) and "C1306645" not in value for value in labels.values()),
    "manual_concepts": [{"cui": cui, "canonical_name": cui_map[cui], "count": n, "category": next(name for name, members in category_sets.items() if cui in members)} for cui, n in sorted(concept_counts.items())],
    "blank_training_captions": sum(not r["Caption"].strip() for r in captions),
    "max_training_images_per_article": max(collections.Counter(r["PMCID"] for r in train_licenses).values()),
}
schemas["pmcvqa_train"], vqa = read_csv("pmcvqa-train.csv")
schemas["pmcvqa_train_2_prefix"], vqa2 = prefix_csv("pmcvqa-train_2.prefix.csv")
schemas["pmcvqa_license_prefix"], vqa_licenses = prefix_csv("pmcvqa-license-list.prefix.csv")
figure_re = re.compile(r"^(PMC[0-9]+)_(.+)\.jpg$")
vqa_articles = set()
unparseable = []
for row in vqa:
    match = figure_re.fullmatch(row["Figure_path"])
    if match:
        vqa_articles.add(match[1])
    else:
        unparseable.append(row["Figure_path"])
vqa_image_q = collections.defaultdict(set)
for row in vqa:
    vqa_image_q[(row["Figure_path"], row["Question"].strip().casefold())].add(row["Answer"].strip().casefold())
option_dep_re = re.compile(r"\b(?:both [abcd] and [abcd]|[abcd] and [abcd]|all of the above|none of the above|all the above|none the above)\b", re.I)
prefix_license_map = {row["Accession ID"]: row for row in vqa_licenses}
pmcvqa = {
    "repository_revision": "b56ae594f794867893143b337b4118a835794647",
    "train_rows": len(vqa),
    "train_unique_figures": len({r["Figure_path"] for r in vqa}),
    "train_article_count_from_filename": len(vqa_articles),
    "train_unparseable_figure_path_count": len(unparseable),
    "train_blank_fields": {k: sum(not r[k].strip() for r in vqa) for k in schemas["pmcvqa_train"]},
    "train_answer_label_distribution": counts(r["Answer_label"] for r in vqa),
    "train_duplicate_full_rows": len(vqa) - len({tuple(r.values()) for r in vqa}),
    "train_same_figure_question_multiple_exact_normalized_answers": sum(len(v) > 1 for v in vqa_image_q.values()),
    "train_answer_option_dependency_heuristic_count": sum(bool(option_dep_re.search(r["Answer"])) for r in vqa),
    "train_answer_option_dependency_heuristic_is_not_exhaustive_or_a_quality_estimate": True,
    "train2_prefix_only_complete_records": len(vqa2),
    "train2_prefix_split_distribution": counts(r["split"] for r in vqa2),
    "train2_prefix_answer_distribution": counts(r["Answer"] for r in vqa2),
    "license_prefix_only_complete_records": len(vqa_licenses),
    "license_prefix_only_assertions": counts(r["License"] for r in vqa_licenses),
    "train_articles_found_in_license_prefix_only": len(vqa_articles & set(prefix_license_map)),
    "full_license_table_not_downloaded_or_joined": True,
    "roco_article_intersections_by_source_partition": {k: len(vqa_articles & v) for k, v in partitions.items()},
    "roco_train_images_with_article_in_pmcvqa_train": sum(r["PMCID"] in vqa_articles for r in train_licenses),
    "article_intersection_is_not_an_exact_image_duplicate_count": True,
    "heldout_pmcvqa_files_not_downloaded": True,
}
retrievals = json.loads((HERE / "retrieval-ledger.json").read_text())
checks = {
    "roco_local_md5_matches_publisher": {},
    "pmcvqa_train_sha256_matches_hub_lfs": None,
}
zenodo = json.loads((HERE / "roco-zenodo-api.json").read_text())
remote_files = {x["key"]: x for x in zenodo["files"]}
for local, remote in (("roco-license_information.csv", "license_information.csv"), ("roco-train_concepts_manual.csv", "train_concepts_manual.csv"), ("roco-train_captions.csv", "train_captions.csv"), ("roco-cui_mapping.csv", "cui_mapping.csv")):
    checks["roco_local_md5_matches_publisher"][remote] = "md5:" + hashlib.md5((HERE / local).read_bytes()).hexdigest() == remote_files[remote]["checksum"]
hub_files = json.loads((HERE / "pmcvqa-tree.json").read_text())
train_file = next(x for x in hub_files if x["path"] == "train.csv")
checks["pmcvqa_train_sha256_matches_hub_lfs"] = hashlib.sha256((HERE / "pmcvqa-train.csv").read_bytes()).hexdigest() == train_file["lfs"]["oid"]
result = {
    "schema_version": 1,
    "scope": "Bounded primary-source metadata and training-text audit; no images, no source-heldout label files, no model use approval.",
    "method_note": "ROCO license table includes heldout article identity and attribution only. Partial HTTP ranges are never treated as complete files.",
    "schemas": schemas,
    "roco": roco,
    "pmcvqa": pmcvqa,
    "integrity_checks": checks,
    "total_saved_response_body_bytes": sum(x.get("bytes", 0) for x in retrievals),
    "retrievals": retrievals,
    "archive_head": json.loads((HERE / "roco-train-images-head.json").read_text()),
    "analysis_inputs": [{"path": str(x.relative_to(PROJECT)), "bytes": x.stat().st_size, "sha256": hashlib.sha256(x.read_bytes()).hexdigest()} for x in sorted(HERE.iterdir()) if x.is_file() and x.name != "roco-metadata-audit.json"],
    "analysis_exit_code": 0,
}
path = PACKAGE / "evidence" / "source-expansion.json"
path.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"report": str(path), "roco": roco, "pmcvqa": pmcvqa, "integrity_checks": checks, "total_saved_response_body_bytes": result["total_saved_response_body_bytes"]}, indent=2))
