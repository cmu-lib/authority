from django.conf import settings
from django.views import View
from django.shortcuts import render
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from authority import serializers
from entity import documents


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

    def get(self, request, format=None):
        payload = {
            "versions": ["0.2"],
            "name": "CMU Authority Reconciliation Service",
            "identifierSpace": "http://localhost/",
            "schemaSpace": "http://localhost/",
            "view": {"url": "http://localhost/person/{{id}}"},
            "defaultTypes": [
                {"id": "/people", "name": "People"},
            ],
            "preview": {
                "height": 200,
                "width": 300,
                "url": "http://localhost/reconcile/preview/{{id}}",
            },
            "extend": {
                "propose_properties": {
                    "service_url": "http://localhost/",
                    "serivce_path": reverse("reconcile-properties"),
                },
                "property_settings": [
                    {
                        "name": "limit",
                        "label": "Limit",
                        "type": "number",
                        "default": 0,
                        "help_text": "Maximum number of values to return per row (0 for no limit)",
                    },
                    {
                        "name": "cmu_uri",
                        "label": "CMU URI",
                        "type": "select",
                        "default": "literal",
                        "help_text": "Content type: ID or literal",
                        "choices": [
                            {"value": "id", "name": "ID"},
                            {"value": "literal", "name": "Literal"},
                        ],
                    },
                ],
            },
            # "suggest": {},
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
                "type": [{"id": "/people", "name": "Person"}],
                "score": hit.meta.score,
                "match": is_match(serialized_query, hit),
            }
            formatted_response.append(result)

        return formatted_response

    def post(self, request, format=None):

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


class DataExtensionEndpoint(APIView):
    permission_classes = [AllowAny]
    max_returned_items = settings.RECONCILIATION_MAX_RETURN

    def post(self, request, format=None):
        pass