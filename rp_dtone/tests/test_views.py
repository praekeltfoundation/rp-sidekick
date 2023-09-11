import json
from unittest.mock import ANY, patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from sidekick.tests.utils import create_org

from .utils import create_dtone_account


class TestDtoneViews(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )
        token = Token.objects.get(user=self.user)
        self.token = token.key

        self.api_client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

        self.org = create_org()
        self.org.users.add(self.user)

        self.dtone_account = create_dtone_account(org=self.org)

    @patch("rp_dtone.views.send_airtime")
    def test_send_fixed_amount_airtime(self, mock_send_airtime):
        msisdn = "+27820006000"
        airtime_amount = 444

        mock_send_airtime.return_value = True, "transaction-uuid"

        response = self.api_client.get(
            reverse(
                "send_fixed_amount_airtime",
                kwargs={
                    "org_id": self.org.id,
                    "msisdn": msisdn,
                    "airtime_value": airtime_amount,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content), {"uuid": "transaction-uuid"})
        mock_send_airtime.assert_called_with(self.org.id, ANY, msisdn, 444)

    @patch("rp_dtone.views.send_airtime")
    def test_send_fixed_amount_airtime_error(self, mock_send_airtime):
        msisdn = "+27820006000"
        airtime_amount = 444

        mock_send_airtime.return_value = False, "transaction-uuid"

        response = self.api_client.get(
            reverse(
                "send_fixed_amount_airtime",
                kwargs={
                    "org_id": self.org.id,
                    "msisdn": msisdn,
                    "airtime_value": airtime_amount,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content), {"uuid": "transaction-uuid"})
        mock_send_airtime.assert_called_with(self.org.id, ANY, msisdn, 444)

    @patch("rp_dtone.views.send_airtime")
    def test_send_fixed_amount_airtime_org_not_found(self, mock_send_airtime):
        msisdn = "+27820006000"
        airtime_amount = 444

        response = self.api_client.get(
            reverse(
                "send_fixed_amount_airtime",
                kwargs={
                    "org_id": 999,
                    "msisdn": msisdn,
                    "airtime_value": airtime_amount,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            json.loads(response.content), {"error": "organisation not found"}
        )
        mock_send_airtime.assert_not_called()

    @patch("rp_dtone.views.send_airtime")
    def test_send_fixed_amount_airtime_user_not_in_org(self, mock_send_airtime):
        msisdn = "+27820006000"
        airtime_amount = 444

        new_org = create_org()

        response = self.api_client.get(
            reverse(
                "send_fixed_amount_airtime",
                kwargs={
                    "org_id": new_org.id,
                    "msisdn": msisdn,
                    "airtime_value": airtime_amount,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(json.loads(response.content), {"error": "user not in org"})
        mock_send_airtime.assert_not_called()

    @patch("rp_dtone.views.send_airtime")
    def test_send_fixed_amount_airtime_no_dtone_account(self, mock_send_airtime):
        msisdn = "+27820006000"
        airtime_amount = 444

        new_org = create_org()
        new_org.users.add(self.user)

        response = self.api_client.get(
            reverse(
                "send_fixed_amount_airtime",
                kwargs={
                    "org_id": new_org.id,
                    "msisdn": msisdn,
                    "airtime_value": airtime_amount,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            json.loads(response.content), {"error": "no dtone account configured"}
        )
        mock_send_airtime.assert_not_called()
