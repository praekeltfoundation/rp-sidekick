from celery.exceptions import SoftTimeLimitExceeded
from django.conf import settings
from requests import RequestException
from temba_client.exceptions import TembaHttpError

from config.celery import app
from sidekick.models import Organization
from sidekick.utils import (
    archive_whatsapp_conversation,
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


@app.task(
    autoretry_for=(RequestException, SoftTimeLimitExceeded),
    retry_backoff=True,
    max_retries=15,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
    ignore_result=True,
)
def archive_turn_conversation(org_id, wa_id, reason):
    org = Organization.objects.get(id=org_id)

    result = get_whatsapp_contact_messages(org, wa_id)
    inbounds = filter(
        lambda m: m.get("_vnd", {}).get("v1", {}).get("direction") == "inbound",
        result["messages"],
    )
    last_inbound_message = max(inbounds, key=lambda m: m.get("timestamp"))

    archive_whatsapp_conversation(org, wa_id, last_inbound_message["id"], reason)


@app.task(
    autoretry_for=(RequestException, SoftTimeLimitExceeded, TembaHttpError),
    retry_backoff=True,
    max_retries=15,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
)
def check_rapidpro_group_membership_count():
    if settings.RAPIDPRO_MONITOR_GROUP:
        group_name = settings.RAPIDPRO_MONITOR_GROUP
        for org in Organization.objects.all():
            client = org.get_rapidpro_client()
            group = client.get_groups(name=group_name).first()
            if group and group.count <= 0:
                raise Exception(f"Org: {org.name} - {group_name} group is empty")
