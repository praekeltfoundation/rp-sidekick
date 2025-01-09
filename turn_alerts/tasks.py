from urllib.parse import urljoin

import requests
from celery.exceptions import SoftTimeLimitExceeded
from requests.exceptions import RequestException
from temba_client.exceptions import TembaHttpError

from config.celery import app

from .models import TurnAlerts


@app.task(
    autoretry_for=(RequestException, SoftTimeLimitExceeded, TembaHttpError),
    retry_backoff=True,
    max_retries=15,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
)
def start_turn_journey(wa_id):

    turn_alerts = TurnAlerts.objects.get(pk=1)
    organization = turn_alerts.org

    headers = {
        "Authorization": f"Bearer {turn_alerts.hmac_secret}",
        "Content-Type": "application/json",
    }
    data = {"wa_id": wa_id}
    journey_id = turn_alerts.journey_id  # Assuming journey_id is a field on TurnAlerts

    url = urljoin(organization.url, f"/v1/stacks/{journey_id}/start")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
