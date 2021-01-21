from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
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
            "birth_early",
            "birth_late",
            "death_early",
            "death_late",
        ]
        related_models = [models.Name]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("alt_labels")

    def get_instances_from_related(self, related_instance):
        if isinstance(related_instance, models.Name):
            return related_instance.name_of
