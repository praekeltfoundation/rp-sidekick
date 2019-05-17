import json
from urllib.parse import urljoin

import pkg_resources
import requests
from django.utils import timezone
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from rest_framework import status
from six.moves import urllib_parse
from temba_client.v2 import TembaClient

from .models import Organization


def get_today():
    return timezone.now().date()


def get_current_week_number():
    return int(get_today().strftime("%W"))


def clean_message(message):
    return " ".join(message.replace("\n", " ").replace("\t", " ").split())


def clean_msisdn(msisdn):
    """
    returns a number without preceeding '+' if it has one
    """
    return msisdn.replace("+", "")


def build_turn_headers(token):
    distribution = pkg_resources.get_distribution("rp-sidekick")
    return {
        "Authorization": "Bearer {}".format(token),
        "User-Agent": "rp-sidekick/{}".format(distribution.version),
        "Content-Type": "application/json",
    }


def send_whatsapp_template_message(
    org, wa_id, namespace, element_name, localizable_params
):
    return requests.post(
        urljoin(org.engage_url, "v1/messages"),
        headers=build_turn_headers(org.engage_token),
        data=json.dumps(
            {
                "to": wa_id,
                "type": "hsm",
                "hsm": {
                    "namespace": namespace,
                    "element_name": element_name,
                    "language": {"policy": "fallback", "code": "en_US"},
                    "localizable_params": localizable_params,
                },
            }
        ),
    )


def send_whatsapp_group_message(org, group_id, message):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1)
    session.mount("https://", HTTPAdapter(max_retries=retries))

    response = session.post(
        urljoin(org.engage_url, "v1/messages"),
        headers=build_turn_headers(org.engage_token),
        data=json.dumps(
            {
                "recipient_type": "group",
                "to": group_id,
                "render_mentions": False,
                "type": "text",
                "text": {"body": message},
            }
        ),
    )
    response.raise_for_status()
    return response


def get_whatsapp_contact_id(org, msisdn):
    """
    Returns the WhatsApp ID for the given MSISDN
    """
    turn_response = get_whatsapp_contacts(org, [msisdn])
    turn_response.raise_for_status()
    return turn_response.json()["contacts"][0].get("wa_id")


def get_whatsapp_contacts(org, msisdns):
    """
    Returns the Turn response for a given list of MSISDNs
    """
    return requests.post(
        urllib_parse.urljoin(org.engage_url, "/v1/contacts"),
        json={"blocking": "wait", "contacts": msisdns},
        headers=build_turn_headers(org.engage_token),
    )


def update_rapidpro_whatsapp_urn(org, msisdn):
    """
    Creates or updates a rapidpro contact with the whatsapp URN from the contact
    check
    """
    client = TembaClient(org.url, org.token)

    whatsapp_id = get_whatsapp_contact_id(org, msisdn)

    if whatsapp_id:
        contact = client.get_contacts(urn="tel:{}".format(msisdn)).first()
        if not contact:
            contact = client.get_contacts(urn="whatsapp:{}".format(whatsapp_id)).first()

        urns = ["tel:{}".format(msisdn), "whatsapp:{}".format(whatsapp_id)]

        if contact:
            if urns != contact.urns:
                client.update_contact(contact=contact.uuid, urns=urns)
        else:
            client.create_contact(urns=urns)


def create_whatsapp_group(org, subject):
    """
    Creates a Whatsapp group using the subject
    """
    result = requests.post(
        urljoin(org.engage_url, "v1/groups"),
        headers=build_turn_headers(org.engage_token),
        data=json.dumps({"subject": subject}),
    )

    return json.loads(result.content)["groups"][0]["id"]


def get_whatsapp_group_invite_link(org, group_id):
    """
    Gets the invite link for a Whatsapp group with the group ID
    """
    response = requests.get(
        urljoin(org.engage_url, "v1/groups/{}/invite".format(group_id)),
        headers=build_turn_headers(org.engage_token),
    )
    return json.loads(response.content)["groups"][0]["link"]


def get_whatsapp_group_info(org, group_id):
    """
    Gets info for a Whatsapp group with the group ID
    """
    result = requests.get(
        urljoin(org.engage_url, "v1/groups/{}".format(group_id)),
        headers=build_turn_headers(org.engage_token),
    )

    return json.loads(result.content)["groups"][0]


def add_whatsapp_group_admin(org, group_id, wa_id):
    """
    Adds a existing Whatsapp group member to the list of admins on the group
    """
    return requests.patch(
        urljoin(org.engage_url, "v1/groups/{}/admins".format(group_id)),
        headers=build_turn_headers(org.engage_token),
        data=json.dumps({"wa_ids": [wa_id]}),
    )


def get_flow_url(org, flow_uuid):
    return urljoin(urljoin(org.url, "/flow/editor/"), flow_uuid)


def validate_organization(org_id, request):
    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return status.HTTP_400_BAD_REQUEST

    if not org.users.filter(id=request.user.id).exists():
        return status.HTTP_401_UNAUTHORIZED

    return status.HTTP_202_ACCEPTED
