import json
import uuid

import responses
from django.test import TestCase

from rp_dtone.dtone_client import DtoneClient


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

        operator_id = self.client.get_operator_id("+27123")

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
                {
                    "id": 111,
                    "destination": {"amount": 10},
                    "service": {
                        "id": 1,
                        "name": "Mobile",
                        "subservice": {"id": 11, "name": "Data"},
                    },
                },
                {
                    "id": 222,
                    "destination": {"amount": 5},
                    "service": {
                        "id": 1,
                        "name": "Mobile",
                        "subservice": {"id": 11, "name": "Data"},
                    },
                },
                {
                    "id": 333,
                    "destination": {"amount": 10},
                    "service": {
                        "id": 1,
                        "name": "Mobile",
                        "subservice": {"id": 11, "name": "Airtime"},
                    },
                },
                {
                    "id": 444,
                    "destination": {"amount": 5},
                    "service": {
                        "id": 1,
                        "name": "Mobile",
                        "subservice": {"id": 11, "name": "Airtime"},
                    },
                },
            ],
            status=200,
        )

        product_id = self.client.get_fixed_value_product(123, 5)

        self.assertEqual(product_id, 444)

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

        transaction_uuid = uuid.uuid4()
        self.client.submit_transaction(transaction_uuid, "+27123", 123)

        request = responses.calls[0].request
        self.assertEqual(
            request.headers["Authorization"],
            "Basic ZmFrZV9hcGlrZXk6ZmFrZV9hcGlzZWNyZXQ=",
        )

        self.assertEqual(
            json.loads(request.body),
            {
                "external_id": str(transaction_uuid),
                "product_id": 123,
                "auto_confirm": True,
                "credit_party_identifier": {"mobile_number": "+27123"},
            },
        )
