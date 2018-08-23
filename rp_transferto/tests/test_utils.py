import responses
from mock import patch
from pytest import raises
from unittest import TestCase

from rp_transferto.utils import TransferToClient


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

        mock.assert_called_once_with("ping")

    def test_reserve_id(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.reserve_id()

        mock.assert_called_once_with("reserve_id")

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

    def test_get_operator_products(self):
        client = TransferToClient("fake_login", "fake_token")
        with patch.object(client, "_make_transferto_request") as mock:
            client.get_operator_products(111)

        mock.assert_called_once_with(
            action="pricelist", info_type="operator", content=111
        )

    def test_get_operators_throws_exception(self):
        with raises(TypeError) as exception_info:
            self.client.get_operators("not an int")
        self.assertEqual(exception_info.value.__str__(), "arg must be an int")

    def test_get_operator_products_throws_exception(self):
        with raises(TypeError) as exception_info:
            self.client.get_operator_products("not an int")
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
