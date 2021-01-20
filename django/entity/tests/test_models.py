from django.test import TestCase
from entity import models


class PersonVIAFImportTest(TestCase):
    fixtures = ["test.json"]

    def test_load_viaf(self):
        pass
