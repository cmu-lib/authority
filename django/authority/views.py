from django.conf import settings
from django.views import View
from django.shortcuts import render
from django.db.models import QuerySet
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework_jsonp.renderers import JSONPRenderer
from authority import serializers
from entity import documents, models
import entity.serializers
import json


class GetSerializerClassMixin(object):
    def get_queryset(self):
        try:
            return self.queryset_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_queryset()

    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super().get_serializer_class()


class HomeView(View):
    def get_context_data(self):
        return {
            "title": "CMU Libraries Authority",
            "subtitle": "lorem ipsum dolor",
            "contents": "instructions go here Sunt nostrud adipisicing minim velit occaecat deserunt. Non labore ea labore qui deserunt minim exercitation proident. Excepteur do tempor cillum aliqua quis est qui consectetur dolore. Elit Lorem est culpa do do id aliquip in consequat ut irure dolore cupidatat.",
        }

    def get(self, request):
        return render(request, "home.html", self.get_context_data())


class CurrentUserView(APIView):
    def get(self, request, format=None):
        current_user = request.user
        serialized_user = serializers.UserSerializer(
            current_user, context={"request": request}
        )
        return Response(serialized_user.data, status=status.HTTP_200_OK)


class ReconciliationEndpoint(APIView):
    permission_classes = [AllowAny]
    max_returned_items = settings.RECONCILIATION_MAX_RETURN
    renderer_classes = [JSONRenderer]

    def get(self, request, format=None):
        payload = {
            "versions": ["0.1", "0.2"],
            "name": "CMU Authority Reconciliation Service",
            "identifierSpace": "http://localhost/",
            "schemaSpace": "http://localhost/",
            "view": {"url": "http://localhost/person/{{id}}"},
            "defaultTypes": [
                {"id": "person", "name": "People"},
            ],
            "preview": {
                "height": 200,
                "width": 300,
                "url": "http://localhost/reconcile/preview/{{id}}",
            },
            "extend": {
                "propose_properties": {
                    "service_url": "http://localhost",
                    "service_path": reverse("reconcile-extend"),
                },
                "property_settings": [],
            },
            "suggest": {
                "property": {
                    "service_url": "http://localhost",
                    "service_path": reverse("reconcile-suggest"),
                }
            },
        }
        return Response(payload, status=status.HTTP_200_OK)

    def query_es(self, serialized_query):
        def is_match(serialized_query, hit):
            """
            Is this match high enough in the results to be an automatic match?
            """
            # TODO Fill in actual method
            return False

        def items_slice(serialized_query):
            try:
                if serialized_query["limit"] <= self.max_returned_items:
                    return serialized_query["limit"]
                else:
                    return self.max_returned_items
            except:
                return self.max_returned_items

        query = serialized_query["query"]
        es_response = documents.PersonDocument().reconciliation_search(
            query=query, max_items=self.max_returned_items
        )
        formatted_response = []
        for hit in es_response:
            result = {
                "id": hit.id,
                "name": hit.pref_label,
                "type": [{"id": "person", "name": "Person"}],
                "score": hit.meta.score,
                "match": is_match(serialized_query, hit),
            }
            formatted_response.append(result)

        return formatted_response

    def post_reconcile(self, request):
        queries_serializer = serializers.QueriesSerializer(data=request.data)

        if not queries_serializer.is_valid():
            return Response(
                queries_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        query_data = queries_serializer.validated_data["queries"]
        payload = {}
        for idx, val in query_data.items():
            serializer = serializers.ReconciliationQuerySerializer(data=val)
            if not serializer.is_valid():
                return Response(
                    {idx: serializer.errors}, status=status.HTTP_400_BAD_REQUEST
                )
            res = self.query_es(serialized_query=serializer.validated_data)
            payload[idx] = {"result": res}

        return Response(payload, status=status.HTTP_200_OK)

    def post_extend(self, request):
        extension_request = serializers.DataExtensionWrapper(data=request.data)
        if not extension_request.is_valid():
            return Response(
                [
                    {
                        "extend": "Requests must be made with application/x-www-form-urlencoded bodies containing a data extension query in a form element named 'extend'",
                    },
                    extension_request.errors,
                ],
                status=status.HTTP_400_BAD_REQUEST,
            )
        extension_serializer = serializers.DataExtensionQueriesSerializer(
            data=extension_request.validated_data["extend"]
        )
        if not extension_serializer.is_valid():
            return Response(
                extension_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Construct meta
        extension_data = extension_serializer.validated_data
        requested_field_names = [
            i["id"] for i in extension_serializer.validated_data["properties"]
        ]
        meta_payload = [
            {"id": i, "name": s}
            for i, s in serializers.PERSON_PROPERTY_CHOICES
            if i in requested_field_names
        ]

        rows_payload = {}
        for e in extension_data["ids"]:
            person = e.person
            serialized_e = entity.serializers.PersonSerializer(person)
            entity_payload = {}
            for k, v in serialized_e.data.items():
                if k in requested_field_names:
                    if isinstance(v, list):
                        entity_payload[k] = [{"str": val} for val in v]
                    else:
                        entity_payload[k] = [{"str": v}]
                    rows_payload[e.id] = entity_payload

        complete_payload = {"meta": meta_payload, "rows": rows_payload}

        return Response(complete_payload, status.HTTP_200_OK)

    def post(self, request, format=None):

        if "queries" in request.data:
            return self.post_reconcile(request)
        elif "extend" in request.data:
            return self.post_extend(request)
        else:
            return Response(
                {
                    "error": "POST request must either include the field 'queries' or 'extend'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class DataExtensionEndpoint(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        entity_type = request.query_params.get("type", None)
        property_limit = request.query_params.get("limit", None)

        if entity_type == "person":
            serialized_properties = []
            for i, n in serializers.PERSON_PROPERTY_CHOICES:
                property_serializer = (
                    serializers.DataExtensionPropertyIndividualSerializer(
                        data={"id": i, "name": n}
                    )
                )
                property_serializer.is_valid()
                serialized_properties.append(property_serializer.validated_data)
            proposal_payload = {"type": "person"}
            if property_limit is not None:
                try:
                    proposal_payload["limit"] = int(property_limit)
                except:
                    pass

            proposal_payload["properties"] = serialized_properties
            proposal_payload["type"] = "person"
            proposal_serializer = serializers.DataExtensionPropertyProposalSerializer(
                data=proposal_payload
            )
            if not proposal_serializer.is_valid():
                return Response(
                    proposal_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                proposal_serializer.validated_data,
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"type": f"Type '{entity_type}' is not valid"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SuggestEndpoint(APIView):
    permission_class = [AllowAny]

    PERSON_FIELDS = [
        {"id": f.name, "name": f.verbose_name, "description": f.help_text}
        for f in entity.models.Person._meta.fields
    ]

    def get(self, request, format=None):
        query_prefix = request.query_params.get("prefix", None)
        query_cursor = request.query_params.get("cursor", None)
        if query_prefix is None:
            return Response(
                {
                    "prefix": "Suggest service query must contain the URL query parameter 'prefix'"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        suggest_serializer = serializers.SuggestQuerySerializer(
            data={"prefix": query_prefix, "cursor": query_cursor}
        )
        if not suggest_serializer.is_valid():
            return Response(
                suggest_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        suggest_response = {
            "result": [
                f
                for f in self.PERSON_FIELDS
                if suggest_serializer.validated_data["prefix"] in f["id"]
            ]
        }

        return Response(suggest_response, status=status.HTTP_200_OK)
