from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ProductTests(APITestCase):
    def test_get_products(self):
        """
        Product Endpoint should return json with list of available products
        """
        response = self.client.get(reverse("get_products"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
