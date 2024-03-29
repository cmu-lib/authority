from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Q
from entity import models


@registry.register_document
class PersonDocument(Document):
    alt_labels = fields.NestedField(properties={"label": fields.TextField()})

    class Index:
        name = "people"
        settings = {"number_of_shards": 1, "number_of_replicas": 0}

    class Django:
        model = models.Person
        fields = [
            "id",
            "pref_label",
            "birth_edtf",
            "birth_early",
            "birth_late",
            "death_edtf",
            "death_early",
            "death_late",
        ]
        related_models = [models.Name]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("alt_labels")

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, models.Name):
            return related_instance.name_of

    def reconciliation_search(self, query, max_items):
        """
        Define the search that works best for common reconciliation needs, weighting matches to a preferred label more than matches to alt_labels
        """
        q_expr = self.search().query(
            Q("multi_match", query=query, fields=["pref_label^5"], fuzziness="AUTO")
            | Q(
                "nested",
                path="alt_labels",
                query=Q(
                    "multi_match",
                    query=query,
                    fields=["alt_labels.label^1"],
                    fuzziness="AUTO",
                ),
            )
        )[0:max_items]
        return q_expr
