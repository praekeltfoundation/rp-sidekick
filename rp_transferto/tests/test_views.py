import json

from mock import patch
from unittest.mock import MagicMock

from pytest import raises

from django.urls import reverse
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.test import TestCase

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient

from sidekick.utils import clean_msisdn

from rp_transferto.views import process_status_code
from rp_transferto.models import MsisdnInformation
from rp_transferto.tasks import topup_data
from rp_transferto.utils import TransferToClient
from .constants import (
    PING_RESPONSE_DICT,
    MSISDN_INFO_RESPONSE_DICT,
    RESERVE_ID_RESPONSE_DICT,
    GET_COUNTRIES_RESPONSE_DICT,
    GET_OPERATORS_RESPONSE_DICT,
    GET_OPERATOR_AIRTIME_PRODUCTS_RESPONSE_DICT,
    GET_PRODUCTS_RESPONSE_DICT,
    GET_COUNTRY_SERVICES_RESPONSE_DICT,
)

fake_ping = MagicMock(return_value=PING_RESPONSE_DICT)
fake_msisdn_info = MagicMock(return_value=MSISDN_INFO_RESPONSE_DICT)
fake_reserve_id = MagicMock(return_value=RESERVE_ID_RESPONSE_DICT)
fake_get_countries = MagicMock(return_value=GET_COUNTRIES_RESPONSE_DICT)
fake_get_operators = MagicMock(return_value=GET_OPERATORS_RESPONSE_DICT)
fake_get_operator_airtime_products = MagicMock(
    return_value=GET_OPERATOR_AIRTIME_PRODUCTS_RESPONSE_DICT
)
fake_get_operator_products = MagicMock(return_value=GET_PRODUCTS_RESPONSE_DICT)
fake_get_country_services = MagicMock(
    return_value=GET_COUNTRY_SERVICES_RESPONSE_DICT
)
fake_delay = MagicMock({"info_txt": "top_up_data"})


