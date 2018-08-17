import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient


class SurveyCheckViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)

        self.assertTrue("id" in result)
        self.assertEqual(result["id"], None)

        self.assertTrue("version" in result)
        self.assertEqual(result["version"], None)
