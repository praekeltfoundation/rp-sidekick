import os

import boto3
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
    urns = ["tel:{}".format(msisdn)]

    whatsapp_id = get_whatsapp_contact_id(org, msisdn)
    if whatsapp_id:
        urns.append("whatsapp:{}".format(whatsapp_id))
        patient_info["has_whatsapp"] = True
    else:
        patient_info["has_whatsapp"] = False

    contact = client.get_contacts(urn="tel:{}".format(msisdn)).first()
    if whatsapp_id and not contact:
        contact = client.get_contacts(urn="whatsapp:{}".format(whatsapp_id)).first()

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


@app.task(soft_time_limit=10, time_limit=15)
def pull_new_import_file(upload_dir, org_name):
    """
    Task to check if there are any new .xlsx files in the S3 bucket and create
    an import object for them.
    """
    org = Organization.objects.get(name=org_name)
    imported_files = ContactImport.objects.all().values_list("file", flat=True)
    bucket = settings.AWS_STORAGE_BUCKET_NAME

    s3 = boto3.client("s3")

    for obj in s3.list_objects(Bucket=bucket, Prefix=upload_dir)["Contents"]:
        if obj["Key"] == upload_dir or ".xlsx" not in obj["Key"]:
            continue
        matching_name = obj["Key"].replace(
            upload_dir, os.path.join(settings.MEDIA_ROOT, "uploads/gpconnect/")
        )
        if matching_name not in imported_files:
            with open(
                os.path.join(settings.MEDIA_ROOT, matching_name), "wb"
            ) as new_file:
                s3.download_fileobj(bucket, obj["Key"], new_file)

            new_import = ContactImport(org=org)
            new_import.file.name = matching_name
            new_import.save()
            # Call the task syncronously so that we're using the same file system
            process_contact_import(new_import.pk)
            break
