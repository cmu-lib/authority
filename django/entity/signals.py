from django.db.models.signals import post_save
from django.dispatch import receiver
from entity import models
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from edtf import parse_edtf


# @receiver(post_save, sender=models.CloseMatch)
# def update_close_match(sender, **kwargs):
#     close_match = kwargs["instance"]
#     viaf_populate(close_match)


# @receiver(post_save, sender=models.Person)
# def update_person(sender, **kwargs):
#     person = kwargs["instance"]
#     viaf_match = person.close_matches.filter(authority__label="VIAF")
#     if viaf_match:
#         viaf_populate(viaf_match.first())
