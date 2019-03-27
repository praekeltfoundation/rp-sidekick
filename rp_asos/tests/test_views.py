from django.contrib.auth.models import User
from django.urls import reverse
from mock import patch
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient

from rp_redcap.tests.base import RedcapBaseTestCase


class CheckViewTests(RedcapBaseTestCase, APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client_noauth = APIClient()

        self.username = "testuser"
        self.password = "testpass"
        self.user = User.objects.create_user(
            self.username, "testuser@example.com", self.password
        )
        token = Token.objects.get(user=self.user)
        self.token = token.key
        self.client.credentials(
            HTTP_AUTHORIZATION="Token {}".format(self.token)
        )

        self.org = self.create_org()
        self.project = self.create_project(self.org)

    @patch("rp_asos.tasks.patient_data_check.delay")
    def test_start_patient_check(self, mock_patient_data_check):
        """
        Valid request test.

        If this is a valid request, a 202 status should be returned and the
        task should be started.
        """
        self.org.users.add(self.user)

        survey_url = reverse(
            "rp_asos.start_patient_check", args=[self.project.id]
        )

        response = self.client.post(
            survey_url, {}, content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_patient_data_check.assert_called_with(self.project.id)
