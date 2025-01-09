from unittest.mock import patch
from urllib.parse import urljoin

from django.test import override_settings
from rest_framework.test import APITestCase

from sidekick.tests.utils import create_org
from turn_alerts.models import TurnAlerts
from turn_alerts.tasks import start_turn_journey


class StartTurnJourneyAPITestCase(APITestCase):

    def setUp(self):
        self.org = create_org()

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch("requests.post")
    def test_start_turn_journey_success(self, mock_post):
        turn_alerts = TurnAlerts.objects.create(
            hmac_secret="test_secret", org=self.org, journey_id="turn_journey_id"
        )
        wa_id = "1234567890"
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}

        response = start_turn_journey(wa_id)

        self.assertEqual(response, {"success": True})
        mock_post.assert_called_once_with(
            urljoin(self.org.url, f"/v1/stacks/{turn_alerts.journey_id}/start"),
            headers={
                "Authorization": f"Bearer {turn_alerts.hmac_secret}",
                "Content-Type": "application/json",
            },
            json={"wa_id": wa_id},
        )
