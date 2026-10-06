"""Strict ROCOv2 training metadata inventory; no image acquisition or model approval."""

from collections import Counter
import csv
import hashlib
import io
from pathlib import Path
import re
from urllib.parse import urlparse


CONVERSION = 'rocov2-manual-modality-metadata-v1'
SOURCE_VERSION = '2.0.1'
MODALITIES = {
    'C0002978': 'angiogram',
    'C0024485': 'Magnetic Resonance Imaging',
    'C0032743': 'Positron-Emission Tomography',
    'C0040405': 'X-Ray Computed Tomography',
    'C0041618': 'Ultrasonography',
    'C1306645': 'Plain x-ray',
}
ANATOMY = {'C0000726', 'C0006141', 'C0023216', 'C0030797', 'C0037303',
           'C0037949', 'C0817096', 'C1140618'}
DIRECTIONALITY = {'C0205106', 'C0205129', 'C1996865', 'C1999039'}
MANUAL_CUIS = set(MODALITIES) | ANATOMY | DIRECTIONALITY
FILES = {
    'train_concepts_manual.csv': (['ID', 'CUIs'], '29c00284c410665b6fe6ddc7f0b72f0a'),
    'train_captions.csv': (['ID', 'Caption'], 'fac7fc6bd570408f451e7558b994518a'),
    'license_information.csv': (['ID', 'PMCID', 'Attribution', 'Link'], '65f21bc4620778259b530a2c033cd4e7'),
    'cui_mapping.csv': (['CUI', 'Canonical name'], 'b12e7e3627b599b18c68dd3091294ef6'),
}
ID_PATTERN = re.compile(r'ROCOv2_2023_(train|valid|test)_[0-9]{6}')
PMCID_PATTERN = re.compile(r'PMC[1-9][0-9]*')
CUI_PATTERN = re.compile(r'C[0-9]{7}')


def _read(metadata_dir, source_filename):
    paths = [metadata_dir / name for name in (source_filename, 'roco-' + source_filename)]
    present = [path for path in paths if path.is_file()]
    if len(present) != 1:
        raise ValueError(f'Exactly one native or roco-prefixed input required: {source_filename}')
    path = present[0]
    if path.stat().st_size > 25_000_000:
        raise ValueError(f'Metadata file exceeds bounded intake size: {source_filename}')
    payload = path.read_bytes()
    header, published_md5 = FILES[source_filename]
    reader = csv.DictReader(io.StringIO(payload.decode('utf-8'), newline=''), strict=True)
    if reader.fieldnames != header:
        raise ValueError(f'Unexpected CSV header: {source_filename}')
    rows = {}
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f'Malformed CSV row: {source_filename}')
        key = row[header[0]]
        if not key or key in rows:
            raise ValueError(f'Empty or duplicate identifier in {source_filename}: {key!r}')
        rows[key] = row
        if len(rows) > 100_000:
            raise ValueError(f'Too many metadata rows: {source_filename}')
    if not rows:
        raise ValueError(f'Empty metadata table: {source_filename}')
    md5 = hashlib.md5(payload).hexdigest()
    return rows, {
        'source_filename': source_filename, 'local_filename': path.name,
        'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(), 'md5': md5,
        'published_md5': published_md5, 'matches_published_md5': md5 == published_md5,
        'source_url': f'https://zenodo.org/records/10821435/files/{source_filename}?download=1',
    }


def _source_partition(source_id):
    match = ID_PATTERN.fullmatch(source_id)
    if match is None:
        raise ValueError(f'Malformed ROCOv2 source ID: {source_id!r}')
    return match[1]


def _attribution_prefix(value):
    for prefix in ('CC BY-NC ', 'CC BY ', 'PUBLIC DOMAIN '):
        if value.startswith(prefix) and value[len(prefix):].strip():
            return prefix.rstrip()
    return 'unrecognized'


