from django.test import TestCase, Client
from rest_framework.reverse import reverse
from rest_framework.test import APIClient
from authority import models
from authority import views


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
        self.assertEqual(res.status_code, 200)
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

    def test_post_reconciliation_query(self):
        pass