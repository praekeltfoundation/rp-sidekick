import json

from django.test import TestCase
from freezegun import freeze_time

from sidekick.tests.utils import create_org

from ..models import Transaction


class TestTransaction(TestCase):
    def setUp(self):
        self.org = create_org()

    @freeze_time("2019-03-14 01:30:00")
    def test_string(self):
        msisdn = "+27820000001"
        airtime_value = 333
        transaction = Transaction.objects.create(
            msisdn=msisdn,
            value=airtime_value,
            org=self.org,
            operator_id=1,
            product_id=2,
            response={"test": "response"},
        )
        self.assertEqual(
            json.loads(transaction.__str__()),
            {
                "id": transaction.id,
                "uuid": str(transaction.uuid),
                "msisdn": msisdn,
                "value": airtime_value,
                "operator_id": 1,
                "product_id": 2,
                "status": str(Transaction.Status.CREATED),
                "response": {"test": "response"},
                "org": self.org.name,
                "timestamp": "2019-03-14 01:30:00",
            },
        )
