import csv
from pathlib import Path
import tempfile
import unittest


MODALITIES = {
    'C0002978': 'angiogram',
    'C0024485': 'Magnetic Resonance Imaging',
    'C0032743': 'Positron-Emission Tomography',
    'C0040405': 'X-Ray Computed Tomography',
    'C0041618': 'Ultrasonography',
    'C1306645': 'Plain x-ray',
}


def source_id(number, split='train'):
    return f'ROCOv2_2023_{split}_{number:06d}'


def write_csv(path, fields, rows):
    with path.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        writer.writerows(rows)


class ROCOInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manual = [[source_id(i), cui] for i, cui in enumerate(MODALITIES, 1)]
        self.captions = [[row[0], 'Source caption, with punctuation.'] for row in self.manual]
        self.licenses = [[row[0], f'PMC{100 + i}', 'CC BY Author et al. (2020)',
                         f'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{100 + i}']
                         for i, row in enumerate(self.manual)]
        self.mapping = list(MODALITIES.items()) + [('C0817096', 'Chest')]

    def write(self):
        for name, header, rows in (
            ('train_concepts_manual.csv', ['ID', 'CUIs'], self.manual),
            ('train_captions.csv', ['ID', 'Caption'], self.captions),
            ('license_information.csv', ['ID', 'PMCID', 'Attribution', 'Link'], self.licenses),
            ('cui_mapping.csv', ['CUI', 'Canonical name'], self.mapping),
        ):
            write_csv(self.root / name, header, rows)

    def build(self, **kwargs):
        from mmbu_prep.roco import build_roco_inventory
        self.write()
        return build_roco_inventory(self.root, **kwargs)

    def test_join_and_semicolon_labels_preserve_unapproved_provenance(self):
        self.manual[-1][1] += ';C0817096'
        inventory, audit = self.build(per_modality=1, seed=17)
        row = inventory[-1]
        self.assertEqual(row['source_partition'], 'train')
        self.assertEqual(row['source_version'], '2.0.1')
        self.assertEqual(row['group_id'], 'pmc-literature:PMC105')
        self.assertEqual(row['manual_cuis'], ['C1306645', 'C0817096'])
        self.assertEqual(row['raw_caption'], self.captions[-1][1])
        self.assertEqual(row['raw_attribution'], self.licenses[-1][2])
        self.assertIsNone(row['original_figure_id'])
        self.assertIsNone(row['patient_id'])
        self.assertNotIn('image_sha256', row)
        self.assertNotIn('image_hash', row)
        self.assertTrue(row['metadata_only'])
        self.assertEqual(row['review_status'], 'pending')
        self.assertEqual(row['allowed_purposes'], [])
        self.assertEqual(row['aggregate_license'], 'CC-BY-NC-4.0')
        self.assertIsNone(row['upstream_license_version'])
        self.assertEqual(len(row['metadata_sha256']), 4)
        self.assertEqual(len(audit['shortlist_source_image_ids']), 6)
        self.assertFalse(audit['training_ready'])
        self.assertFalse(audit['release_integrity_verified'])

    def test_duplicate_ids_fail_in_every_joined_table(self):
        for field in ('manual', 'captions', 'licenses'):
            rows = getattr(self, field)
            rows.append(rows[0].copy())
            with self.subTest(table=field), self.assertRaises(ValueError):
                self.build()
            rows.pop()

    def test_missing_or_extra_training_join_ids_fail(self):
        self.captions.pop()
        with self.assertRaises(ValueError):
            self.build()
        self.captions.append([source_id(999), 'Unmatched caption'])
        with self.assertRaises(ValueError):
            self.build()

    def test_malformed_pmcid_or_mismatching_article_link_fail(self):
        original = self.licenses[0].copy()
        for pmcid in ('PMC', 'PMC1/../2', 'pmc100', ' PMC100', 'PMC0'):
            self.licenses[0][1] = pmcid
            with self.subTest(pmcid=pmcid), self.assertRaises(ValueError):
                self.build()
        self.licenses[0] = original
        self.licenses[0][3] = 'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC999'
        with self.assertRaises(ValueError):
            self.build()

    def test_heldout_labels_rejected_but_license_metadata_allowed(self):
        heldout = source_id(1, 'valid')
        self.licenses.append([heldout, 'PMC999', 'CC BY Author (2020)',
                              'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC999'])
        inventory, audit = self.build(per_modality=1)
        self.assertEqual(len(inventory), 6)
        self.assertEqual(audit['source_article_counts']['valid'], 1)
        self.manual.append([heldout, 'C0040405'])
        self.captions.append([heldout, 'Heldout poison label'])
        with self.assertRaises(ValueError):
            self.build()

    def test_missing_unknown_ambiguous_and_repeated_labels_stay_flagged(self):
        self.manual[0][1] = ''
        self.manual[1][1] = 'C9999999'
        self.manual[2][1] = 'C0032743;C0040405'
        self.manual[3][1] = 'C0040405;C0040405'
        inventory, audit = self.build(per_modality=1)
        self.assertEqual(len(inventory), 6)
        self.assertEqual(len(audit['shortlist_source_image_ids']), 2)
        self.assertIn('missing_modality', inventory[0]['shortlist_exclusion_reasons'])
        self.assertIn('unknown_manual_cui', inventory[1]['shortlist_exclusion_reasons'])
        self.assertIn('ambiguous_modality', inventory[2]['shortlist_exclusion_reasons'])
        self.assertIn('repeated_manual_cui', inventory[3]['shortlist_exclusion_reasons'])

    def test_rights_prefix_and_heldout_article_overlap_exclude_from_shortlist(self):
        self.licenses[0][2] = 'CC BY-NC Author (2020)'
        self.licenses[1][2] = 'CC CC-BY Author (2020)'
        self.licenses[2][2] = 'PUBLIC DOMAIN Author (2020)'
        self.licenses.append([source_id(1, 'test'), 'PMC103', 'CC BY Author (2020)',
                              'https://www.ncbi.nlm.nih.gov/pmc/articles/PMC103'])
        inventory, audit = self.build(per_modality=1)
        self.assertEqual(len(audit['shortlist_source_image_ids']), 2)
        self.assertEqual(audit['shortlist_exclusion_counts']['attribution_not_exact_cc_by_prefix'], 3)
        self.assertIn('article_crosses_source_heldout', inventory[3]['shortlist_exclusion_reasons'])
        self.assertEqual(inventory[0]['allowed_purposes'], [])

    def test_shortlist_deterministic_under_row_order_and_unique_articles(self):
        # Shared articles across modality strata test global article uniqueness.
        for number in range(7, 37):
            cui = list(MODALITIES)[number % 6]
            pmcid = f'PMC{100 + number // 2}'
            self.manual.append([source_id(number), cui])
            self.captions.append([source_id(number), 'Training caption'])
            self.licenses.append([source_id(number), pmcid, 'CC BY Author (2020)',
                                  f'https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}'])
        first, audit_first = self.build(per_modality=2, seed=1729)
        self.manual.reverse(); self.captions.reverse(); self.licenses.reverse()
        _, audit_second = self.build(per_modality=2, seed=1729)
        self.assertEqual(audit_first['shortlist_source_image_ids'], audit_second['shortlist_source_image_ids'])
        by_id = {row['source_image_id']: row for row in first}
        shortlist = [by_id[key] for key in audit_first['shortlist_source_image_ids']]
        self.assertEqual(len(shortlist), 12)
        self.assertEqual(len({row['pmcid'] for row in shortlist}), 12)
        self.assertTrue(all(row['source_partition'] == 'train' for row in shortlist))

    def test_file_aliases_do_not_create_ambiguous_acquisition_identity(self):
        from mmbu_prep.roco import build_roco_inventory
        self.write()
        for path in list(self.root.glob('*.csv')):
            path.rename(path.with_name('roco-' + path.name))
        self.assertEqual(len(build_roco_inventory(self.root)[0]), 6)
        (self.root / 'train_captions.csv').write_text((self.root / 'roco-train_captions.csv').read_text())
        with self.assertRaises(ValueError):
            build_roco_inventory(self.root)

    def test_changed_modality_mapping_fails_semantic_relabeling(self):
        self.mapping[0] = ('C0002978', 'malignant tumor')
        with self.assertRaises(ValueError):
            self.build()


if __name__ == '__main__':
    unittest.main()
