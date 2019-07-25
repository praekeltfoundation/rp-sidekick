import tempfile
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from openpyxl import Workbook

from rp_gpconnect.models import ContactImport, trigger_contact_import
from rp_gpconnect.tasks import import_or_update_contact, process_contact_import
from sidekick.models import Organization
from sidekick.tests.utils import assertCallMadeWith


def create_temp_xlsx_file(temp_file, msisdns):
    wb = Workbook()
    sheet = wb.create_sheet("GP Connect daily report", 0)
    sheet["A1"] = "msisdn"
    sheet["B1"] = "something_else"
    for x in range(len(msisdns)):
        sheet.cell(row=(x + 2), column=1, value=msisdns[x])
        sheet.cell(row=(x + 2), column=2, value="stuuuuff")
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
    @patch("rp_gpconnect.tasks.import_or_update_contact.delay")
    def test_contact_import_calls_contact_task_for_each_row(
        self, mock_contact_update_task, mock_logger
    ):
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx")
        contacts_file = create_temp_xlsx_file(
            temp_file, ["+27000000001", "+27000000002"]
        ).name
        import_obj = ContactImport.objects.create(
            file=contacts_file, org=self.org, created_by=self.user
        )

        process_contact_import(import_obj.pk)

        mock_logger.info.assert_called_with(
            "Importing contacts for file: %s" % contacts_file
        )

        self.assertEqual(mock_contact_update_task.call_count, 2)
        mock_contact_update_task.assert_any_call(
            {"msisdn": "+27000000001", "something_else": "stuuuuff"}, self.org.pk
        )
        mock_contact_update_task.assert_any_call(
            {"msisdn": "+27000000002", "something_else": "stuuuuff"}, self.org.pk
        )


class ImportOrUpdateContactTaskTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Organization", url="http://localhost:8002/", token="REPLACEME"
        )
        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )

    @patch("rp_gpconnect.tasks.log")
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("rp_gpconnect.tasks.get_whatsapp_contact_id", autospec=True)
    def test_contact_task_skips_if_no_wa_id(
        self, mock_get_whatsapp_contact_id, mock_get_rp_contact, mock_logger
    ):
        mock_get_whatsapp_contact_id.return_value = None

        import_or_update_contact(
            {"msisdn": "+27000000001", "something_else": "stuuuuff"}, self.org.pk
        )
        mock_get_whatsapp_contact_id.assert_called_with(self.org, "+27000000001")
        mock_get_rp_contact.assert_not_called()
        mock_logger.info.assert_called_with(
            "Skipping contact +27000000001. No WhatsApp Id."
        )

    @patch("temba_client.v2.TembaClient.create_contact")
    @patch("temba_client.v2.TembaClient.update_contact")
    @patch("temba_client.v2.TembaClient.get_contacts")
    @patch("rp_gpconnect.tasks.get_whatsapp_contact_id")
    def test_contact_task_if_contact_exists(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_rp_contact,
        mock_update_rp_contact,
        mock_create_rp_contact,
    ):
        mock_get_whatsapp_contact_id.return_value = "27000000001"

        mock_contact_object = Mock()
        mock_contact_object.uuid = "123456"
        mock_contact_object.urns = ["tel:+27000000001"]

        mock_get_rp_contact.return_value.first.return_value = mock_contact_object

        import_or_update_contact(
            {"msisdn": "+27000000001", "something_else": "stuuuuff"}, self.org.pk
        )
        mock_get_whatsapp_contact_id.assert_called_with(self.org, "+27000000001")

        self.assertEqual(mock_get_rp_contact.call_count, 1)
        mock_update_rp_contact.assert_called_with(
            contact="123456", urns=["tel:+27000000001", "whatsapp:27000000001"]
        )

        mock_create_rp_contact.assert_not_called()

    @patch("temba_client.v2.TembaClient.create_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.update_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("rp_gpconnect.tasks.get_whatsapp_contact_id", autospec=True)
    def test_contact_task_if_new_contact(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_rp_contact,
        mock_update_rp_contact,
        mock_create_rp_contact,
    ):
        mock_get_whatsapp_contact_id.return_value = "27000000001"

        mock_get_rp_contact.return_value.first.side_effect = [None, None]

        import_or_update_contact(
            {"msisdn": "+27000000001", "something_else": "stuuuuff"}, self.org.pk
        )

        self.assertEqual(mock_get_rp_contact.call_count, 2)
        call_1_args, call_2_args = mock_get_rp_contact.call_args_list
        assertCallMadeWith(call_1_args, urn="tel:+27000000001")
        assertCallMadeWith(call_2_args, urn="whatsapp:27000000001")

        mock_update_rp_contact.assert_not_called()

        assertCallMadeWith(
            mock_create_rp_contact.call_args,
            urns=["tel:+27000000001", "whatsapp:27000000001"],
        )
