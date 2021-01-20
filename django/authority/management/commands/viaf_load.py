from django.core.management.base import BaseCommand
from rdflib import Graph, namespace
from rdflib.term import URIRef
from tqdm import tqdm
from entity import models
from django.db import transaction


def load_rdf_file(xmlfile):
    with open(xmlfile, "r") as handle:
        for line in tqdm(handle):
            try:
                load_rdf_entity(line)
            except Exception as e:
                print(e)
                continue


@transaction.atomic
def load_rdf_entity(entity_text):
    g = Graph().parse(data=entity_text)
    # skip if not a person resource
    person_triples = [
        s
        for s, p, o in g.triples(
            (None, namespace.RDF.type, URIRef("http://schema.org/Person"))
        )
    ]
    if len(person_triples) <= 0:
        return
    viaf_uri = [
        str(s) for s, p, o in g.triples((None, URIRef("http://schema.org/name"), None))
    ][0]
    lcnaf_uri = [
        str(o)
        for s, p, o in g.triples((None, URIRef("http://schema.org/sameAs"), None))
        if "http://id.loc.gov/authorities/names/" in o
    ]
    if len(lcnaf_uri) > 0:
        person = models.Person.objects.get_or_create(
            viaf_match=viaf_uri, lcnaf_match=lcnaf_uri[0]
        )[0]
    person = models.Person.objects.get_or_create(viaf_match=viaf_uri)[0]
    person.populate_from_viaf_graph(g)


class Command(BaseCommand):
    help = "Load VIAF SKOS RDF XML"

    def add_arguments(self, parser):
        parser.add_argument("xml", nargs="+", type=str)

    def handle(self, *args, **options):
        load_rdf_file(options["xml"][0])
