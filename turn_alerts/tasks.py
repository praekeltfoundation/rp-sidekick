from urllib.parse import urljoin

import requests
from celery.exceptions import SoftTimeLimitExceeded
from requests.exceptions import RequestException
from temba_client.exceptions import TembaHttpError

from config.celery import app


@app.task(
    autoretry_for=(RequestException, SoftTimeLimitExceeded, TembaHttpError),
    retry_backoff=True,
    max_retries=15,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
)
def start_turn_journey(wa_id, journey_id, engage_url, engage_token):

    headers = {
        "Authorization": f"Bearer {engage_token}",
        "Content-Type": "application/json",
    }
    data = {"wa_id": wa_id}

    url = urljoin(engage_url, f"/v1/stacks/{journey_id}/start")
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
