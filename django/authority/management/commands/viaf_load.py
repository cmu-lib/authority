from django.core.management.base import BaseCommand
from rdflib import Graph, namespace
from rdflib.term import URIRef
from tqdm import tqdm
import entity.models
import authority.models
from django.db import transaction
from authority import namespaces


def load_rdf_file(xmlfile, wipe=True, n_lines=None):
    if wipe:
        entity.models.Person.objects.all().delete()
    with open(xmlfile, "r") as handle:
        for line in tqdm(handle, total=n_lines):
            try:
                # The VIAF xml file is actually a tab-separated file with the ID in the first column, followed by the XML as a string in the second column
                split_line = line.split("\t")
                load_rdf_entity(split_line[0], split_line[1], wipe=wipe)
            except Exception as e:
                print(line)
                print(e)
                continue


@transaction.atomic
def load_rdf_entity(viaf_id, entity_text, wipe):
    g = Graph().parse(data=entity_text)
    # skip if not a person resource
    person = entity.models.Person.objects.create()
    person_triples = [
        s
        for s, p, o in g.triples(
            (None, namespace.RDF.type, URIRef("http://schema.org/Person"))
        )
    ]
    if len(person_triples) <= 0:
        return
    viaf_uri = f"{namespaces.VIAF}{viaf_id}"
    authority.models.CloseMatch.objects.create(
        authority_id=1, entity=person, identifier=viaf_uri
    )
    lcnaf_uris = [
        str(o)
        for s, p, o in g.triples((None, URIRef("http://schema.org/sameAs"), None))
        if namespaces.LOC in o
    ]
    if len(lcnaf_uris) > 0:
        authority.models.CloseMatch.objects.create(
            authority_id=2, entity=person, identifier=lcnaf_uris[0]
        )
    person.populate_from_viaf_graph(g)


class Command(BaseCommand):
    help = "Load VIAF SKOS RDF XML"

    def add_arguments(self, parser):
        parser.add_argument("xml", nargs="+", type=str)
        parser.add_argument("lines", nargs=1, type=int)

    def handle(self, *args, **options):
        load_rdf_file(options["xml"][0], n_lines=options["lines"][0])
