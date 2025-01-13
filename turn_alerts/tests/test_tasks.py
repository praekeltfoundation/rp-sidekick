from unittest.mock import patch
from urllib.parse import urljoin

from django.test import TestCase

from turn_alerts.tasks import start_turn_journey


class TestStartTurnJourney(TestCase):
    @patch("requests.post")
    def test_start_turn_journey_calls_requests_post(self, mock_requests_post):

        wa_id = "TEST_WA_ID"
        journey_id = "0000077-cb41-4e98-ac3f-de56635a99f6"
        engage_url = "https://whatsapp.praekelt.org"
        engage_token = "ENGAGE_TOKEN"

        expected_url = urljoin(engage_url, f"/v1/stacks/{journey_id}/start")
        expected_headers = {
            "Authorization": f"Bearer {engage_token}",
            "Content-Type": "application/json",
        }
        expected_data = {"wa_id": wa_id}

        mock_response = mock_requests_post.return_value
        mock_response.status_code = 200

        start_turn_journey(wa_id, journey_id, engage_url, engage_token)

        mock_requests_post.assert_called_once_with(
            expected_url, headers=expected_headers, json=expected_data
        )
        self.assertEqual(mock_response.status_code, 200)
