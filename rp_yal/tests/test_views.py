from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from sidekick.tests.utils import create_org


class TestYalViews(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )
        token = Token.objects.get(user=self.user)
        self.token = token.key

        self.api_client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

        self.org = create_org()
        self.org.users.add(self.user)

    def test_get_ordered_contentset_validation(self):
        response = self.api_client.post(
            reverse(
                "get_ordered_contentset",
                kwargs={"org_id": self.org.id},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"fields": ["This field is required."]})

    @patch("rp_yal.views.get_ordered_content_set")
    def test_get_ordered_contentset(self, mock_get_ocs):
        mock_get_ocs.return_value = 111

        response = self.api_client.post(
            reverse(
                "get_ordered_contentset",
                kwargs={"org_id": self.org.id},
            ),
            data={"fields": {"last_topic_sent": "Connectedness"}},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"ordered_set_id": 111})

        mock_get_ocs.assert_called_with(self.org, {"last_topic_sent": "Connectedness"})
