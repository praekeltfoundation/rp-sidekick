from unittest.mock import patch

from django.test import TestCase as DjangoTestCase
from django.test import override_settings

from turn_alerts.tasks import start_turn_journey


class TestStartTurnJourney(DjangoTestCase):
    @override_settings(
        TURN_ALERTS_JOURNEY_URL="turn-journey-url",
        TURN_ALERTS_JOURNEY_TOKEN="token",
    )
    @patch("requests.post")
    def test_start_turn_journey_calls_requests_post(self, mock_requests_post):

        expected_url = "turn-journey-url"
        expected_headers = {
            "Authorization": "Bearer token",
            "Content-Type": "application/json",
        }
        expected_data = {"wa_id": "TEST_WA_ID"}

        start_turn_journey("TEST_WA_ID")

        mock_requests_post.assert_called_once_with(
            expected_url, headers=expected_headers, json=expected_data
        )
