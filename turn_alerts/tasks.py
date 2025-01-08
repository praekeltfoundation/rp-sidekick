import requests
from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
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
def start_turn_journey(wa_id):
    """
    Starts the contact in a turn journey using the Turn API.
    """
    headers = {
        "Authorization": "Bearer {}".format(settings.TURN_ALERTS_JOURNEY_TOKEN),
        "Content-Type": "application/json",
    }

    data = {"wa_id": wa_id}

    response = requests.post(
        settings.TURN_ALERTS_JOURNEY_URL, headers=headers, json=data
    )
    response.raise_for_status()
    return response.json()
