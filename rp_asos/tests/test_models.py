import datetime
import json
from unittest.mock import patch

import responses
from django.test import TestCase
from freezegun import freeze_time

from rp_asos.models import Hospital, ScreeningRecord
from rp_redcap.tests.base import RedcapBaseTestCase


class TestHospitalModelTask(RedcapBaseTestCase, TestCase):
    def setUp(self):
        self.org = self.create_org()
        self.project = self.create_project(self.org)

    def create_hospital(self, nomination_urn="+27321", whatsapp_group_id=None):
        return Hospital.objects.create(
            name="Test Hospital One",
            project_id=self.project.id,
            data_access_group="my_test_hospital",
            rapidpro_flow="123123123",
            hospital_lead_urn="+27123",
            hospital_lead_name="Tony Test",
            nomination_urn=nomination_urn,
            nomination_name="Peter Test",
            whatsapp_group_id=whatsapp_group_id,
        )

    def test_hospital_status_no_screening_record(self):
        """
        If there is no screening record do nothing
        """
        hospital = self.create_hospital()
        hospital.check_and_update_status()

        hospital.refresh_from_db()
        self.assertTrue(hospital.is_active)

    def test_hospital_status_screening_record_empty_date(self):
        """
        If there is no date on the screening record do nothing
        """
        hospital = self.create_hospital()
        ScreeningRecord.objects.create(
            **{
                "hospital": hospital,
                "week_1_case_count": 50,
                "week_2_case_count": 45,
                "week_3_case_count": 5,
                "week_4_case_count": 2,
                "total_eligible": 102,
            }
        )

        hospital.check_and_update_status()

        hospital.refresh_from_db()
        self.assertTrue(hospital.is_active)

    @freeze_time("2019-01-24 01:30:00")
    def test_hospital_status_not_enough_cases(self):
        """
        If there is not enough cases and it has not been 4 weeks, do nothing
        """
        hospital = self.create_hospital()
        ScreeningRecord.objects.create(
            **{
                "hospital": hospital,
                "date": datetime.date(2019, 1, 7),
                "week_1_case_count": 50,
                "total_eligible": 50,
            }
        )

        hospital.check_and_update_status()

        hospital.refresh_from_db()
        self.assertTrue(hospital.is_active)

    @freeze_time("2019-01-24 01:30:00")
    def test_hospital_status_enough_cases(self):
        """
        If there is enough cases in the first week and we are 4 days past the
        new week, disable hospital
        """
        hospital = self.create_hospital()
        ScreeningRecord.objects.create(
            **{
                "hospital": hospital,
                "date": datetime.date(2019, 1, 7),
                "week_1_case_count": 101,
                "week_2_case_count": 0,
                "week_3_case_count": 0,
                "week_4_case_count": 0,
                "total_eligible": 101,
            }
        )

        hospital.check_and_update_status()

        hospital.refresh_from_db()
        self.assertFalse(hospital.is_active)

    @freeze_time("2019-02-05 01:30:00")
    def test_hospital_status_after_4_weeks(self):
        """
        If the case count is too low and 4 weeks have passed but not the 4 days
        after that, do nothing.
        """
        hospital = self.create_hospital()
        ScreeningRecord.objects.create(
            **{
                "hospital": hospital,
                "date": datetime.date(2019, 1, 7),
                "week_1_case_count": 20,
                "week_2_case_count": 20,
                "week_3_case_count": 20,
                "week_4_case_count": 20,
                "total_eligible": 80,
            }
        )

        hospital.check_and_update_status()

        hospital.refresh_from_db()
        self.assertTrue(hospital.is_active)

    @freeze_time("2019-02-07 01:30:00")
    def test_hospital_status_after_4_weeks_4_days(self):
        """
        If the case count is low and 4 days and 4 weeks have passed, disable
        the hospital.
        """
        hospital = self.create_hospital()
        ScreeningRecord.objects.create(
            **{
                "hospital": hospital,
                "date": datetime.date(2019, 1, 7),
                "week_1_case_count": 20,
                "week_2_case_count": 20,
                "week_3_case_count": 20,
                "week_4_case_count": 20,
                "total_eligible": 80,
            }
        )

        hospital.check_and_update_status()

        hospital.refresh_from_db()
        self.assertFalse(hospital.is_active)

    @patch("sidekick.utils.create_whatsapp_group")
    def test_create_hospital_wa_group_no_group_id(self, mock_create_whatsapp_group):
        mock_create_whatsapp_group.return_value = "group-id-1"

        hospital = self.create_hospital()

        hospital.create_hospital_wa_group()

        self.assertEqual(hospital.whatsapp_group_id, "group-id-1")
        mock_create_whatsapp_group.assert_called_with(
            self.org, "{} - ASOS2".format(hospital.name[:17])
        )

    @patch("sidekick.utils.create_whatsapp_group")
    def test_create_hospital_wa_group_with_group_id(self, mock_create_whatsapp_group):
        hospital = self.create_hospital(whatsapp_group_id="group-id-2")

        hospital.create_hospital_wa_group()

        self.assertEqual(hospital.whatsapp_group_id, "group-id-2")
        mock_create_whatsapp_group.assert_not_called()

    @patch("sidekick.utils.get_whatsapp_group_info")
    def test_get_wa_group_info(self, mock_get_whatsapp_group_info):
        mock_get_whatsapp_group_info.return_value = {"group": "info"}

        hospital = self.create_hospital(whatsapp_group_id="group-id-3")

        group_info = hospital.get_wa_group_info()

        self.assertEqual(group_info, {"group": "info", "id": "group-id-3"})
        mock_get_whatsapp_group_info.assert_called_with(self.org, "group-id-3")

    @patch("sidekick.utils.get_whatsapp_group_info")
    def test_get_wa_group_info_no_id(self, mock_get_whatsapp_group_info):
        hospital = self.create_hospital()

        group_info = hospital.get_wa_group_info()

        self.assertEqual(group_info, {"participants": [], "admins": []})
        mock_get_whatsapp_group_info.assert_not_called()

    @patch("sidekick.utils.get_whatsapp_contact_id")
    @patch("sidekick.utils.add_whatsapp_group_admin")
    def test_add_admins_noop(self, mock_add_admin, mock_get_wa_id):
        hospital = self.create_hospital()
        mock_get_wa_id.return_value = "wa-id-1"

        wa_ids = hospital.add_group_admins(
            {"participants": ["wa-id-1"], "admins": ["wa-id-1"]}, ["msisdn-1"]
        )

        self.assertEqual(wa_ids, ["wa-id-1"])

        mock_add_admin.assert_not_called()
        mock_get_wa_id.assert_called_with(self.org, "msisdn-1")

    @patch("sidekick.utils.get_whatsapp_contact_id")
    @patch("sidekick.utils.add_whatsapp_group_admin")
    def test_add_admins(self, mock_add_admin, mock_get_wa_id):
        hospital = self.create_hospital()
        mock_get_wa_id.return_value = "wa-id-2"

        wa_ids = hospital.add_group_admins(
            {
                "id": "group-id-5",
                "participants": ["wa-id-1", "wa-id-2"],
                "admins": ["wa-id-1"],
            },
            ["msisdn-2"],
        )

        self.assertEqual(wa_ids, ["wa-id-2"])

        mock_add_admin.assert_called_with(self.org, "group-id-5", "wa-id-2")
        mock_get_wa_id.assert_called_with(self.org, "msisdn-2")

    @patch("sidekick.utils.get_whatsapp_contact_id")
    @patch("sidekick.utils.add_whatsapp_group_admin")
    def test_add_admins_no_wa_contact(self, mock_add_admin, mock_get_wa_id):
        hospital = self.create_hospital()
        mock_get_wa_id.return_value = None

        wa_ids = hospital.add_group_admins(
            {"participants": ["wa-id-1"], "admins": ["wa-id-1"]}, ["msisdn-1"]
        )

        self.assertEqual(wa_ids, [])

        mock_add_admin.assert_not_called()
        mock_get_wa_id.assert_called_with(self.org, "msisdn-1")

    @responses.activate
    @freeze_time("2018-06-06 01:30:00")
    @patch("sidekick.utils.update_rapidpro_whatsapp_urn")
    def test_send_message_not_in_group(self, mock_update_wa_urn):
        responses.add(
            responses.POST,
            "http://localhost:8002/api/v2/flow_starts.json",
            json={
                "uuid": "09d23a05",
                "flow": {"uuid": "f5901b62", "name": "Send Reminder"},
                "groups": [{"uuid": "f5901b62", "name": "Investigators"}],
                "contacts": [{"uuid": "f5901b62", "name": "Ryan Lewis"}],
                "restart_participants": True,
                "status": "complete",
                "extra": {},
                "created_on": "2013-08-19T19:11:21.082Z",
                "modified_on": "2013-08-19T19:11:21.082Z",
            },
            status=200,
            match_querystring=True,
        )

        hospital = self.create_hospital(nomination_urn=None)

        hospital.send_message("Test message")

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "123123123",
                "restart_participants": 1,
                "urns": ["tel:+27123"],
                "extra": {
                    "hospital_name": "Test Hospital One",
                    "week": 23,
                    "reminder": "Test message",
                    "contact_name": "Tony Test",
                },
            },
        )

        mock_update_wa_urn.assert_called()

    @responses.activate
    @freeze_time("2018-06-06 01:30:00")
    @patch("sidekick.utils.update_rapidpro_whatsapp_urn")
    def test_send_message_not_in_group_nominated_urn(self, mock_update_wa_urn):
        responses.add(
            responses.POST,
            "http://localhost:8002/api/v2/flow_starts.json",
            json={
                "uuid": "09d23a05",
                "flow": {"uuid": "f5901b62", "name": "Send Reminder"},
                "groups": [{"uuid": "f5901b62", "name": "Investigators"}],
                "contacts": [{"uuid": "f5901b62", "name": "Ryan Lewis"}],
                "restart_participants": True,
                "status": "complete",
                "extra": {},
                "created_on": "2013-08-19T19:11:21.082Z",
                "modified_on": "2013-08-19T19:11:21.082Z",
            },
            status=200,
            match_querystring=True,
        )

        hospital = self.create_hospital()

        hospital.send_message(["Test message"])

        self.assertEqual(len(responses.calls), 2)

        mock_update_wa_urn.assert_called()

    @responses.activate
    @patch("sidekick.utils.get_whatsapp_group_info")
    @patch("sidekick.utils.send_whatsapp_group_message")
    def test_send_message_in_group(self, mock_send_group, mock_get_whatsapp_group_info):
        mock_get_whatsapp_group_info.return_value = {"participants": ["27123"]}

        hospital = self.create_hospital(
            nomination_urn=None, whatsapp_group_id="group-id-1"
        )

        hospital.send_message("Test message")

        mock_send_group.assert_called_with(self.org, "group-id-1", "Test message")

    @responses.activate
    @patch("sidekick.utils.get_whatsapp_group_info")
    @patch("sidekick.utils.send_whatsapp_group_message")
    def test_send_message_in_group_with_nomination(
        self, mock_send_group, mock_get_whatsapp_group_info
    ):
        mock_get_whatsapp_group_info.return_value = {"participants": ["27123", "27321"]}

        hospital = self.create_hospital(whatsapp_group_id="group-id-1")

        hospital.send_message(["Test message"])

        mock_send_group.assert_called_once()
