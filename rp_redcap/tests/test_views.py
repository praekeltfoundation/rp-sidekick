from django.contrib.auth.models import User
from django.urls import reverse
from mock import patch
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient

from .base import RedcapBaseTestCase


class CheckViewTests(RedcapBaseTestCase, APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.client_noauth = APIClient()

        self.username = "testuser"
        self.password = "testpass"
        self.user = User.objects.create_user(
            self.username, "testuser@example.com", self.password
        )
        token = Token.objects.create(user=self.user)
        self.token = token.key
        self.client.credentials(
            HTTP_AUTHORIZATION="Token {}".format(self.token)
        )

        self.org = self.create_org()
        self.project = self.create_project(self.org)

    @patch("rp_redcap.tasks.project_check.delay")
    def test_no_auth(self, mock_project_check):
        """
        No authentication test.

        If there is no or invalid auth supplied, a 401 error should be
        returned and the task should not be started.
        """
        survey_url = reverse(
            "rp_redcap.start_project_check", args=[self.project.id]
        )

        response = self.client_noauth.post(
            survey_url, {}, content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_project_check.assert_not_called()

    @patch("rp_redcap.tasks.project_check.delay")
    def test_project_not_found(self, mock_project_check):
        """
        Project not found test.

        If the project id in the url doesn't exist we should respond with an
        appropriate message.
        """
        survey_url = reverse("rp_redcap.start_project_check", args=[-1])

        response = self.client.post(
            survey_url, {}, content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_project_check.assert_not_called()

    @patch("rp_redcap.tasks.project_check.delay")
    def test_not_in_org(self, mock_project_check):
        """
        Not in organization test.

        If the user is not linked to the organization of the project, a 401
        error should be returned and the task should not be started.
        """
        survey_url = reverse(
            "rp_redcap.start_project_check", args=[self.project.id]
        )

        response = self.client.post(
            survey_url, {}, content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_project_check.assert_not_called()

    @patch("rp_redcap.tasks.project_check.delay")
    def test_start_survey_check(self, mock_project_check):
        """
        Valid request test.

        If this is a valid request, a 202 status should be returned and the
        task should be started.
        """
        self.org.users.add(self.user)

        survey_url = reverse(
            "rp_redcap.start_project_check", args=[self.project.id]
        )

        response = self.client.post(
            survey_url, {}, content_type="application/json"
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_project_check.assert_called_with(self.project.id)
