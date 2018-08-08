from django.contrib.auth.models import User
from django.urls import reverse
from mock import patch
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIClient


class SurveyCheckViewTests(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.client_noauth = APIClient()

        self.username = 'testuser'
        self.password = 'testpass'
        self.user = User.objects.create_user(self.username,
                                             'testuser@example.com',
                                             self.password)
        token = Token.objects.create(user=self.user)
        self.token = token.key
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)

    @patch('rp_redcap.tasks.survey_check.delay')
    def test_no_auth(self, mock_survey_check):
        """
        No authentication test.

        If there is no or invalid auth supplied, a 401 error should be
        returned and the task should not be started.
        """
        survey_url = reverse('rp_redcap.start_survey_check', args=["survey_1"])

        response = self.client_noauth.post(
            survey_url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        mock_survey_check.assert_not_called()

    @patch('rp_redcap.tasks.survey_check.delay')
    def test_start_survey_check(self, mock_survey_check):
        """
        Valid request test.

        If this is a valid request, a 202 status should be returned and the
        task should be started.
        """
        survey_url = reverse('rp_redcap.start_survey_check', args=["survey_1"])

        response = self.client.post(
            survey_url, {}, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_survey_check.assert_called_with("survey_1")
