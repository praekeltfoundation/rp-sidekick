import tempfile

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase, override_settings
from django.urls import reverse_lazy
from openpyxl import Workbook

from rp_gpconnect.models import ContactImport, trigger_contact_import
from sidekick.models import Organization


class ContactImportViewTests(TestCase):
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

        self.client.post(reverse_lazy("contact_import"), {"org": 1, "file": temp_file})
        imports = ContactImport.objects.all()
        self.assertEqual(len(imports), 1)
        self.assertEqual(imports[0].created_by, self.user)
