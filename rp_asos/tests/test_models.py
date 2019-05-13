import json
import responses

from django.test import TestCase
from freezegun import freeze_time
from mock import patch

from rp_asos.models import Hospital
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

    @patch("sidekick.utils.create_whatsapp_group")
    def test_create_hospital_wa_group_no_group_id(
        self, mock_create_whatsapp_group
    ):
        mock_create_whatsapp_group.return_value = "group-id-1"

        hospital = self.create_hospital()

        hospital.create_hospital_wa_group()

        self.assertEqual(hospital.whatsapp_group_id, "group-id-1")
        mock_create_whatsapp_group.assert_called_with(
            self.org, "{} - ASOS2".format(hospital.name[:17])
        )

    @patch("sidekick.utils.create_whatsapp_group")
    def test_create_hospital_wa_group_with_group_id(
        self, mock_create_whatsapp_group
    ):
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
    @patch("sidekick.utils.send_whatsapp_template_message")
    @patch("sidekick.utils.get_whatsapp_group_invite_link")
    def test_invites_noop(
        self, mock_get_invite_link, mock_send, mock_get_wa_id
    ):
        mock_get_wa_id.return_value = "wa-id-1"

        hospital = self.create_hospital()
        wa_ids = hospital.send_group_invites(
            {"participants": ["wa-id-1"]}, ["msisdn-1"]
        )

        self.assertEqual(wa_ids, [])

        mock_get_invite_link.assert_not_called()
        mock_send.assert_not_called()
        mock_get_wa_id.assert_called_with(self.org, "msisdn-1")

    @patch("sidekick.utils.get_whatsapp_contact_id")
    @patch("sidekick.utils.send_whatsapp_template_message")
    @patch("sidekick.utils.get_whatsapp_group_invite_link")
    def test_invites_no_wa_contact(
        self, mock_get_invite_link, mock_send, mock_get_wa_id
    ):
        mock_get_wa_id.return_value = None

        hospital = self.create_hospital()
        wa_ids = hospital.send_group_invites(
            {"participants": ["wa-id-1"]}, ["msisdn-1"]
        )

        self.assertEqual(wa_ids, [])

        mock_get_invite_link.assert_not_called()
        mock_send.assert_not_called()
        mock_get_wa_id.assert_called_with(self.org, "msisdn-1")

    @patch("sidekick.utils.get_whatsapp_contact_id")
    @patch("sidekick.utils.send_whatsapp_template_message")
    @patch("sidekick.utils.get_whatsapp_group_invite_link")
    def test_invites_send(
        self, mock_get_invite_link, mock_send, mock_get_wa_id
    ):
        mock_get_invite_link.return_value = "test-link"
        mock_get_wa_id.return_value = "wa-id-1"

        hospital = self.create_hospital()

        wa_ids = hospital.send_group_invites(
            {"id": "group-id-4", "participants": ["wa-id-2"]}, ["msisdn-1"]
        )

        self.assertEqual(wa_ids, ["wa-id-1"])

        mock_get_invite_link.assert_called_with(self.org, "group-id-4")
        mock_send.assert_called_with(
            self.org,
            "wa-id-1",
            "whatsapp:hsm:npo:praekeltpbc",
            "asos2_notification_v2",
            {"default": "Hi, please join the ASOS2 Whatsapp group: test-link"},
        )
        mock_get_wa_id.assert_called_with(self.org, "msisdn-1")

    @patch("sidekick.utils.add_whatsapp_group_admin")
    def test_add_admins_noop(self, mock_add_admin):
        hospital = self.create_hospital()

        hospital.add_group_admins(
            {
                "participants": ["wa-id-1", "wa-id-2"],
                "admins": ["wa-id-1", "wa-id-2"],
            },
            ["wa-id-1", "wa-id-2"],
        )
        mock_add_admin.assert_not_called()

    @patch("sidekick.utils.add_whatsapp_group_admin")
    def test_add_admins(self, mock_add_admin):
        hospital = self.create_hospital()

        hospital.add_group_admins(
            {
                "id": "group-id-5",
                "participants": ["wa-id-1", "wa-id-2"],
                "admins": ["wa-id-1"],
            },
            ["wa-id-1", "wa-id-2"],
        )
        mock_add_admin.assert_called_with(self.org, "group-id-5", "wa-id-2")

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
    def test_send_message_in_group(
        self, mock_send_group, mock_get_whatsapp_group_info
    ):
        mock_get_whatsapp_group_info.return_value = {"participants": ["27123"]}

        hospital = self.create_hospital(
            nomination_urn=None, whatsapp_group_id="group-id-1"
        )

        hospital.send_message("Test message")

        mock_send_group.assert_called_with(
            self.org, "group-id-1", "Test message"
        )

    @responses.activate
    @patch("sidekick.utils.get_whatsapp_group_info")
    @patch("sidekick.utils.send_whatsapp_group_message")
    def test_send_message_in_group_with_nomination(
        self, mock_send_group, mock_get_whatsapp_group_info
    ):
        mock_get_whatsapp_group_info.return_value = {
            "participants": ["27123", "27321"]
        }

        hospital = self.create_hospital(whatsapp_group_id="group-id-1")

        hospital.send_message(["Test message"])

        mock_send_group.assert_called_once()
