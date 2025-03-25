from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from momconnect.models import Clinic


class ClinicDetailsViewTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )
        token = Token.objects.get(user=self.user)
        self.api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        self.clinic = Clinic.objects.create(value="123456", name="Test Clinic")
        self.url = reverse("clinic-check")

    def test_unauthenticated_client(self):
        """
        Test that an unauthenticated client receives a 401 Unauthorized response
        when attempting to access the clinic details endpoint.
        """
        response = self.client.get(self.url, {"clinic_code": self.clinic.value})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_clinic_code(self):
        """
        Test that the endpoint returns a 400 Bad Request response
        when the clinic_code parameter is missing.
        """
        response = self.api_client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "missing clinic code"})

    def test_invalid_clinic_code(self):
        """
        Test that the endpoint returns a 400 Bad Request response
        when the clinic_code parameter is invalid.
        """
        response = self.api_client.get(self.url, {"clinic_code": "invalid"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "invalid"})

    def test_clinic_not_found(self):
        """
        Test that the endpoint returns a 404 Not Found response
        when the clinic with the provided clinic_code does not exist.
        """
        response = self.api_client.get(self.url, {"clinic_code": "999999"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"error": "clinic not found"})

    def test_successful_clinic_retrieval(self):
        """
        Test that the endpoint successfully retrieves clinic details
        when a valid clinic_code is provided.
        """
        response = self.api_client.get(self.url, {"clinic_code": self.clinic.value})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], self.clinic.value)
        self.assertEqual(response.data["name"], self.clinic.name)
