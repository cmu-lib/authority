from django.test import TestCase
from entity import models


class EDTFTest(TestCase):
    def test_edtf_parse(self):
        p = models.Person(birth_edtf="1901", death_edtf="1972-11")
        self.assertIsNone(p.birth_early)
        self.assertIsNone(p.birth_late)
        p.process_birth_edtf()
        self.assertGreater(p.birth_late, p.birth_early)

        self.assertIsNone(p.death_early)
        self.assertIsNone(p.death_late)
        p.process_death_edtf()
        self.assertGreater(p.death_late, p.death_early)


class PersonVIAFImportTest(TestCase):
    def test_load_viaf(self):
        simon = models.Person(viaf_match="http://viaf.org/viaf/29540765")
        simon.save()
        self.assertEqual(simon.death_edtf, "")
        self.assertIsNone(simon.death_early)
        self.assertIsNone(simon.death_late)
        self.assertEquals(simon.birth_edtf, "")
        self.assertIsNone(simon.birth_early)
        self.assertIsNone(simon.birth_late)
        self.assertEqual(simon.alt_labels.count(), 0)
        simon.populate_from_viaf_uri()
        self.assertNotEqual(simon.death_edtf, "")
        self.assertIsNotNone(simon.death_early)
        self.assertIsNotNone(simon.death_late)
        self.assertNotEqual(simon.birth_edtf, "")
        self.assertIsNotNone(simon.birth_early)
        self.assertIsNotNone(simon.birth_late)
        self.assertGreater(simon.alt_labels.count(), 0)