class TestTransferToFunctions(TestCase):
    def test_process_status_code_400(self):
        result = process_status_code({"error_code": 101})
        self.assertEqual(type(result), JsonResponse)
        self.assertEqual(result.status_code, 400)

    def test_process_status_code_200(self):
        result = process_status_code({"error_code": 0})
        self.assertEqual(type(result), JsonResponse)
        self.assertEqual(result.status_code, 200)

    def test_process_status_code_exception(self):
        with raises(KeyError) as exception_info:
            process_status_code({"errorCode": 0})
        self.assertEqual(exception_info.value.__str__(), "'error_code'")


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

    @patch("rp_transferto.utils.TransferToClient.get_misisdn_info")
    def test_msisdn_info_view_object_does_not_exist(
        self, fake_get_misisdn_info
    ):
        fake_get_misisdn_info.return_value = MSISDN_INFO_RESPONSE_DICT
        self.assertEqual(MsisdnInformation.objects.count(), 0)
        self.assertFalse(fake_get_misisdn_info.called)
        response = self.api_client.get(
            reverse("msisdn_info", kwargs={"msisdn": "+27820000001"})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), MSISDN_INFO_RESPONSE_DICT
        )
        self.assertTrue(fake_get_misisdn_info.called)
        self.assertEqual(MsisdnInformation.objects.count(), 1)

    @patch("rp_transferto.utils.TransferToClient.get_misisdn_info")
    def test_msisdn_info_view_cached_object(self, fake_get_misisdn_info):
        fake_get_misisdn_info.return_value = MSISDN_INFO_RESPONSE_DICT
        msisdn = "+27820000000"
        MsisdnInformation.objects.create(
            msisdn=msisdn, data=MSISDN_INFO_RESPONSE_DICT
        )
        self.assertEqual(MsisdnInformation.objects.count(), 1)
        self.assertFalse(fake_get_misisdn_info.called)
        response = self.api_client.get(
            reverse("msisdn_info", kwargs={"msisdn": msisdn})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), MSISDN_INFO_RESPONSE_DICT
        )
        self.assertFalse(fake_get_misisdn_info.called)
        self.assertEqual(MsisdnInformation.objects.count(), 1)

    @patch("rp_transferto.utils.TransferToClient.get_misisdn_info")
    def test_msisdn_info_no_cache(self, fake_get_misisdn_info):
        fake_get_misisdn_info.return_value = MSISDN_INFO_RESPONSE_DICT
        msisdn = "+27820000000"
        MsisdnInformation.objects.create(
            msisdn=msisdn, data=MSISDN_INFO_RESPONSE_DICT
        )
        self.assertEqual(MsisdnInformation.objects.count(), 1)
        self.assertFalse(fake_get_misisdn_info.called)
        response = self.api_client.get(
            "{}?no_cache=True".format(
                reverse("msisdn_info", kwargs={"msisdn": msisdn})
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), MSISDN_INFO_RESPONSE_DICT
        )
        self.assertTrue(fake_get_misisdn_info.called)
        self.assertEqual(MsisdnInformation.objects.count(), 2)

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
    def test_get_operator_airtime_products_view(self):
        self.assertFalse(fake_get_operator_airtime_products.called)
        response = self.api_client.get(
            reverse(
                "get_operator_airtime_products", kwargs={"operator_id": 222}
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content),
            GET_OPERATOR_AIRTIME_PRODUCTS_RESPONSE_DICT,
        )
        self.assertTrue(fake_get_operator_airtime_products.called)

    @patch.object(
        TransferToClient, "get_operator_products", fake_get_operator_products
    )
    def test_get_operator_products_view(self):
        self.assertFalse(fake_get_operator_products.called)
        response = self.api_client.get(
            reverse("get_operator_products", kwargs={"operator_id": 222})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), GET_PRODUCTS_RESPONSE_DICT
        )
        self.assertTrue(fake_get_operator_products.called)

    @patch.object(
        TransferToClient, "get_country_services", fake_get_country_services
    )
    def test_get_country_services_view(self):
        self.assertFalse(fake_get_country_services.called)
        response = self.api_client.get(
            reverse("get_country_services", kwargs={"country_id": 222})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), GET_COUNTRY_SERVICES_RESPONSE_DICT
        )
        self.assertTrue(fake_get_country_services.called)

    @patch.object(topup_data, "delay", fake_delay)
    def test_top_up_data_view(self):
        self.assertFalse(fake_delay.called)
        response = self.api_client.get(
            "{base_url}?msisdn={msisdn}&user_uuid={user_uuid}&data_amount={data_amount}".format(
                base_url=reverse("top_up_data"),
                msisdn="+27820000000",
                user_uuid="abc-1234",
                data_amount="100MB",
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content), {"info_txt": "top_up_data"}
        )
        self.assertTrue(fake_delay.called)

    @patch("rp_transferto.tasks.BuyProductTakeAction.delay")
    def test_buy_product_take_action_view_simple(
        self, fake_buy_product_take_action
    ):
        msisdn = "+27820006000"
        product_id = 444
        self.assertFalse(fake_buy_product_take_action.called)

        response = self.api_client.get(
            reverse(
                "buy_product_take_action",
                kwargs={"msisdn": msisdn, "product_id": product_id},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content),
            {"info_txt": "buy_product_take_action"},
        )
        fake_buy_product_take_action.assert_called_with(
            clean_msisdn(msisdn),
            product_id,
            flow_start=False,
            user_uuid=False,
            values_to_update={},
        )

    @patch("rp_transferto.tasks.BuyProductTakeAction.delay")
    def test_buy_product_take_action_view_update_fields(
        self, fake_buy_product_take_action
    ):
        msisdn = "+27820006000"
        product_id = 444
        user_uuid = "3333-abc"
        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }
        self.assertFalse(fake_buy_product_take_action.called)

        url = (
            "{base_url}?rp_0001_01_transferto_status=status"
            "&rp_0001_01_transferto_status_message=status_message"
            "&rp_0001_01_transferto_product_desc=product_desc"
            "&user_uuid={user_uuid}"
        ).format(
            base_url=reverse(
                "buy_product_take_action",
                kwargs={"msisdn": msisdn, "product_id": product_id},
            ),
            user_uuid=user_uuid,
        )

        response = self.api_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content),
            {"info_txt": "buy_product_take_action"},
        )
        fake_buy_product_take_action.assert_called_with(
            clean_msisdn(msisdn),
            product_id,
            flow_start=False,
            user_uuid=user_uuid,
            values_to_update=values_to_update,
        )

    @patch("rp_transferto.tasks.BuyProductTakeAction.delay")
    def test_buy_product_take_action_view_start_flow(
        self, fake_buy_product_take_action
    ):
        msisdn = "+27820006000"
        product_id = 444
        user_uuid = "3333-abc"
        flow_uuid = "123412341234"

        url = (
            "{base_url}?user_uuid={user_uuid}&flow_uuid={flow_uuid}" ""
        ).format(
            base_url=reverse(
                "buy_product_take_action",
                kwargs={"msisdn": msisdn, "product_id": product_id},
            ),
            user_uuid=user_uuid,
            flow_uuid=flow_uuid,
        )

        response = self.api_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content),
            {"info_txt": "buy_product_take_action"},
        )
        fake_buy_product_take_action.assert_called_with(
            clean_msisdn(msisdn),
            product_id,
            flow_start=flow_uuid,
            user_uuid=user_uuid,
            values_to_update={},
        )

    @patch("rp_transferto.tasks.BuyAirtimeTakeAction.delay")
    def test_buy_airtime_take_action_view_simple(
        self, fake_buy_airtime_take_action
    ):
        msisdn = "+27820006000"
        airtime_amount = 444
        from_string = "bob"
        self.assertFalse(fake_buy_airtime_take_action.called)

        response = self.api_client.get(
            reverse(
                "buy_airtime_take_action",
                kwargs={
                    "msisdn": msisdn,
                    "airtime_amount": airtime_amount,
                    "from_string": from_string,
                },
            )
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content),
            {"info_txt": "buy_airtime_take_action"},
        )
        fake_buy_airtime_take_action.assert_called_with(
            clean_msisdn(msisdn),
            airtime_amount,
            from_string,
            flow_start=False,
            user_uuid=False,
            values_to_update={},
        )

    @patch("rp_transferto.tasks.BuyAirtimeTakeAction.delay")
    def test_buy_airtime_take_action_view_update_fields(
        self, fake_buy_airtime_take_action
    ):
        msisdn = "+27820006000"
        airtime_amount = 444
        from_string = "bob"
        user_uuid = "3333-abc"
        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }
        self.assertFalse(fake_buy_airtime_take_action.called)

        url = (
            "{base_url}?rp_0001_01_transferto_status=status"
            "&rp_0001_01_transferto_status_message=status_message"
            "&rp_0001_01_transferto_product_desc=product_desc"
            "&user_uuid={user_uuid}"
        ).format(
            base_url=reverse(
                "buy_airtime_take_action",
                kwargs={
                    "msisdn": msisdn,
                    "airtime_amount": airtime_amount,
                    "from_string": from_string,
                },
            ),
            user_uuid=user_uuid,
        )

        response = self.api_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content),
            {"info_txt": "buy_airtime_take_action"},
        )
        fake_buy_airtime_take_action.assert_called_with(
            clean_msisdn(msisdn),
            airtime_amount,
            from_string,
            flow_start=False,
            user_uuid=user_uuid,
            values_to_update=values_to_update,
        )

    @patch("rp_transferto.tasks.BuyAirtimeTakeAction.delay")
    def test_buy_airtime_take_action_view_start_flow(
        self, fake_buy_airtime_take_action
    ):
        msisdn = "+27820006000"
        airtime_amount = 444
        from_string = "bob"
        user_uuid = "3333-abc"
        flow_uuid = "123412341234"

        url = (
            "{base_url}?user_uuid={user_uuid}&flow_uuid={flow_uuid}" ""
        ).format(
            base_url=reverse(
                "buy_airtime_take_action",
                kwargs={
                    "msisdn": msisdn,
                    "airtime_amount": airtime_amount,
                    "from_string": from_string,
                },
            ),
            user_uuid=user_uuid,
            flow_uuid=flow_uuid,
        )

        response = self.api_client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            json.loads(response.content),
            {"info_txt": "buy_airtime_take_action"},
        )
        fake_buy_airtime_take_action.assert_called_with(
            clean_msisdn(msisdn),
            airtime_amount,
            from_string,
            flow_start=flow_uuid,
            user_uuid=user_uuid,
            values_to_update={},
        )
