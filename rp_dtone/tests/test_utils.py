import json
from unittest import TestCase

import responses

from rp_dtone.utils import DtoneClient


class TestDtoneClient(TestCase):
    def setUp(self):
        self.client = DtoneClient("fake_apikey", "fake_apisecret", False)

    @responses.activate
    def test_get_operator_id(self):
        responses.add(
            method=responses.GET,
            url="https://preprod-dvs-api.dtone.com/v1/lookup/mobile-number/+27123",
            json=[{"id": 123}],
            status=200,
        )

        operator_id = self.client._get_operator_id("+27123")

        self.assertEqual(operator_id, 123)

        request = responses.calls[0].request
        self.assertEqual(
            request.headers["Authorization"],
            "Basic ZmFrZV9hcGlrZXk6ZmFrZV9hcGlzZWNyZXQ=",
        )

    @responses.activate
    def test_get_fixed_value_product(self):
        responses.add(
            method=responses.GET,
            url="https://preprod-dvs-api.dtone.com/v1/products?type=FIXED_VALUE_RECHARGE&operator_id=123&per_page=100",
            json=[
                {"id": 111, "destination": {"amount": 10}},
                {"id": 222, "destination": {"amount": 5}},
            ],
            status=200,
        )

        product_id = self.client._get_fixed_value_product(123, 5)

        self.assertEqual(product_id, 222)

        request = responses.calls[0].request
        self.assertEqual(
            request.headers["Authorization"],
            "Basic ZmFrZV9hcGlrZXk6ZmFrZV9hcGlzZWNyZXQ=",
        )

    @responses.activate
    def test_submit_transaction(self):
        responses.add(
            method=responses.POST,
            url="https://preprod-dvs-api.dtone.com/v1/async/transactions",
            json={"test": "response"},
            status=200,
        )

        self.client._submit_transaction("+27123", 123)

        request = responses.calls[0].request
        self.assertEqual(
            request.headers["Authorization"],
            "Basic ZmFrZV9hcGlrZXk6ZmFrZV9hcGlzZWNyZXQ=",
        )

        self.assertEqual(
            json.loads(request.body),
            {
                "external_id": "fe755a2f-d305-4232-a920-796b4140b329",
                "product_id": 123,
                "auto_confirm": True,
                "credit_party_identifier": {"mobile_number": "+27123"},
            },
        )
