from django.views.generic import DetailView
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.serializers import ValidationError
from entity import serializers
from entity import models
from django.contrib import messages
from django.shortcuts import render, reverse, redirect

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

class PopulateVIAF(DetailView):
    model = models.Person
    context_object_name = "object"
    redirect_url_name = "admin:entity_person_change"

    def get(self, request, pk=None):
        person = self.get_object()
        if person.viaf_match is None:
            messages.warning(request, "No VIAF match entered. Save the Person record first before trying to auto-populate it.")
        else:
            try:
                person.populate_from_viaf_uri()
                messages.success(request, f"{person} populated from {person.viaf_match}")
            except Exception as e:
                messages.danger(request, e)

        return redirect(reverse(self.redirect_url_name, args=[person.id]))

class PopulateLCNAF(DetailView):
    model = models.Person
    context_object_name = "object"
    redirect_url_name = "admin:entity_person_change"

    def get(self, request, pk=None):
        person = self.get_object()
        if person.lcnaf_match is None:
            messages.warning(request, "No LCNAF match entered. Save the Person record first before trying to auto-populate it.")
        else:
            try:
                person.populate_from_lcnaf_uri()
                messages.success(request, f"{person} populated from {person.lcnaf_match}")
            except Exception as e:
                messages.danger(request, e)

        return redirect(reverse(self.redirect_url_name, args=[person.id]))