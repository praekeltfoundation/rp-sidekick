import os
import tempfile
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from openpyxl import Workbook

from rp_gpconnect.models import ContactImport, Flow, trigger_contact_import
from rp_gpconnect.tasks import (
    import_or_update_contact,
    process_contact_import,
    pull_new_import_file,
)
from sidekick.models import Organization
from sidekick.tests.utils import assertCallMadeWith


def create_temp_xlsx_file(temp_file, msisdns):
    wb = Workbook()
    sheet = wb.create_sheet("GP Connect daily report", 0)
    sheet["A1"] = "msisdn"
    sheet["B1"] = "something_else"
    sheet["C1"] = "patients_tested_positive"
    for x in range(len(msisdns)):
        sheet.cell(row=(x + 2), column=1, value=msisdns[x])
        sheet.cell(row=(x + 2), column=2, value="stuuuuff")
        sheet.cell(row=(x + 2), column=3, value=(x % 2))
    wb.save(temp_file)
    return temp_file


class PullNewImportFileTaskTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Organization", url="http://localhost:8002/", token="REPLACEME"
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
    def test_new_file_creates_contact_import_obj(self):
        self.assertEqual(ContactImport.objects.count(), 0)
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".xlsx", dir="/tmp/uploads/gpconnect"
        )

        pull_new_import_file(self.org.pk)
        self.assertEqual(ContactImport.objects.count(), 1)
        obj = ContactImport.objects.first()
        self.assertEqual(obj.file.name, os.path.basename(temp_file.name))

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_only_one_file_creates_contact_import_obj(self):
        self.assertEqual(ContactImport.objects.count(), 0)
        temp_file_1 = tempfile.NamedTemporaryFile(
            suffix=".xlsx", dir="/tmp/uploads/gpconnect"
        )
        temp_file_2 = tempfile.NamedTemporaryFile(
            suffix=".xlsx", dir="/tmp/uploads/gpconnect"
        )

        pull_new_import_file(self.org.pk)
        self.assertEqual(ContactImport.objects.count(), 1)
        obj = ContactImport.objects.first()
        existing_files = [
            os.path.basename(temp_file_1.name),
            os.path.basename(temp_file_2.name),
        ]
        self.assertIn(obj.file.name, existing_files)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_already_processed_file_doesnt_create_cotact_import_obj(self):
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".xlsx", dir="/tmp/uploads/gpconnect"
        )
        ContactImport.objects.create(file=temp_file.name, org=self.org)
        self.assertEqual(ContactImport.objects.count(), 1)

        pull_new_import_file(self.org.pk)
        self.assertEqual(ContactImport.objects.count(), 1)


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
    def test_contact_import_calls_contact_task_for_each_positive_row(
        self, mock_contact_update_task, mock_logger
    ):
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx")
        contacts_file = create_temp_xlsx_file(
            temp_file, ["+27000000001", "+27000000002", "+27000000003", "+27000000004"]
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
            {
                "msisdn": "+27000000002",
                "something_else": "stuuuuff",
                "patients_tested_positive": 1,
            },
            self.org.pk,
        )
        mock_contact_update_task.assert_any_call(
            {
                "msisdn": "+27000000004",
                "something_else": "stuuuuff",
                "patients_tested_positive": 1,
            },
            self.org.pk,
        )


class ImportOrUpdateContactTaskTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Organization", url="http://localhost:8002/", token="REPLACEME"
        )
        self.create_flow = Flow.objects.create(
            type="new_contact", rapidpro_flow="new_contact_flow", org=self.org
        )
        self.update_flow = Flow.objects.create(
            type="contact_update", rapidpro_flow="contact_update_flow", org=self.org
        )
        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )

    @patch("temba_client.v2.TembaClient.create_flow_start")
    @patch("temba_client.v2.TembaClient.update_contact")
    @patch("temba_client.v2.TembaClient.get_contacts")
    @patch("rp_gpconnect.tasks.get_whatsapp_contact_id")
    def test_contact_task_if_contact_exists_without_wa_id(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_rp_contact,
        mock_update_rp_contact,
        mock_create_flow_start,
    ):
        mock_get_whatsapp_contact_id.return_value = None

        # Create a mock contact that is already up to date
        mock_contact_object = Mock()
        mock_contact_object.uuid = "123456"
        mock_contact_object.urns = ["tel:+27000000001"]
        mock_contact_object.fields = {
            "something_else": "stuuuuff",
            "has_whatsapp": False,
        }
        mock_get_rp_contact.return_value.first.return_value = mock_contact_object

        import_or_update_contact(
            {"msisdn": "+27000000001", "something_else": "stuuuuff"}, self.org.pk
        )

        mock_get_whatsapp_contact_id.assert_called_with(self.org, "+27000000001")
        self.assertEqual(mock_get_rp_contact.call_count, 1)
        mock_update_rp_contact.assert_not_called()
        mock_create_flow_start.assert_not_called()

    @patch("temba_client.v2.TembaClient.create_flow_start")
    @patch("temba_client.v2.TembaClient.create_contact")
    @patch("temba_client.v2.TembaClient.update_contact")
    @patch("temba_client.v2.TembaClient.get_contacts")
    @patch("rp_gpconnect.tasks.get_whatsapp_contact_id")
    def test_contact_task_if_contact_exists_with_wa_id(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_rp_contact,
        mock_update_rp_contact,
        mock_create_rp_contact,
        mock_create_flow_start,
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
        assertCallMadeWith(
            mock_create_flow_start.call_args,
            flow=self.update_flow.rapidpro_flow,
            urns=["tel:+27000000001", "whatsapp:27000000001"],
            restart_participants=True,
            extra={"something_else": "stuuuuff", "has_whatsapp": True},
        )

        mock_create_rp_contact.assert_not_called()

    @patch("temba_client.v2.TembaClient.create_flow_start", autospec=True)
    @patch("temba_client.v2.TembaClient.create_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.update_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("rp_gpconnect.tasks.get_whatsapp_contact_id", autospec=True)
    def test_contact_task_if_new_contact_without_wa_id(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_rp_contact,
        mock_update_rp_contact,
        mock_create_rp_contact,
        mock_create_flow_start,
    ):
        mock_get_whatsapp_contact_id.return_value = None

        mock_get_rp_contact.return_value.first.side_effect = [None, None]

        import_or_update_contact(
            {"msisdn": "+27000000001", "something_else": "stuuuuff"}, self.org.pk
        )

        self.assertEqual(mock_get_rp_contact.call_count, 1)
        mock_update_rp_contact.assert_not_called()

        assertCallMadeWith(mock_create_rp_contact.call_args, urns=["tel:+27000000001"])

        assertCallMadeWith(
            mock_create_flow_start.call_args,
            flow=self.create_flow.rapidpro_flow,
            urns=["tel:+27000000001"],
            restart_participants=True,
            extra={"something_else": "stuuuuff", "has_whatsapp": False},
        )

    @patch("temba_client.v2.TembaClient.create_flow_start", autospec=True)
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
        mock_create_flow_start,
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

        assertCallMadeWith(
            mock_create_flow_start.call_args,
            flow=self.create_flow.rapidpro_flow,
            urns=["tel:+27000000001", "whatsapp:27000000001"],
            restart_participants=True,
            extra={"something_else": "stuuuuff", "has_whatsapp": True},
        )
