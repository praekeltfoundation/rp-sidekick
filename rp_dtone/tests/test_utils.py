from unittest.mock import patch

from django.test import TestCase

from rp_dtone.dtone_client import DtoneClient
from rp_dtone.models import Transaction
from rp_dtone.utils import send_airtime
from sidekick.tests.utils import create_org


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


class TestSendAirtime(TestCase):
    def setUp(self):
        self.client = DtoneClient("fake_apikey", "fake_apisecret", False)
        self.org = create_org()

    @patch("rp_dtone.dtone_client.DtoneClient.get_operator_id")
    def test_send_airtime_operator_not_found(self, mock_get_operator_id):
        mock_get_operator_id.return_value = None

        success, transaction_uuid = send_airtime(
            self.org.id, self.client, "+27123", 1000
        )

        self.assertFalse(success)
        t = Transaction.objects.get(uuid=transaction_uuid)
        self.assertEqual(t.status, Transaction.Status.OPERATOR_NOT_FOUND)

        mock_get_operator_id.assert_called_with("+27123")

    @patch("rp_dtone.dtone_client.DtoneClient.get_operator_id")
    @patch("rp_dtone.dtone_client.DtoneClient.get_fixed_value_product")
    def test_send_airtime_fix_product_not_found(
        self, mock_get_fixed_value_product, mock_get_operator_id
    ):
        mock_get_operator_id.return_value = 1
        mock_get_fixed_value_product.return_value = None

        success, transaction_uuid = send_airtime(
            self.org.id, self.client, "+27123", 1000
        )

        self.assertFalse(success)
        t = Transaction.objects.get(uuid=transaction_uuid)
        self.assertEqual(t.status, Transaction.Status.PRODUCT_NOT_FOUND)

        mock_get_operator_id.assert_called_with("+27123")
        mock_get_fixed_value_product.assert_called_with(1, 1000)

    @patch("rp_dtone.dtone_client.DtoneClient.get_operator_id")
    @patch("rp_dtone.dtone_client.DtoneClient.get_fixed_value_product")
    @patch("rp_dtone.dtone_client.DtoneClient.submit_transaction")
    def test_send_airtime_error(
        self,
        mock_submit_transaction,
        mock_get_fixed_value_product,
        mock_get_operator_id,
    ):
        mock_get_operator_id.return_value = 1
        mock_get_fixed_value_product.return_value = 2
        mock_submit_transaction.return_value = MockResponse({"test": "Error"}, 400)

        success, transaction_uuid = send_airtime(
            self.org.id, self.client, "+27123", 1000
        )

        self.assertFalse(success)
        t = Transaction.objects.get(uuid=transaction_uuid)
        self.assertEqual(t.status, Transaction.Status.ERROR)
        self.assertEqual(t.response, {"test": "Error"})

        mock_get_operator_id.assert_called_with("+27123")
        mock_get_fixed_value_product.assert_called_with(1, 1000)
        mock_submit_transaction.assert_called_with("+27123", 2)

    @patch("rp_dtone.dtone_client.DtoneClient.get_operator_id")
    @patch("rp_dtone.dtone_client.DtoneClient.get_fixed_value_product")
    @patch("rp_dtone.dtone_client.DtoneClient.submit_transaction")
    def test_send_airtime_success(
        self,
        mock_submit_transaction,
        mock_get_fixed_value_product,
        mock_get_operator_id,
    ):
        mock_get_operator_id.return_value = 1
        mock_get_fixed_value_product.return_value = 2
        mock_submit_transaction.return_value = MockResponse({}, 201)

        success, transaction_uuid = send_airtime(
            self.org.id, self.client, "+27123", 1000
        )

        self.assertTrue(success)
        t = Transaction.objects.get(uuid=transaction_uuid)
        self.assertEqual(t.status, Transaction.Status.SUCCESS)
        self.assertIsNone(t.response)

        mock_get_operator_id.assert_called_with("+27123")
        mock_get_fixed_value_product.assert_called_with(1, 1000)
        mock_submit_transaction.assert_called_with("+27123", 2)
