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

    @patch("rp_asos.tasks.create_hospital_groups.s")
    @patch("rp_asos.tasks.patient_data_check.s")
    def test_start_patient_check(
        self, mock_patient_data_check, mock_create_hospital_groups
    ):
        """
        Valid request test.

        If this is a valid request, a 202 status should be returned and the
        task should be started.
        """
        mock_create_hospital_groups.return_value = self.project.id
        self.org.users.add(self.user)

        survey_url = reverse(
            "rp_asos.start_patient_check", args=[self.project.id]
        )

        response = self.client.post(
            survey_url, {}, content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_create_hospital_groups.assert_called()
        mock_patient_data_check.assert_called()

    @patch("rp_asos.tasks.create_hospital_groups.s")
    @patch("rp_asos.tasks.patient_data_check.s")
    def test_not_in_org(
        self, mock_patient_data_check, mock_create_hospital_groups
    ):
        """
        Not in organization test.

        If the user is not linked to the organization of the project, a 401
        error should be returned and the task should not be started.
        """
        survey_url = reverse(
            "rp_asos.start_patient_check", args=[self.project.id]
        )

        response = self.client.post(
            survey_url, {}, content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_patient_data_check.assert_not_called()
        mock_create_hospital_groups.assert_not_called()
