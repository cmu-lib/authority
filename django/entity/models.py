from django.db import models
from django.contrib.postgres.fields import ArrayField
from authority import mixins
from rdflib import Graph, namespace
from rdflib.term import URIRef
from edtf import parse_edtf, struct_time_to_date
from collections import namedtuple

"""
Abstract models used across the rest of the application
"""


class Entity(mixins.trackedModel):
    pass

    class Meta:
        verbose_name_plural = "entities"


class Name(mixins.labeledModel, mixins.trackedModel):
    name_of = models.ForeignKey(
        "Person", on_delete=models.CASCADE, related_name="alt_labels"
    )
    language = models.CharField(default="", blank=True, max_length=50, db_index=True)

    class Meta:
        unique_together = ("label", "name_of")


class Person(Entity):
    pref_label = models.CharField(default="", blank=True, db_index=True, max_length=5000)
    birth_edtf = models.CharField(
        default="",
        blank=True,
        max_length=1000,
        verbose_name="Birth date expressed in EDTF",
    )
    birth_early = models.DateField(null=True, blank=True)
    birth_late = models.DateField(null=True, blank=True)
    death_edtf = models.CharField(
        default="",
        blank=True,
        max_length=1000,
        verbose_name="Death date expressed in EDTF",
    )
    death_early = models.DateField(null=True, blank=True)
    death_late = models.DateField(null=True, blank=True)
    viaf_match = models.URLField(
        unique=True,
        null=True,
        blank=True,
        help_text="VIAF URI for this person",
        verbose_name="VIAF match",
    )
    lcnaf_match = models.URLField(
        unique=True,
        null=True,
        blank=True,
        help_text="LCNAF URI for this person",
        verbose_name="LCNAF match",
    )

    class Meta:
        verbose_name_plural = "people"

    def process_edtf(self, d):
        ProcessedEDTF = namedtuple("ProcessedEDTF", "string begin end")
        edtf_date = parse_edtf(d)
        start_date = struct_time_to_date(edtf_date.lower_strict())
        end_date = struct_time_to_date(edtf_date.upper_strict())
        return ProcessedEDTF(str(edtf_date), start_date, end_date)

    def process_birth_edtf(self):
        processed_birth = self.process_edtf(self.birth_edtf)
        self.birth_early = processed_birth.begin
        self.birth_late = processed_birth.end
        self.save()

    def process_death_edtf(self):
        processed_death = self.process_edtf(self.death_edtf)
        self.death_early = processed_death.begin
        self.death_late = processed_death.end
        self.save()

    def populate_from_lcnaf_graph(self, lcnaf_graph):
        """
        Given an RDF graph of LCNAF data, populate
        """
        core_data = [
            (str(s), o.value)
            for s, p, o in lcnaf_graph.triples((None, namespace.SKOS.prefLabel, None))
        ][0]
        prefLabel = core_data[1]
        altLabels = []
        for s, p, o in lcnaf_graph.triples((None, namespace.SKOS.altLabel, None)):
            lang = o.language
            if lang is None:
                lang = ""
            altLabels.append({"value": o.value, "lang": lang})
        self.label = prefLabel
        self.pref_label = prefLabel
        alt_labels = [
            Name(name_of=self, label=l["value"], language=l["lang"]) for l in altLabels
        ]
        Name.objects.bulk_create(alt_labels, ignore_conflicts=True)

        viaf_concept = [
            str(o)
            for s, p, o in lcnaf_graph.triples((None, namespace.SKOS.exactMatch, None))
            if "http://viaf.org/viaf/" in str(o)
        ]
        if len(viaf_concept) > 0:
            viaf_graph = Graph().parse(viaf_concept[0])
            viaf_uris = [
                str(s)
                for s, p, o in viaf_graph.triples(
                    (None, URIRef("http://schema.org/name"), None)
                )
            ]
            if len(viaf_uris) > 0:
                self.viaf_match = viaf_uris[0]
                self.populate_from_viaf_graph(viaf_graph)

        self.save()

    def populate_from_lcnaf_uri(self):
        if self.lcnaf_match is None:
            return
        g = Graph().parse(f"{self.lcnaf_match}.skos.xml", format="xml")
        self.populate_from_lcnaf_graph(lcnaf_graph=g)

    def populate_from_viaf_graph(self, viaf_graph):

        pref_labels = [
            o for s, p, o in viaf_graph.triples((None, namespace.SKOS.prefLabel, None))
        ]
        en_pref_labels = [
            o.value
            for o in pref_labels
            if o.language is not None and "en" in o.language
        ]
        if len(en_pref_labels) > 0:
            self.pref_label = en_pref_labels[0]
        else:
            self.pref_label = pref_labels[0].value

        altLabels = []
        for s, p, o in viaf_graph.triples((None, namespace.SKOS.altLabel, None)):
            lang = o.language
            if lang is None:
                lang = ""
            altLabels.append({"value": o.value, "lang": lang})
        alt_labels = [
            Name(name_of=self, label=l["value"], language=l["lang"]) for l in altLabels
        ]
        Name.objects.bulk_create(alt_labels, ignore_conflicts=True)

        # Get birthdates
        birth_literals = {
            o.value
            for s, p, o in viaf_graph.triples(
                (None, URIRef("http://schema.org/birthDate"), None)
            )
        }
        birth_start = None
        birth_end = None
        for d in birth_literals:
            try:
                self.birth_edtf = d
                self.process_birth_edtf()
                break
            except Exception as e:
                continue

        # Get deathdates
        death_literals = birth_literals = {
            o.value
            for s, p, o in viaf_graph.triples(
                (None, URIRef("http://schema.org/deathDate"), None)
            )
        }
        death_start = None
        death_end = None
        for d in death_literals:
            try:
                self.death_edtf = d
                self.process_death_edtf()
                break
            except:
                continue

        self.save()

    def populate_from_viaf_uri(self):
        if self.viaf_match is None:
            return
        g = Graph().parse(f"{self.viaf_match}/rdf.xml", format="xml")
        self.populate_from_viaf_graph(viaf_graph=g)

    def __str__(self):
        return self.pref_label


class Concept(Entity):
    broader = models.ManyToManyField("Concept", related_name="narrower_items")
    narrower = models.ManyToManyField("Concept", related_name="broader_items")

    class Meta:
        pass


# class Predicate(
#     userCreatedModel, uniqueLabledModel, descriptionModel, URIModel, dateModifiedModel
# ):
#     authority = models.ForeignKey(
#         "Authority", on_delete=models.CASCADE, related_name="predicates"
#     )


# class Relation(userCreatedModel, dateModifiedModel):
#     source = models.ForeignKey(
#         Entity, on_delete=models.CASCADE, related_name="statements_from"
#     )
#     target = models.ForeignKey(
#         Entity, on_delete=models.CASCADE, related_name="statements_to"
#     )
#     relation_type = models.ForeignKey(
#         Predicate, on_delete=models.CASCADE, related_name="used_in_statements"
#     )

#     class Meta:
#         unique_together = ("source", "target", "relation_type")
