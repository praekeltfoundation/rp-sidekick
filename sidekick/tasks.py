from celery.exceptions import SoftTimeLimitExceeded
from requests import RequestException

from config.celery import app
from sidekick.models import Organization
from sidekick.utils import (
    get_whatsapp_contact_messages,
    label_whatsapp_message,
    start_flow,
)


@app.task(
    autoretry_for=(RequestException, SoftTimeLimitExceeded),
    retry_backoff=True,
    max_retries=15,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
    ignore_result=True,
)
def start_flow_task(org_id, user_uuid, flow_uuid):
    org = Organization.objects.get(id=org_id)
    start_flow(org, user_uuid, flow_uuid)


@app.task(
    autoretry_for=(RequestException, SoftTimeLimitExceeded),
    retry_backoff=True,
    max_retries=15,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
    ignore_result=True,
)
def add_label_to_turn_conversation(org_id, wa_id, labels):
    org = Organization.objects.get(id=org_id)

    result = get_whatsapp_contact_messages(org, wa_id)
    inbounds = filter(
        lambda m: m.get("_vnd", {}).get("v1", {}).get("direction") == "inbound",
        result.get("messages", []),
    )
    last_inbound = max(inbounds, key=lambda m: m.get("timestamp"))

    label_whatsapp_message(org, last_inbound["id"], labels)
