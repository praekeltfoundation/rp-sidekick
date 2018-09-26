import requests
import json
from os import environ
from urllib.parse import urljoin
from django.http import JsonResponse
from rest_framework import status

from .models import Organization


def health(request):
    app_id = environ.get("MARATHON_APP_ID", None)
    ver = environ.get("MARATHON_APP_VERSION", None)
    return JsonResponse({"id": app_id, "version": ver})


def send_wa_template_message(request):
    data = request.GET.dict()

    required_params = [
        "org_id",
        "wa_id",
        "namespace",
        "element_name",
        "message",
    ]
    for field in required_params:
        if field not in data:
            return JsonResponse(
                {
                    "error": "Required fields: {}".format(
                        ", ".join(required_params)
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    org_id = data["org_id"]
    wa_id = data["wa_id"]
    namespace = data["namespace"]
    element_name = data["element_name"]
    message = data["message"]

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
        data={
            "to": wa_id,
            "type": "hsm",
            "hsm": {
                "namespace": namespace,
                "element_name": element_name,
                "language": {"policy": "fallback", "code": "en_US"},
                "localizable_params": [{"default": message}],
            },
        },
    )

    return JsonResponse(json.loads(result.content), status=result.status_code)
