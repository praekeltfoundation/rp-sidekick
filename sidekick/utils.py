import requests
from django.utils import timezone
from six.moves import urllib_parse
from temba_client.v2 import TembaClient
import pkg_resources


def get_today():
    return timezone.now().date()


def get_current_week_number():
    return int(get_today().strftime("%W"))


def clean_message(message):
    return " ".join(message.replace("\n", " ").replace("\t", " ").split())


def get_whatsapp_contact(org, msisdn):
    """
    Returns the WhatsApp ID for the given MSISDN
    """
    distribution = pkg_resources.get_distribution("rp-sidekick")

    response = requests.post(
        urllib_parse.urljoin(org.engage_url, "/v1/contacts"),
        json={"blocking": "wait", "contacts": [msisdn]},
        headers={
            "Authorization": "Bearer %s" % (org.engage_token,),
            "User-Agent": "rp-sidekick/{}".format(distribution.version),
        },
    )
    response.raise_for_status()
    whatsapp_id = response.json()["contacts"][0].get("wa_id")

    return whatsapp_id


def update_rapidpro_whatsapp_urn(org, msisdn):
    """
    Creates or updates a rapidpro contact with the whatsapp URN from the contact
    check
    """
    client = TembaClient(org.url, org.token)

    whatsapp_id = get_whatsapp_contact(org, msisdn)

    if whatsapp_id:
        contact = client.get_contacts(urn="tel:{}".format(msisdn)).first()

        urns = ["tel:{}".format(msisdn), "whatsapp:{}".format(whatsapp_id)]

        if contact:
            if urns != contact.urns:
                client.update_contact(contact=contact.uuid, urns=urns)
        else:
            client.create_contact(urns=urns)
