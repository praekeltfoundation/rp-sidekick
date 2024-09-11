import json
from datetime import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class GetMsisdnTimezonesTest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser("adminuser", "admin_password")

    def test_auth_required_to_get_timezones(self):
        response = self.client.post(
            "/timezone_utils/timezones/",
            data={"contacts": [{"msisdn": "something"}]},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_no_msisdn_returns_400(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/timezone_utils/timezones/",
            data=json.dumps({"contact": {"urn": "something"}}),
            content_type="application/json",
        )

        self.assertEqual(response.data, {"msisdn": ["This field is required."]})
        self.assertEqual(response.status_code, 400)

    def test_phonenumber_unparseable_returns_400(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/timezone_utils/timezones/",
            data=json.dumps({"msisdn": "something"}),
            content_type="application/json",
        )

        self.assertEqual(
            response.data,
            {"msisdn": ["This value must be a phone number with a region prefix."]},
        )
        self.assertEqual(response.status_code, 400)

    def test_not_possible_phonenumber_returns_400(self):
        # If the length of a number doesn't match accepted length for it's region
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/timezone_utils/timezones/",
            data=json.dumps({"msisdn": "120012301"}),
            content_type="application/json",
        )

        self.assertEqual(
            response.data,
            {"msisdn": ["This value must be a phone number with a region prefix."]},
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_phonenumber_returns_400(self):
        # If a phone number is invalid for it's region
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/timezone_utils/timezones/",
            data=json.dumps({"msisdn": "12001230101"}),
            content_type="application/json",
        )

        self.assertEqual(
            response.data,
            {"msisdn": ["This value must be a phone number with a region prefix."]},
        )
        self.assertEqual(response.status_code, 400)

    def test_phonenumber_with_plus(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/timezone_utils/timezones/",
            data=json.dumps({"msisdn": "+27345678910"}),
            content_type="application/json",
        )

        self.assertEqual(
            response.data, {"success": True, "timezones": ["Africa/Johannesburg"]}
        )
        self.assertEqual(response.status_code, 200)

    def test_single_timezone_number(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/timezone_utils/timezones/",
            data=json.dumps({"msisdn": "27345678910"}),
            content_type="application/json",
        )

        self.assertEqual(
            response.data, {"success": True, "timezones": ["Africa/Johannesburg"]}
        )
        self.assertEqual(response.status_code, 200)

    def test_multiple_timezone_number_returns_all(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            "/timezone_utils/timezones/",
            data=json.dumps({"msisdn": "61498765432"}),
            content_type="application/json",
        )

        self.assertEqual(
            response.data,
            {
                "success": True,
                "timezones": [
                    "Australia/Adelaide",
                    "Australia/Brisbane",
                    "Australia/Eucla",
                    "Australia/Lord_Howe",
                    "Australia/Perth",
                    "Australia/Sydney",
                    "Indian/Christmas",
                    "Indian/Cocos",
                ],
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_return_one_flag_gives_middle_timezone(self):
        self.client.force_authenticate(user=self.admin_user)

        with patch("timezone_utils.views.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2022, 8, 8)
            response = self.client.post(
                "/timezone_utils/timezones/?return_one=true",
                data=json.dumps({"msisdn": "61498765432"}),
                content_type="application/json",
            )

        self.assertEqual(
            response.data, {"success": True, "timezones": ["Australia/Adelaide"]}
        )
        self.assertEqual(response.status_code, 200)
