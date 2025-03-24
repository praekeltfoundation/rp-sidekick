import base64
import hashlib
import hmac
import json
import time
from unittest import TestCase
from unittest.mock import patch

import responses
from freezegun import freeze_time
from pytest import raises

from rp_transferto.utils import TransferToClient


class TestTransferToClient(TestCase):
    def setUp(self):
        self.client = TransferToClient(
            "fake_login", "fake_token", "fake_apikey", "fake_apisecret"
        )

    def test_convert_response_body(self):
        """
        Returns a dict of the airtime API body response
        """
        test_input = b"\r\n".join(
            [
                b"authentication_key=1111111111111111",
                b"error_code=919",
                b"error_txt=All needed argument not received",
            ]
        )
        expected_output = {
            "authentication_key": "1111111111111111",
            "error_code": "919",
            "error_txt": "All needed argument not received",
        }
        output = self.client._convert_response_body(test_input)
        self.assertDictEqual(output, expected_output)

    @responses.activate
    def test_make_transferto_request(self):
        test_input = b"\r\n".join(
            [
                b"info_txt=pong",
                b"authentication_key=1111111111111111",
                b"error_code=0",
                b"error_txt=Transaction successful",
            ]
        )
        responses.add(
            responses.POST,
            self.client.url,
            body=test_input,
            status=200,
        )
        output = self.client._make_transferto_request(action="ping")
        expected_output = {
            "info_txt": "pong",
            "authentication_key": "1111111111111111",
            "error_code": "0",
            "error_txt": "Transaction successful",
        }
        self.assertDictEqual(output, expected_output)

    def test_ping(self):
        with patch.object(self.client, "_make_transferto_request") as mock:
            self.client.ping()

        mock.assert_called_once_with(action="ping")

    def test_get_misisdn_info(self):
        with patch.object(self.client, "_make_transferto_request") as mock:
            self.client.get_misisdn_info("+27820000001")

        mock.assert_called_once_with(
            action="msisdn_info", destination_msisdn="+27820000001"
        )

    def test_reserve_id(self):
        with patch.object(self.client, "_make_transferto_request") as mock:
            self.client.reserve_id()

        mock.assert_called_once_with(action="reserve_id")

    def test_get_countries(self):
        with patch.object(self.client, "_make_transferto_request") as mock:
            self.client.get_countries()

        mock.assert_called_once_with(action="pricelist", info_type="countries")

    def test_get_operators(self):
        with patch.object(self.client, "_make_transferto_request") as mock:
            self.client.get_operators(111)

        mock.assert_called_once_with(
            action="pricelist", info_type="country", content=111
        )

    def test_get_operator_airtime_products(self):
        with patch.object(self.client, "_make_transferto_request") as mock:
            self.client.get_operator_airtime_products(111)

        mock.assert_called_once_with(
            action="pricelist", info_type="operator", content=111
        )

    def test_get_operators_throws_exception(self):
        with raises(TypeError) as exception_info:
            self.client.get_operators("not an int")
        self.assertEqual(exception_info.value.__str__(), "arg must be an int")

    def test_get_operator_airtime_products_throws_exception(self):
        with raises(TypeError) as exception_info:
            self.client.get_operator_airtime_products("not an int")
        self.assertEqual(exception_info.value.__str__(), "arg must be an int")

    def test_make_topup_throws_exception_product_must_be_int(self):
        with raises(TypeError) as exception_info:
            self.client.make_topup("fake_msisdn", "10", from_string="test_name")
        self.assertEqual(exception_info.value.__str__(), "product arg must be an int")

    def test_make_topup_1(self):
        with patch.object(self.client, "_make_transferto_request") as mock:
            self.client.make_topup("+27820000001", 10, from_string="+27820000002")

        mock.assert_called_once_with(
            action="topup",
            destination_msisdn="+27820000001",
            product=10,
            msisdn="+27820000002",
        )

    def test_make_topup_2(self):
        with patch.object(self.client, "_make_transferto_request") as mock:
            self.client.make_topup("+27820000001", 10, from_string="john")

        mock.assert_called_once_with(
            action="topup", destination_msisdn="+27820000001", product=10, msisdn="john"
        )

    def test_make_topup_3(self):
        with patch.object(self.client, "_make_transferto_request") as mock:
            self.client.make_topup(
                "+27820000001", 10, from_string="+27820000002", reserve_id=1234
            )

        mock.assert_called_once_with(
            action="topup",
            destination_msisdn="+27820000001",
            product=10,
            msisdn="+27820000002",
            reserve_id=1234,
        )

    def _check_headers(self, headers, time):
        """
        headers is a dict
        time is unix timestamp expected when the function was called
        """
        expected_nonce = str(int(time * 1000000))
        self.assertEqual(headers["X-TransferTo-apikey"], "fake_apikey")
        self.assertEqual(headers["X-TransferTo-nonce"], expected_nonce)
        self.assertEqual(
            headers["x-transferto-hmac"],
            base64.b64encode(
                hmac.new(
                    b"fake_apisecret",
                    bytes(("fake_apikey" + expected_nonce).encode("utf-8")),
                    digestmod=hashlib.sha256,
                ).digest()
            ),
        )

    @freeze_time("2000-01-01")  # set time to 946684800000000
    @responses.activate
    def test_make_transferto_request_get(self):
        fake_country_id = 99
        responses.add(
            responses.GET,
            f"https://api.transferto.com/v1.1/operators/{fake_country_id}/products",
            json={"fake": "payload"},
            status=200,
        )

        output = self.client._make_transferto_api_request(
            "some_action",
            url=f"https://api.transferto.com/v1.1/operators/{fake_country_id}/products",
        )
        expected_output = {"fake": "payload"}
        self.assertDictEqual(output, expected_output)
        test_request_headers = responses.calls[0].request.headers
        self._check_headers(test_request_headers, time.time())

    @freeze_time("2000-01-01")
    @responses.activate
    def test_make_transferto_request_post(self):
        FAKE_REQUEST_BODY = {"fake": "request body"}
        responses.add(
            responses.POST,
            "https://api.transferto.com/v1.1/transactions/fixed_value_recharges",
            json={"fake": "payload"},
            status=200,
        )
        self.client._make_transferto_api_request(
            "some_action",
            url="https://api.transferto.com/v1.1/transactions/fixed_value_recharges",
            body=FAKE_REQUEST_BODY,
        )

        self.assertDictEqual(
            json.loads(responses.calls[0].request.body), FAKE_REQUEST_BODY
        )
        test_request_headers = responses.calls[0].request.headers
        self._check_headers(test_request_headers, time.time())

    def test_get_operator_products(self):
        fake_operator_id = 99
        with patch.object(self.client, "_make_transferto_api_request") as mock:
            self.client.get_operator_products(fake_operator_id)

        mock.assert_called_once_with(
            "get_operator_products",
            f"https://api.transferto.com/v1.1/operators/{fake_operator_id}/products",
        )

    def test_get_country_services(self):
        fake_country_id = 99
        with patch.object(self.client, "_make_transferto_api_request") as mock:
            self.client.get_country_services(fake_country_id)

        mock.assert_called_once_with(
            "get_country_services",
            f"https://api.transferto.com/v1.1/countries/{fake_country_id}/services",
        )

    @freeze_time("2000-01-01")
    def test_topup_data(self):
        test_msisdn = "+27820000000"
        formatted_test_msisdn = "27820000000"
        test_product_id = "123456"
        external_id_frozen_time = "946684800000000"

        with patch.object(self.client, "_make_transferto_api_request") as mock:
            self.client.topup_data(test_msisdn, test_product_id)

        mock.assert_called_once_with(
            "topup_data",
            "https://api.transferto.com/v1.1/transactions/fixed_value_recharges",
            body={
                "account_number": formatted_test_msisdn,
                "product_id": test_product_id,
                "external_id": external_id_frozen_time,
                "simulation": "0",
                "sender_sms_notification": "1",
                "sender_sms_text": "Sender message",
                "recipient_sms_notification": "1",
                "recipient_sms_text": "MomConnect",
                "sender": {
                    "last_name": "",
                    "middle_name": " ",
                    "first_name": "",
                    "email": "",
                    "mobile": "08443011",
                },
                "recipient": {
                    "last_name": "",
                    "middle_name": "",
                    "first_name": "",
                    "email": "",
                    "mobile": formatted_test_msisdn,
                },
            },
        )

    @freeze_time("2000-01-01")
    def test_topup_data_simulate_true(self):
        test_msisdn = "+27820000000"
        formatted_test_msisdn = "27820000000"
        test_product_id = "123456"
        external_id_frozen_time = "946684800000000"

        with patch.object(self.client, "_make_transferto_api_request") as mock:
            self.client.topup_data(test_msisdn, test_product_id, simulate=True)

        mock.assert_called_once_with(
            "topup_data",
            "https://api.transferto.com/v1.1/transactions/fixed_value_recharges",
            body={
                "account_number": formatted_test_msisdn,
                "product_id": test_product_id,
                "external_id": external_id_frozen_time,
                "simulation": "1",
                "sender_sms_notification": "1",
                "sender_sms_text": "Sender message",
                "recipient_sms_notification": "1",
                "recipient_sms_text": "MomConnect",
                "sender": {
                    "last_name": "",
                    "middle_name": " ",
                    "first_name": "",
                    "email": "",
                    "mobile": "08443011",
                },
                "recipient": {
                    "last_name": "",
                    "middle_name": "",
                    "first_name": "",
                    "email": "",
                    "mobile": formatted_test_msisdn,
                },
            },
        )
