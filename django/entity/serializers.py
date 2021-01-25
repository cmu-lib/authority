from rest_framework import serializers
from entity import models


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Person
        fields = [
            "id",
            "pref_label",
            "birth_early",
            "birth_late",
            "birth_edtf",
            "death_early",
            "death_late",
            "death_edtf",
            "viaf_match",
            "lcnaf_match",
        ]
