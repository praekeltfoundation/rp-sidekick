import os
import tempfile
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse_lazy
from openpyxl import Workbook

from rp_gpconnect.models import ContactImport
from sidekick.models import Organization


class ContactImportViewTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Organization", url="http://localhost:8002/", token="REPLACEME"
        )
        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )

    def test_login_required(self):
        # Not logged in
        response = self.client.get(reverse_lazy("contact_import"))
        self.assertRedirects(
            response, "/admin/login/?next=/gpconnect/", fetch_redirect_response=False
        )
        # Logged in
        self.client.login(username="username", password="password")
        response = self.client.get(reverse_lazy("contact_import"))
        self.assertContains(response, "Upload Contacts")

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    def test_request_user_added_to_object(self):
        self.client.login(username="username", password="password")
        # Create file for upload
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx")
        Workbook().save(temp_file)
        temp_file.seek(0)

        try:
            self.client.post(
                reverse_lazy("contact_import"), {"org": self.org.pk, "file": temp_file}
            )
        finally:
            # Clean up filesystem
            upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads/gpconnect/")
            filepath = os.path.join(upload_dir, os.path.basename(temp_file.name))
            os.remove(filepath)
        imports = ContactImport.objects.all()
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].created_by, self.user)

    @override_settings(MEDIA_ROOT=tempfile.gettempdir())
    @patch("rp_gpconnect.forms.process_contact_import.delay")
    def test_form_submission_calls_process_task(self, mock_task):
        self.client.login(username="username", password="password")
        # Create file for upload
        temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx")
        Workbook().save(temp_file)
        temp_file.seek(0)

        try:
            self.client.post(
                reverse_lazy("contact_import"), {"org": self.org.pk, "file": temp_file}
            )
        finally:
            # Clean up filesystem
            upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads/gpconnect/")
            filepath = os.path.join(upload_dir, os.path.basename(temp_file.name))
            os.remove(filepath)
            os.rmdir(os.path.join(tempfile.gettempdir(), "uploads/gpconnect"))
            os.rmdir(os.path.join(tempfile.gettempdir(), "uploads"))
        imports = ContactImport.objects.all()
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].created_by, self.user)
        mock_task.assert_called_with(imports[0].pk)
