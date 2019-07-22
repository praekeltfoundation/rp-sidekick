import os

from celery.task import Task
from celery.utils.log import get_task_logger
from django.conf import settings
from openpyxl import load_workbook
from temba_client.v2 import TembaClient

from sidekick.utils import get_whatsapp_contact_id

from .models import ContactImport

log = get_task_logger(__name__)


class ProcessContactImport(Task):
    name = "rp_gpconnect.tasks.process_contact_import"

    def run(self, contact_import_id, **kwargs):
        # org = Organization.objects.get(id=org_id)
        contact_import = ContactImport.objects.get(id=contact_import_id)
        log.info("Importing contacts for file: %s" % contact_import.file.name)

        wb = load_workbook(
            filename=os.path.join(settings.MEDIA_ROOT, contact_import.file.name),
            data_only=True,
        )
        sheet = wb["GP Connect daily report"]
        max_row = sheet.max_row
        max_column = sheet.max_column

        headers = []
        for y in range(max_column):
            headers.append(sheet.cell(row=1, column=y + 1).value)
        msisdn_index = headers.index("msisdn") + 1

        org = contact_import.org

        client = TembaClient(org.url, org.token)
        for x in range(1, max_row):
            # TODO: Get indicator fields
            msisdn = sheet.cell(row=x + 1, column=msisdn_index).value

            whatsapp_id = get_whatsapp_contact_id(org, msisdn)
            if not whatsapp_id:
                log.info("Skipping contact {}. No WhatsApp Id.".format(msisdn))
                continue

            contact = client.get_contacts(urn="tel:{}".format(msisdn)).first()
            if not contact:
                contact = client.get_contacts(
                    urn="whatsapp:{}".format(whatsapp_id)
                ).first()

            urns = ["tel:{}".format(msisdn), "whatsapp:{}".format(whatsapp_id)]

            if contact:
                if urns != contact.urns:
                    contact = client.update_contact(contact=contact.uuid, urns=urns)
            else:
                contact = client.create_contact(urns=urns)


process_contact_import = ProcessContactImport()
