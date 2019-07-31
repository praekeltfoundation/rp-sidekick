import os

from celery.exceptions import SoftTimeLimitExceeded
from celery.utils.log import get_task_logger
from django.conf import settings
from openpyxl import load_workbook
from requests.exceptions import ConnectionError, HTTPError, Timeout
from temba_client.v2 import TembaClient

from config.celery import app
from sidekick.models import Organization
from sidekick.utils import get_whatsapp_contact_id

from .models import ContactImport

log = get_task_logger(__name__)


@app.task(
    autoretry_for=Timeout,
    retry_backoff=True,
    retry_jitter=True,
    max_retries=10,
    acks_late=True,
)
def process_contact_import(contact_import_id):
    contact_import = ContactImport.objects.get(id=contact_import_id)
    log.info("Importing contacts for file: %s" % contact_import.file.name)

    wb = load_workbook(
        filename=os.path.join(settings.MEDIA_ROOT, contact_import.file.name),
        data_only=True,
    )
    sheet = wb["GP Connect daily report"]

    # Get the headers
    headers = []
    for cell in sheet[1]:
        headers.append(cell.value)

    current_row = 0
    for row in sheet.values:
        # Skip header row
        if current_row == 0:
            current_row += 1
            continue

        row_dict = dict(zip(headers, row))
        if row_dict["patients_tested_positive"] == 1:
            import_or_update_contact.delay(row_dict, contact_import.org.id)


@app.task(
    autoretry_for=(HTTPError, ConnectionError, Timeout, SoftTimeLimitExceeded),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=10,
    acks_late=True,
    soft_time_limit=10,
    time_limit=15,
)
def import_or_update_contact(patient_info, org_id):
    org = Organization.objects.get(id=org_id)
    client = TembaClient(org.url, org.token)

    msisdn = patient_info.pop("msisdn")
    whatsapp_id = get_whatsapp_contact_id(org, msisdn)
    if not whatsapp_id:
        log.info("Skipping contact {}. No WhatsApp Id.".format(msisdn))
        return

    contact = client.get_contacts(urn="tel:{}".format(msisdn)).first()
    if not contact:
        contact = client.get_contacts(urn="whatsapp:{}".format(whatsapp_id)).first()

    urns = ["tel:{}".format(msisdn), "whatsapp:{}".format(whatsapp_id)]

    if contact:
        if urns != contact.urns:
            contact = client.update_contact(contact=contact.uuid, urns=urns)
        if contact.fields != patient_info:
            client.create_flow_start(
                flow=org.flows.get(type="contact_update").rapidpro_flow,
                urns=urns,
                restart_participants=True,
                extra=patient_info,
            )
    else:
        contact = client.create_contact(urns=urns)
        client.create_flow_start(
            flow=org.flows.get(type="new_contact").rapidpro_flow,
            urns=urns,
            restart_participants=True,
            extra=patient_info,
        )
