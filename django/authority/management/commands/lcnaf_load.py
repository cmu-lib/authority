from django.core.management.base import BaseCommand
from rdflib import Graph, namespace
from tqdm import tqdm
import entity.models
import authority.models
from django.db import transaction


def load_rdf_file(xmlfile, n_lines=None):
    entity.models.Person.objects.delete()
    with open(xmlfile, "r") as handle:
        for line in tqdm(handle, total=n_lines):
            try:
                load_rdf_entity(line)
            except Exception as e:
                print(e)
                print(line)
                continue


@transaction.atomic
def load_rdf_entity(entity_text):
    g = Graph().parse(data=entity_text)
    lcnaf_uri = [
        str(s) for s, p, o in g.triples((None, namespace.SKOS.prefLabel, None))
    ][0]
    person = models.Person.objects.create()
    authority.models.CloseMatch.objects.create(
        authority_id=2, entity=person, identifier=lcnaf_uri
    )
    person.populate_from_lcnaf_graph(g)


class Command(BaseCommand):
    help = "Load LCNAF SKOS RDF XML"

    def add_arguments(self, parser):
        parser.add_argument("xml", nargs="+", type=str)
        parser.add_argument("lines", nargs=1, type=int)

    def handle(self, *args, **options):
        load_rdf_file(options["xml"][0], n_lines=options["lines"][0])
