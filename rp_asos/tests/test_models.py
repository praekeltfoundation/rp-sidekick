from django.test import TestCase
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

    @patch("sidekick.utils.send_whatsapp_template_message")
    @patch("sidekick.utils.get_whatsapp_group_invite_link")
    def test_invites_noop(self, mock_get_invite_link, mock_send):
        hospital = self.create_hospital()
        hospital.send_group_invites(
            {"participants": ["wa-id-1", "wa-id-2"]}, ["wa-id-1", "wa-id-2"]
        )
        mock_get_invite_link.assert_not_called()
        mock_send.assert_not_called()

    @patch("sidekick.utils.send_whatsapp_template_message")
    @patch("sidekick.utils.get_whatsapp_group_invite_link")
    def test_invites_send(self, mock_get_invite_link, mock_send):
        mock_get_invite_link.return_value = "test-link"

        hospital = self.create_hospital()

        hospital.send_group_invites(
            {"id": "group-id-4", "participants": ["wa-id-2"]},
            ["wa-id-1", "wa-id-2"],
        )
        mock_get_invite_link.assert_called_with(self.org, "group-id-4")
        mock_send.assert_called_with(
            self.org,
            "wa-id-1",
            "whatsapp:hsm:npo:praekeltpbc",
            "asos2_notification2",
            {"default": "Hi, please join the ASOS2 Whatsapp group: test-link"},
        )

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
