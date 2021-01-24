from rest_framework import serializers
from django.contrib.auth.models import User
from authority import models
import entity.models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email", "is_staff"]


class AuthoritySerializer(serializers.ModelSerializer):
    model = models.Authority


class QueriesSerializer(serializers.Serializer):
    queries = serializers.JSONField()


class ReconciliationQuerySerializer(serializers.Serializer):
    TYPE_CHOICES = (("any", "any"), ("all", "all"), ("should", "should"))

    query = serializers.CharField(max_length=4000, help_text="A string to search for.")
    limit = serializers.IntegerField(
        min_value=1,
        required=False,
        help_text="An integer to specify how many results to return.",
    )
    type = serializers.CharField(
        max_length=1000,
        required=False,
        help_text="A single string, or an array of strings, specifying the types of result",
    )
    type_strict = serializers.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        help_text='A string, one of "any", "all", "should"',
    )
    properties = serializers.ListField(
        serializers.DictField(),
        required=False,
        help_text="Array of json object literals.",
    )


class DataExtensionSettings(serializers.Serializer):
    CONTENT_CHOICES = (("id", "id"), ("label", "label"))
    limit = serializers.IntegerField(
        required=False,
    )
    content = serializers.ChoiceField(required=False, choices=CONTENT_CHOICES)


PERSON_PROPERTY_CHOICES = (
    ("pref_label", "Preferred Name"),
    ("alt_labels", "Alternative Names"),
    ("viaf_match", "VIAF exact match URI"),
    ("lcnaf_match", "LCNAF exact match URI"),
    ("birth_early", "Earliest birth date range"),
    ("birth_late", "Latest birth date range"),
    ("death_early", "Earliest death date range"),
    ("death_late", "Latest death date range"),
)


class DataExtensionPropertySerializer(serializers.Serializer):
    id = serializers.ChoiceField(choices=PERSON_PROPERTY_CHOICES)
    settings = serializers.JSONField(required=False)


class DataExtensionPropertyIndividualSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=4000)
    name = serializers.CharField(max_length=4000)


class DataExtensionPropertyProposalSerializer(serializers.Serializer):
    limit = serializers.IntegerField(
        required=False, min_value=1, help_text="Requested limit on number of properties"
    )
    type = serializers.ChoiceField(choices=(("person", "Person")))
    properties = DataExtensionPropertyIndividualSerializer(many=True)


class DataExtensionQueriesSerializer(serializers.Serializer):
    ids = serializers.PrimaryKeyRelatedField(
        queryset=entity.models.Entity.objects.all(), many=True
    )
    properties = DataExtensionPropertySerializer(many=True)


class DataExtensionWrapper(serializers.Serializer):
    extend = serializers.JSONField()


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop("fields", None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class DynamicPersonSerializer(DynamicFieldsModelSerializer):
    alt_labels = serializers.SlugRelatedField(
        queryset=entity.models.Name.objects.all(), many=True, slug_field="label"
    )

    class Meta:
        model = entity.models.Person
        fields = [
            "id",
            "pref_label",
            "alt_labels",
            "viaf_match",
            "lcnaf_match",
            "birth_early",
            "birth_late",
            "death_early",
            "death_late",
        ]
