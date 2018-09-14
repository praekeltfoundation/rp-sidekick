import time
import hashlib
import hmac
import base64
import json
import responses
from mock import patch
from freezegun import freeze_time
from pytest import raises
from unittest import TestCase

from rp_transferto.utils import TransferToClient, TransferToClient2


class TestTransferToClient(TestCase):
    def setUp(self):
        self.client = TransferToClient("fake_login", "fake_token")

    def test_convert_response_body(self):
        """
        Returns a dict of the airtime API body response
        """
        test_input = b"authentication_key=1111111111111111\r\nerror_code=919\r\nerror_txt=All needed argument not received\r\n"
        expected_output = {
            "authentication_key": "1111111111111111",
            "error_code": "919",
            "error_txt": "All needed argument not received",
        }
        output = self.client._convert_response_body(test_input)
        self.assertDictEqual(output, expected_output)

    @responses.activate
    def test_make_transferto_request(self):
        responses.add(
            responses.POST,
            self.client.url,
            body=b"info_txt=pong\r\nauthentication_key=1111111111111111\r\nerror_code=0\r\nerror_txt=Transaction successful\r\n",
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
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.ping()

        mock.assert_called_once_with(action="ping")

    def test_get_misisdn_info(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.get_misisdn_info("+27820000001")

        mock.assert_called_once_with(
            action="msisdn_info", destination_msisdn="+27820000001"
        )

    def test_reserve_id(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.reserve_id()

        mock.assert_called_once_with(action="reserve_id")

    def test_get_countries(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.get_countries()

        mock.assert_called_once_with(action="pricelist", info_type="countries")

    def test_get_operators(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.get_operators(111)

        mock.assert_called_once_with(
            action="pricelist", info_type="country", content=111
        )

    def test_get_operator_airtime_products(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.get_operator_airtime_products(111)

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

    def test_make_topup_throws_exception_source_variables(self):
        with raises(Exception) as exception_info:
            self.client.make_topup("fake_msisdn", 10)
        self.assertEqual(
            exception_info.value.__str__(),
            "source_msisdn and source_name cannot both be None",
        )

    def test_make_topup_throws_exception_product_must_be_int(self):
        with raises(TypeError) as exception_info:
            self.client.make_topup("fake_msisdn", "10", source_name="test_name")
        self.assertEqual(
            exception_info.value.__str__(), "product arg must be an int"
        )

    def test_make_topup_1(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.make_topup("+27820000001", 10, source_msisdn="+27820000002")

        mock.assert_called_once_with(
            action="topup",
            destination_msisdn="+27820000001",
            product=10,
            msisdn="+27820000002",
        )

    def test_make_topup_2(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.make_topup("+27820000001", 10, source_name="john")

        mock.assert_called_once_with(
            action="topup",
            destination_msisdn="+27820000001",
            product=10,
            msisdn="john",
        )

    def test_make_topup_3(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.make_topup(
                "+27820000001",
                10,
                source_msisdn="+27820000002",
                reserve_id=1234,
            )

        mock.assert_called_once_with(
            action="topup",
            destination_msisdn="+27820000001",
            product=10,
            msisdn="+27820000002",
            reserve_id=1234,
        )


class TestTransferToClient2(TestCase):
    def setUp(self):
        self.client = TransferToClient2("fake_apikey", "fake_apisecret")

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
                    bytes("fake_apisecret".encode("utf-8")),
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
            "https://api.transferto.com/v1.1/operators/{}/products".format(
                fake_country_id
            ),
            json={"fake": "payload"},
            status=200,
        )

        output = self.client._make_transferto_api_request(
            url="https://api.transferto.com/v1.1/operators/{}/products".format(
                fake_country_id
            )
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
        client = TransferToClient2("fake_apikey", "fake_apisecret")
        with patch.object(client, "_make_transferto_api_request") as mock:
            client.get_operator_products(fake_operator_id)

        mock.assert_called_once_with(
            "https://api.transferto.com/v1.1/operators/{}/products".format(
                fake_operator_id
            )
        )

    def test_get_country_services(self):
        fake_country_id = 99
        client = TransferToClient2("fake_apikey", "fake_apisecret")
        with patch.object(client, "_make_transferto_api_request") as mock:
            client.get_country_services(fake_country_id)

        mock.assert_called_once_with(
            "https://api.transferto.com/v1.1/countries/{}/services".format(
                fake_country_id
            )
        )

    @freeze_time("2000-01-01")
    def test_topup_data(self):
        test_msisdn = "+27820000000"
        formatted_test_msisdn = "27820000000"
        test_product_id = "123456"
        external_id_frozen_time = "946684800000000"

        client = TransferToClient2("fake_apikey", "fake_apisecret")
        with patch.object(client, "_make_transferto_api_request") as mock:
            client.topup_data(test_msisdn, test_product_id)

        mock.assert_called_once_with(
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

        client = TransferToClient2("fake_apikey", "fake_apisecret")
        with patch.object(client, "_make_transferto_api_request") as mock:
            client.topup_data(test_msisdn, test_product_id, simulate=True)

        mock.assert_called_once_with(
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
