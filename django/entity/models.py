from django.db import models
from django.contrib.postgres.fields import ArrayField
from authority import mixins, namespaces
from authority.models import CloseMatch, Authority
from rdflib import Graph, namespace
from rdflib.term import URIRef
from edtf import parse_edtf, struct_time_to_date
from collections import namedtuple

"""
Abstract models used across the rest of the application
"""


class Entity(mixins.trackedModel):
    pref_label = models.CharField(
        default="", blank=True, db_index=True, max_length=5000
    )

    @property
    def viaf_match(self):
        try:
            return CloseMatch.objects.get(
                authority__namespace=namespaces.VIAF, entity=self
            ).identifier
        except:
            return None

    @property
    def lcnaf_match(self):
        try:
            return CloseMatch.objects.get(
                authority__namespace=namespaces.LOC, entity=self
            ).identifier
        except:
            return None

    def __str__(self):
        return self.pref_label

    class Meta:
        verbose_name_plural = "entities"


class Name(mixins.labeledModel, mixins.trackedModel):
    name_of = models.ForeignKey(
        "Entity", on_delete=models.CASCADE, related_name="alt_labels"
    )
    authority = models.ForeignKey(
        "authority.Authority",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="Authority that uses this name",
        related_name="names_used",
    )
    language = models.CharField(default="", blank=True, max_length=50, db_index=True)
    preferred = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Is this name considered 'preferred' by the authority using it?",
    )

    class Meta:
        unique_together = ("label", "name_of", "language", "preferred", "authority")


class Person(Entity):
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

    def process_death_edtf(self):
        processed_death = self.process_edtf(self.death_edtf)
        self.death_early = processed_death.begin
        self.death_late = processed_death.end

    def populate_from_lcnaf_graph(self, lcnaf_graph, update_viaf=False):
        """
        Given an RDF graph of LCNAF data, populate birth/death dates
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
            if namespaces.VIAF in str(o)
        ]
        if len(viaf_concept) > 0:
            viaf_graph = Graph().parse(viaf_concept[0])
            viaf_uris = [
                str(o)
                for s, p, o in viaf_graph.triples(
                    (None, URIRef(f"{namespace.FOAF}focus"), None)
                )
            ]
            if len(viaf_uris) > 0 and update_viaf:
                CloseMatch.objects.get_or_create(
                    entity=self,
                    authority=Authority.objects.get(namespace=namespaces.VIAF),
                    identifier=viaf_uris[0],
                )
                self.populate_from_viaf_graph(viaf_graph)

        self.save()

    def populate_from_lcnaf_uri(self, update_viaf=True):
        if self.lcnaf_match is None:
            return
        g = Graph().parse(f"{self.lcnaf_match}.skos.xml", format="xml")
        self.populate_from_lcnaf_graph(lcnaf_graph=g, update_viaf=update_viaf)

    def populate_from_viaf_graph(self, viaf_graph):
        viaf_uri = self.viaf_match
        # Collect other authority labels
        pref_labels = [
            {"label": o.value, "language": o.language, "subject": s}
            for s, p, o in viaf_graph.triples((None, namespace.SKOS.prefLabel, None))
            if str(s) != viaf_uri
        ]
        prefNames = []
        for l in pref_labels:
            # Get source schema
            source_schemae = [
                o
                for s, p, o in viaf_graph.triples(
                    (l["subject"], namespace.SKOS.inScheme, None)
                )
            ]
            # If there is no source schema, skip to the next name
            if len(source_schemae) == 0:
                continue
            else:
                source_schema = source_schemae[0].__str__()
            authority = Authority.objects.get_or_create(
                viaf_namespace=source_schema,
                defaults={
                    "label": source_schema,
                    "namespace": source_schema,
                },
            )[0]
            norm_language = l["language"] if l["language"] is not None else ""
            prefNames.append(
                Name(
                    name_of=self,
                    label=l["label"],
                    language=norm_language,
                    authority=authority,
                    preferred=True,
                )
            )
        Name.objects.bulk_create(prefNames, ignore_conflicts=True)

        # Assign person pref_label from VIAF's preferred labels, privilegeing english first if possible
        viaf_preferred_labels = [
            {"label": o.value, "language": o.language}
            for s, p, o in viaf_graph.triples(
                (URIRef(viaf_uri), namespace.SKOS.prefLabel, None)
            )
        ]
        viaf_en_label = [l for l in viaf_preferred_labels if l["language"] == "en-US"]
        if len(viaf_en_label) > 0:
            self.pref_label = viaf_en_label[0]["label"]
        elif len(viaf_preferred_labels) > 0:
            self.pref_label = viaf_preferred_labels[0]["label"]
        else:
            self.pref_label = pref_labels[0]["label"]

        # Collect other authority labels
        alt_labels = [
            {"label": o.value, "language": o.language, "subject": s}
            for s, p, o in viaf_graph.triples((None, namespace.SKOS.altLabel, None))
            if s is not URIRef(viaf_uri)
        ]
        altNames = []
        for l in alt_labels:
            # Get source schema
            source_schemae = [
                o
                for s, p, o in viaf_graph.triples(
                    (l["subject"], namespace.SKOS.inScheme, None)
                )
            ]
            # If there is no source schema, skip to the next name
            if len(source_schemae) == 0:
                continue
            else:
                source_schema = source_schemae[0].__str__()
            authority = Authority.objects.get_or_create(
                viaf_namespace=source_schema,
                defaults={"label": source_schema, "namespace": source_schema},
            )[0]
            norm_language = l["language"] if l["language"] is not None else ""
            altNames.append(
                Name(
                    name_of=self,
                    label=l["label"],
                    language=norm_language,
                    authority=authority,
                    preferred=False,
                )
            )
        Name.objects.bulk_create(altNames, ignore_conflicts=True)

        # Get birthdates
        birth_literals = {
            o.value
            for s, p, o in viaf_graph.triples(
                (URIRef(viaf_uri), URIRef("http://schema.org/birthDate"), None)
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
                (URIRef(viaf_uri), URIRef("http://schema.org/deathDate"), None)
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


class CorporateBody(Entity):
    class Meta:
        verbose_name_plural = "corporate bodies"


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
