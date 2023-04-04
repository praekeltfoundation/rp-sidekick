import requests
from celery.exceptions import SoftTimeLimitExceeded
from requests.exceptions import RequestException

from config.celery import app


@app.task(
    autoretry_for=(RequestException, SoftTimeLimitExceeded),
    ignore_result=True,
    retry_backoff=True,
    max_retries=10,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
)
def http_request(method, url, headers, body):
    response = requests.request(
        method=method, url=url, headers=headers, data=body.encode()
    )
    response.raise_for_status()
