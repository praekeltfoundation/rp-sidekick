import json

from mock import patch
from unittest.mock import MagicMock
from django.urls import reverse
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient

from rp_transferto.utils import TransferToClient
from .constants import (
    PING_RESPONSE_DICT,
    MSISDN_INFO_RESPONSE_DICT,
    RESERVE_ID_RESPONSE_DICT,
    GET_COUNTRIES_RESPONSE_DICT,
    GET_OPERATORS_RESPONSE_DICT,
    GET_OPERATOR_PRODUCTS_RESPONSE_DICT,
)

fake_ping = MagicMock(return_value=PING_RESPONSE_DICT)
fake_msisdn_info = MagicMock(return_value=MSISDN_INFO_RESPONSE_DICT)
fake_reserve_id = MagicMock(return_value=RESERVE_ID_RESPONSE_DICT)
fake_get_countries = MagicMock(return_value=GET_COUNTRIES_RESPONSE_DICT)
fake_get_operators = MagicMock(return_value=GET_OPERATORS_RESPONSE_DICT)
fake_get_operator_airtime_products = MagicMock(
    return_value=GET_OPERATOR_PRODUCTS_RESPONSE_DICT
)


class TestTransferToViews(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )
        token = Token.objects.create(user=self.user)
        self.token = token.key
        self.api_client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

    @patch.object(TransferToClient, "ping", fake_ping)
    def test_ping_view(self):
        self.assertFalse(fake_ping.called)
        response = self.api_client.get(reverse("ping"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), PING_RESPONSE_DICT)
        self.assertTrue(fake_ping.called)

    @patch.object(TransferToClient, "get_misisdn_info", fake_msisdn_info)
    def test_msisdn_info_view(self):
        self.assertFalse(fake_ping.called)
        response = self.api_client.get(
            reverse("msisdn_info", kwargs={"msisdn": "+27820000001"})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), MSISDN_INFO_RESPONSE_DICT
        )
        self.assertTrue(fake_msisdn_info.called)

    @patch.object(TransferToClient, "reserve_id", fake_reserve_id)
    def test_reserve_id_view(self):
        self.assertFalse(fake_reserve_id.called)
        response = self.api_client.get(reverse("reserve_id"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), RESERVE_ID_RESPONSE_DICT)
        self.assertTrue(fake_reserve_id.called)

    @patch.object(TransferToClient, "get_countries", fake_get_countries)
    def test_get_countries_view(self):
        self.assertFalse(fake_get_countries.called)
        response = self.api_client.get(reverse("get_countries"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), GET_COUNTRIES_RESPONSE_DICT
        )
        self.assertTrue(fake_get_countries.called)

    @patch.object(TransferToClient, "get_operators", fake_get_operators)
    def test_get_operators_view(self):
        self.assertFalse(fake_get_operators.called)
        response = self.api_client.get(
            reverse("get_operators", kwargs={"country_id": 111})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), GET_OPERATORS_RESPONSE_DICT
        )
        self.assertTrue(fake_get_operators.called)

    @patch.object(
        TransferToClient,
        "get_operator_airtime_products",
        fake_get_operator_airtime_products,
    )
    def test_get_operator_products_view(self):
        self.assertFalse(fake_get_operator_airtime_products.called)
        response = self.api_client.get(
            reverse(
                "get_operator_airtime_products", kwargs={"operator_id": 222}
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), GET_OPERATOR_PRODUCTS_RESPONSE_DICT
        )
        self.assertTrue(fake_get_operator_airtime_products.called)