def build_roco_inventory(metadata_dir, *, per_modality=4, seed=1729):
    """Return ``(metadata_records, audit)`` without writing or acquiring anything.

    Only source-native training labels/captions are accepted. All-split license
    metadata may be read to flag article crossings; no heldout labels are needed.
    The shortlist is an engineering inspection sample, not an approved split.
    Sort each modality by SHA256(seed NUL CUI NUL source ID), process CUIs in
    lexical order, and take up to ``per_modality`` records with unused articles.
    Exact ``CC BY `` attribution is only a provenance filter; the aggregate NC
    declaration and unverified upstream license versions apply to every result.
    """
    if type(per_modality) is not int or per_modality < 1:
        raise ValueError('per_modality must be a positive integer')
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    metadata_dir = Path(metadata_dir)
    tables = {}
    receipts = {}
    for filename in FILES:
        tables[filename], receipts[filename] = _read(metadata_dir, filename)
    manual = tables['train_concepts_manual.csv']
    captions = tables['train_captions.csv']
    licenses = tables['license_information.csv']
    mapping = tables['cui_mapping.csv']
    for cui, row in mapping.items():
        if CUI_PATTERN.fullmatch(cui) is None or not row['Canonical name'].strip():
            raise ValueError(f'Malformed CUI mapping: {cui!r}')
    for cui, expected_name in MODALITIES.items():
        if cui not in mapping or mapping[cui]['Canonical name'] != expected_name:
            raise ValueError(f'Missing or changed canonical modality mapping: {cui}')
    for table in (manual, captions):
        if any(_source_partition(key) != 'train' for key in table):
            raise ValueError('Only source-training captions and concepts are accepted')
    partitions = {key: set() for key in ('train', 'valid', 'test')}
    articles = {key: set() for key in partitions}
    for source_id, row in licenses.items():
        partition = _source_partition(source_id)
        pmcid = row['PMCID']
        if PMCID_PATTERN.fullmatch(pmcid) is None:
            raise ValueError(f'Malformed PMCID: {pmcid!r}')
        link = urlparse(row['Link'])
        allowed_article_paths = {f'/pmc/articles/{pmcid}', f'/articles/{pmcid}'}
        if (link.scheme not in {'http', 'https'} or
                link.netloc not in {'www.ncbi.nlm.nih.gov', 'ncbi.nlm.nih.gov', 'pmc.ncbi.nlm.nih.gov'} or
                link.path.rstrip('/') not in allowed_article_paths or link.query or link.fragment):
            raise ValueError(f'Article link does not identify the supplied PMCID: {source_id}')
        if not row['Attribution'].strip():
            raise ValueError(f'Missing attribution assertion: {source_id}')
        partitions[partition].add(source_id)
        articles[partition].add(pmcid)
    if set(manual) != set(captions) or set(manual) != partitions['train']:
        raise ValueError('Training concepts, captions and license IDs must join exactly')
    if any(not row['Caption'].strip() for row in captions.values()):
        raise ValueError('Training captions must be nonblank')
    crossed_articles = articles['train'] & (articles['valid'] | articles['test'])
    metadata_hashes = {name: rec['sha256'] for name, rec in receipts.items()}
    inventory = []
    for source_id in sorted(manual):
        raw_cuis = manual[source_id]['CUIs']
        cuis = raw_cuis.split(';') if raw_cuis else []
        unique_cuis = set(cuis)
        modality_cuis = sorted(unique_cuis & set(MODALITIES))
        license_row = licenses[source_id]
        prefix = _attribution_prefix(license_row['Attribution'])
        exclusions = []
        if not modality_cuis:
            exclusions.append('missing_modality')
        elif len(modality_cuis) > 1:
            exclusions.append('ambiguous_modality')
        if any(cui not in MANUAL_CUIS or cui not in mapping for cui in cuis):
            exclusions.append('unknown_manual_cui')
        if len(unique_cuis) != len(cuis):
            exclusions.append('repeated_manual_cui')
        if unique_cuis & (ANATOMY | DIRECTIONALITY) and 'C1306645' not in unique_cuis:
            exclusions.append('xray_context_without_xray_modality')
        if prefix != 'CC BY':
            exclusions.append('attribution_not_exact_cc_by_prefix')
        if license_row['PMCID'] in crossed_articles:
            exclusions.append('article_crosses_source_heldout')
        modality = modality_cuis[0] if len(modality_cuis) == 1 else None
        inventory.append({
            'schema_version': 1, 'record_kind': 'quarantined_source_training_metadata',
            'metadata_record_id': 'rocov2:' + source_id + ':manual-modality',
            'metadata_only': True, 'training_ready': False, 'source_id': 'rocov2',
            'source_family': 'pmc-literature', 'source_version': SOURCE_VERSION,
            'source_doi': '10.5281/zenodo.10821435', 'source_partition': 'train',
            'source_image_id': source_id, 'pmcid': license_row['PMCID'],
            'group_id': 'pmc-literature:' + license_row['PMCID'],
            'original_figure_id': None, 'patient_id': None,
            'article_url': license_row['Link'], 'raw_attribution': license_row['Attribution'],
            'attribution_prefix': prefix, 'aggregate_license': 'CC-BY-NC-4.0',
            'upstream_license_version': None, 'upstream_license_uri': None,
            'raw_caption': captions[source_id]['Caption'], 'raw_manual_cuis': raw_cuis,
            'manual_cuis': cuis,
            'manual_concepts': [{'cui': cui, 'canonical_name': mapping.get(cui, {}).get('Canonical name')} for cui in cuis],
            'modality_cui': modality, 'modality_label': MODALITIES.get(modality),
            'annotation_origin': 'source-manual-concepts', 'conversion_version': CONVERSION,
            'proposed_task': 'global_classification', 'proposed_subtype': 'modality',
            'proposed_question': 'Which imaging modality is shown in this image?',
            'proposed_answer': MODALITIES.get(modality),
            'review_status': 'pending', 'allowed_purposes': [],
            'review_flags': ['image_not_acquired', 'conversion_not_visually_reviewed',
                             'aggregate_nc_license', 'upstream_license_version_unverified',
                             'original_figure_lineage_unknown', 'model_use_not_approved'] + exclusions,
            'shortlist_exclusion_reasons': exclusions, 'metadata_sha256': metadata_hashes,
        })
    eligible = [row for row in inventory if not row['shortlist_exclusion_reasons']]
    shortlist = []
    used_articles = set()
    selection_counts = {}
    article_skips = {}
    for cui in sorted(MODALITIES):
        candidates = [row for row in eligible if row['modality_cui'] == cui]
        ranked = sorted(candidates, key=lambda row: (
            hashlib.sha256(f'{seed}\0{cui}\0{row["source_image_id"]}'.encode('utf-8')).hexdigest(),
            row['source_image_id']))
        chosen = 0
        skipped = 0
        for row in ranked:
            if chosen == per_modality:
                break
            if row['pmcid'] in used_articles:
                skipped += 1
                continue
            shortlist.append(row['source_image_id'])
            used_articles.add(row['pmcid'])
            chosen += 1
        selection_counts[cui] = chosen
        article_skips[cui] = skipped
    audit = {
        'schema_version': 1, 'kind': 'roco_training_metadata_quarantine',
        'conversion_version': CONVERSION, 'source_version': SOURCE_VERSION,
        'training_ready': False, 'model_executed': False, 'images_acquired': False,
        'heldout_labels_opened': False, 'allowed_purposes': [],
        'source_image_counts': {key: len(value) for key, value in partitions.items()},
        'source_article_counts': {key: len(value) for key, value in articles.items()},
        'source_article_intersections': {
            a + '__' + b: len(articles[a] & articles[b])
            for a, b in (('train', 'valid'), ('train', 'test'), ('valid', 'test'))},
        'metadata_files': receipts,
        'release_integrity_verified': all(rec['matches_published_md5'] for rec in receipts.values()),
        'inventory_records': len(inventory), 'eligible_shortlist_pool': len(eligible),
        'excluded_from_shortlist_pool': len(inventory) - len(eligible),
        'shortlist_exclusion_counts': dict(sorted(Counter(
            reason for row in inventory for reason in row['shortlist_exclusion_reasons']).items())),
        'shortlist_exclusion_counts_can_overlap': True,
        'attribution_prefix_counts': dict(sorted(Counter(row['attribution_prefix'] for row in inventory).items())),
        'modality_counts': dict(sorted(Counter(row['modality_cui'] or 'missing_or_ambiguous' for row in inventory).items())),
        'shortlist_source_image_ids': shortlist,
        'shortlist_selection': {
            'seed': seed, 'requested_per_modality': per_modality,
            'algorithm': 'lexical CUI order; ascending SHA256(seed NUL CUI NUL source_image_id), then ID; globally unique PMCID',
            'modality_order': sorted(MODALITIES), 'selected_counts': selection_counts,
            'duplicate_article_candidates_skipped': article_skips,
            'provenance_filter': 'exact CC BY attribution prefix only; not rights clearance',
            'sampling_scope': 'conversion inspection only; not representative performance evaluation',
        },
        'remaining_checks': ['MMBU eligibility and source overlap disposition',
                             'aggregate and upstream rights/release review',
                             'source image bytes, dimensions and figure provenance',
                             'image-supported modality and conversion review'],
    }
    return inventory, audit
