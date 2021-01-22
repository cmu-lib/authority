from django.test import TestCase, Client
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from rest_framework import status
from authority import models
from authority import views
from django.core import management
import json


def noaccess(self):
    """Expect no unauthorized access to the endpoint"""
    self.assertEqual(self.client.get(self.ENDPOINT).status_code, 403)
    self.assertEqual(self.client.post(self.ENDPOINT).status_code, 403)
    self.assertEqual(self.client.delete(self.ENDPOINT).status_code, 403)


def as_auth(username="root"):
    def as_auth_name(func):
        """
        Run a test using an APIClient authorized with a particular username. Defaults to "root"
        """

        def auth_client(self):
            token = Token.objects.get(user__username=username)
            self.client = APIClient()
            self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
            return func(self)

        return auth_client

    return as_auth_name


class ReconcilationInfoView(TestCase):
    fixtures = ["test.json"]

    ENDPOINT = reverse("reconciliation_endpoint")

    def test_get(self):
        res = self.client.get(self.ENDPOINT)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for k in [
            "versions",
            "name",
            "identifierSpace",
            "schemaSpace",
            "defaultTypes",
            "view",
            "preview",
        ]:
            self.assertIn(k, res.data)


class ReconciliationQueryTest(TestCase):
    fixtures = ["test.json"]

    ENDPOINT = reverse("reconciliation_endpoint")

    def test_bad(self):
        # populate elasticsearch index
        management.call_command("search_index", "--rebuild", "-f")
        query_payload = {
            "q0": {
                "term": "andrew",
                "type": "/person",
            }
        }
        res = self.client.post(
            self.ENDPOINT, data={"queries": json.dumps(query_payload)}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post(self):
        query_payload = {
            "q0": {
                "query": "andrew",
                "limit": 5,
                "type": "/person",
                "type_strict": "should",
            },
            "q1": {
                "query": "mary",
                "limit": 5,
                "type": "/person",
                "type_strict": "should",
            },
            "q2": {
                "query": "fizzbuzz",
                "limit": 5,
                "type": "/person",
                "type_strict": "should",
            },
        }
        res = self.client.post(
            self.ENDPOINT, data={"queries": json.dumps(query_payload)}
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for qid in query_payload.keys():
            self.assertIn(qid, res.data.keys())

        q0_result = res.data["q0"]["result"]
        q1_result = res.data["q1"]["result"]
        q2_result = res.data["q2"]["result"]
        for k in ["id", "name", "score", "match"]:
            self.assertIn(k, q0_result[0])

        # Results should be ranked by descending score
        self.assertGreaterEqual(
            q0_result[0]["score"],
            q0_result[1]["score"],
        )

        # Queries should correctly find alt_labels
        self.assertGreater(len(q1_result), 0)

        # Non-matches should return no results
        self.assertEqual(len(q2_result), 0)