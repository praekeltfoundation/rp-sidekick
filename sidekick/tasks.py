from celery.exceptions import SoftTimeLimitExceeded
from requests import RequestException

from config.celery import app
from sidekick.models import Organization
from sidekick.utils import start_flow


@app.task(
    autoretry_for=(RequestException, SoftTimeLimitExceeded),
    retry_backoff=True,
    max_retries=15,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
)
def start_flow_task(org_id, user_uuid, flow_uuid):
    org = Organization.objects.get(id=org_id)
    start_flow(org, user_uuid, flow_uuid)
