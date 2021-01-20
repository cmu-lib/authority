from rest_framework import serializers
from entity import models


class PersonSerializer(serializers.ModelSerializer):
    model = models.Person
    fields = [
        "id",
        "url",
        "label",
        "pref_label",
        "birth_date",
        "death_date",
        "viaf_match",
    ]
