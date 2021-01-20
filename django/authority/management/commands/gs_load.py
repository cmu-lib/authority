from django.core.management.base import BaseCommand
from entity import models
from django.db import transaction
import csv
from tqdm import tqdm


@transaction.atomic
def load_person(row):
    try:
        if row["Term"] is not None:
            person = models.Person.objects.create(pref_label=row["Term"])
            if row["Authority File"] == "VIAF":
                person.viaf_match = row["URI"]
                person.save()
                person.populate_from_viaf_uri()
            elif row["Authority File"] == "Library of Congress":
                person.lcnaf_match = row["URI"]
                person.save()
                person.populate_from_lcnaf_uri()
            else:
                return
    except Exception as e:
        print(e)
        print(row)
        return


class Command(BaseCommand):
    help = "Load existing CSV of "

    def add_arguments(self, parser):
        parser.add_argument("csv", nargs="+", type=str)

    def handle(self, *args, **options):
        with open(options["csv"][0], "r") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in tqdm(reader):
                load_person(row)
