import json
import pkg_resources

from mock import patch
from freezegun import freeze_time

from django.test import TestCase

from sidekick.utils import clean_msisdn
from sidekick.tests.utils import create_org

from ..models import TopupAttempt

from .utils import create_transferto_account
from .constants import TOPUP_RESPONSE_DICT, TOPUP_ERROR_RESPONSE_DICT


class TestTopupAttempt(TestCase):
    def setUp(self):
        self.org = create_org()
        self.transferto_account = create_transferto_account(org=self.org)

    @freeze_time("2019-03-14 01:30:00")
    def test_string_1(self):
        msisdn = "+27820000001"
        airtime_amount = 333
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn, amount=airtime_amount, org=self.org
        )
        self.assertEqual(
            json.loads(topup_attempt.__str__()),
            {
                "id": topup_attempt.id,
                "sidekick_version": pkg_resources.get_distribution(
                    "rp-sidekick"
                ).version,
                "msisdn": clean_msisdn(msisdn),
                "from_string": "",
                "amount": airtime_amount,
                "response": None,
                "rapidpro_user_uuid": None,
                "org": self.org.name,
                "timestamp": "2019-03-14 01:30:00",
                "status": TopupAttempt.CREATED,
            },
        )

    @freeze_time("2019-03-14 01:30:00")
    def test_string_2(self):
        msisdn = "+27820000001"
        airtime_amount = 333
        from_string = "bob"
        user_uuid = "3333-abc"
        TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            rapidpro_user_uuid=user_uuid,
            amount=airtime_amount,
            response=TOPUP_RESPONSE_DICT,
            org=self.org,
        )
        topup_attempt = TopupAttempt.objects.last()
        self.assertEqual(
            json.loads(topup_attempt.__str__()),
            {
                "id": topup_attempt.id,
                "sidekick_version": pkg_resources.get_distribution(
                    "rp-sidekick"
                ).version,
                "msisdn": clean_msisdn(msisdn),
                "from_string": from_string,
                "amount": airtime_amount,
                "response": TOPUP_RESPONSE_DICT,
                "rapidpro_user_uuid": user_uuid,
                "org": self.org.name,
                "timestamp": "2019-03-14 01:30:00",
                "status": TopupAttempt.SUCEEDED,
            },
        )

    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_make_request_success(self, fake_make_topup):
        fake_make_topup.return_value = TOPUP_RESPONSE_DICT
        self.assertFalse(fake_make_topup.called)

        msisdn = "+27820000001"
        airtime_amount = 333
        from_string = "bob"

        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
        )
        self.assertEqual(topup_attempt.status, TopupAttempt.CREATED)

        topup_attempt.make_request()

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )

        topup_attempt = TopupAttempt.objects.last()
        self.assertEqual(topup_attempt.response, TOPUP_RESPONSE_DICT)
        self.assertEqual(topup_attempt.status, TopupAttempt.SUCEEDED)

    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_make_request_failure(self, fake_make_topup):
        fake_make_topup.return_value = TOPUP_ERROR_RESPONSE_DICT
        self.assertFalse(fake_make_topup.called)

        msisdn = "+27820000001"
        airtime_amount = 333
        from_string = "bob"

        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
        )
        self.assertEqual(topup_attempt.status, TopupAttempt.CREATED)

        topup_attempt.make_request()

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )

        topup_attempt = TopupAttempt.objects.last()
        self.assertEqual(topup_attempt.response, TOPUP_ERROR_RESPONSE_DICT)
        self.assertEqual(topup_attempt.status, TopupAttempt.FAILED)
