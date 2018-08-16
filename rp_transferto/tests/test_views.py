from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ProductTests(APITestCase):
    def test_get_products(self):
        """
        Product Endpoint should return response
        """
        url = reverse("rp_transferto:get_products")
        data = {"name": "test"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
