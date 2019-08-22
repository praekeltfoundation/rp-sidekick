from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.files import File
from django.test import TestCase

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

    @patch("rp_gpconnect.tasks.process_contact_import.delay")
    def test_object_creation_does_not_trigger_task(self, mock_task):
        mock_file = MagicMock(spec=File)
        mock_file.name = "test_file.xlsx"
        ContactImport.objects.create(file=mock_file, org=self.org, created_by=self.user)
        mock_task.assert_not_called()
