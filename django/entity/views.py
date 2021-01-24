from django.views.generic import DetailView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.serializers import ValidationError
from entity import serializers
from entity import models


class PreviewView(DetailView):
    model = models.Person
    template_name = "people_preview.html"
    context_object_name = "object"


class FlyoutView(DetailView):
    model = models.Person
    template_name = "people_preview.html"
    context_object_name = "object"


class PersonView(viewsets.ModelViewSet):
    model = models.Person
    serializer_class = serializers.PersonSerializer
    queryset = model.objects.prefetch_related("alt_labels")
