import requests
import json
from os import environ
from urllib.parse import urljoin
from django.http import JsonResponse

from rest_framework import status
from rest_framework.views import APIView

from .models import Organization
from .utils import clean_message


def health(request):
    app_id = environ.get("MARATHON_APP_ID", None)
    ver = environ.get("MARATHON_APP_VERSION", None)
    return JsonResponse({"id": app_id, "version": ver})


def send_wa_template_message(request):
    data = request.GET.dict()

    required_params = ["org_id", "wa_id", "namespace", "element_name"]

    missing_params = [key for key in required_params if key not in data]
    if missing_params:
        return JsonResponse(
            {"error": "Missing fields: {}".format(", ".join(missing_params))},
            status=status.HTTP_400_BAD_REQUEST,
        )

    localizable_params = [
        {"default": clean_message(data[_key])}
        for _key in sorted([key for key in data.keys() if key.isdigit()])
    ]

    org_id = data["org_id"]
    wa_id = data["wa_id"]
    namespace = data["namespace"]
    element_name = data["element_name"]

    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return JsonResponse(
            {"error": "Organization not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    headers = {
        "Authorization": "Bearer {}".format(org.engage_token),
        "Content-Type": "application/json",
    }

    result = requests.post(
        urljoin(org.engage_url, "v1/messages"),
        headers=headers,
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

    return JsonResponse(json.loads(result.content), status=result.status_code)


class CheckContactView(APIView):
    """
    Accepts Org id and msisdn
    Checks the Turn API to see if the contact is valid
    Returns a JsonResponse containing status as valid/invalid
    """

    def get(self, request, org_id, msisdn, *args, **kwargs):
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return JsonResponse(
                {"error": "Organization not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        headers = {
            "Authorization": "Bearer {}".format(org.engage_token),
            "Content-Type": "application/json",
        }

        result = requests.post(
            urljoin(org.engage_url, "v1/contacts"),
            headers=headers,
            data=json.dumps({"blocking": "wait", "contacts": [msisdn]}),
        )
        if not (200 <= result.status_code and result.status_code < 300):
            return JsonResponse(
                {"error": result.content.decode("utf-8")},
                status=result.status_code,
            )

        return JsonResponse(
            json.loads(result.content)["contacts"][0], status=status.HTTP_200_OK
        )
