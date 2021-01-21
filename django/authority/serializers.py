from rest_framework import serializers
from django.contrib.auth.models import User
from authority import models


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
