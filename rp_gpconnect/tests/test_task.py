import tempfile
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from openpyxl import Workbook

from rp_gpconnect.models import ContactImport, trigger_contact_import
from rp_gpconnect.tasks import process_contact_import
from sidekick.models import Organization
from sidekick.tests.utils import assertCallMadeWith


def create_temp_xlsx_file(temp_file, msisdns):
    wb = Workbook()
    sheet = wb.create_sheet("GP Connect daily report", 0)
    sheet["A1"] = "msisdn"
    for x in range(len(msisdns)):
        sheet.cell(row=(x + 2), column=1, value=msisdns[x])
    wb.save(temp_file)
    return temp_file


class ProcessContactImportTaskTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Organization", url="http://localhost:8002/", token="REPLACEME"
        )
        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )
        post_save.disconnect(
            receiver=trigger_contact_import,
            sender=ContactImport,
            dispatch_uid="trigger_contact_import",
        )

    def tearDown(self):
        post_save.connect(
            trigger_contact_import,
            sender=ContactImport,
            dispatch_uid="trigger_contact_import",
        )

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch("rp_gpconnect.tasks.log")
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("rp_gpconnect.tasks.get_whatsapp_contact_id", autospec=True)
    def test_contact_import_skips_if_no_wa_id(
        self, mock_get_whatsapp_contact_id, mock_get_rp_contact, mock_logger
    ):
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx")
        contacts_file = create_temp_xlsx_file(temp_file, ["+27723456789"]).name
        import_obj = ContactImport.objects.create(
            file=contacts_file, org=self.org, created_by=self.user
        )

        mock_get_whatsapp_contact_id.return_value = None

        process_contact_import(import_obj.pk)
        mock_get_whatsapp_contact_id.assert_called_with(self.org, "+27723456789")
        mock_get_rp_contact.assert_not_called()
        mock_logger.info.assert_called_with(
            "Skipping contact +27723456789. No WhatsApp Id."
        )

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch("temba_client.v2.TembaClient.create_contact")
    @patch("temba_client.v2.TembaClient.update_contact")
    @patch("temba_client.v2.TembaClient.get_contacts")
    @patch("rp_gpconnect.tasks.get_whatsapp_contact_id")
    def test_contact_import_if_contact_exists(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_rp_contact,
        mock_update_rp_contact,
        mock_create_rp_contact,
    ):
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx")
        contacts_file = create_temp_xlsx_file(temp_file, ["+27723456789"]).name
        import_obj = ContactImport.objects.create(
            file=contacts_file, org=self.org, created_by=self.user
        )

        mock_get_whatsapp_contact_id.return_value = "27723456789"

        mock_contact_object = Mock()
        mock_contact_object.uuid = "123456"
        mock_contact_object.urns = ["tel:+27723456789"]

        mock_get_rp_contact.return_value.first.return_value = mock_contact_object

        process_contact_import(import_obj.pk)
        mock_get_whatsapp_contact_id.assert_called_with(self.org, "+27723456789")

        self.assertEqual(mock_get_rp_contact.call_count, 1)
        mock_update_rp_contact.assert_called_with(
            contact="123456", urns=["tel:+27723456789", "whatsapp:27723456789"]
        )

        mock_create_rp_contact.assert_not_called()

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch("temba_client.v2.TembaClient.create_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.update_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("rp_gpconnect.tasks.get_whatsapp_contact_id", autospec=True)
    def test_contact_import_if_new_contact(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_rp_contact,
        mock_update_rp_contact,
        mock_create_rp_contact,
    ):
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx")
        contacts_file = create_temp_xlsx_file(temp_file, ["+27723456789"]).name
        import_obj = ContactImport.objects.create(
            file=contacts_file, org=self.org, created_by=self.user
        )

        mock_get_whatsapp_contact_id.return_value = "27723456789"

        mock_get_rp_contact.return_value.first.side_effect = [None, None]

        process_contact_import(import_obj.pk)

        self.assertEqual(mock_get_rp_contact.call_count, 2)
        call_1_args, call_2_args = mock_get_rp_contact.call_args_list
        assertCallMadeWith(call_1_args, urn="tel:+27723456789")
        assertCallMadeWith(call_2_args, urn="whatsapp:27723456789")

        mock_update_rp_contact.assert_not_called()

        assertCallMadeWith(
            mock_create_rp_contact.call_args,
            urns=["tel:+27723456789", "whatsapp:27723456789"],
        )
