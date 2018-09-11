import requests
import json
from os import environ
from urllib.parse import urljoin
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse

from rest_framework import status
from rest_framework.views import APIView

from django.http import JsonResponse, HttpResponse
from django.views import View
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Organization
from .utils import clean_message, get_whatsapp_contacts
from .auth_utils import get_authorization_url, save_credentials, get_flow


def health(request):
    app_id = environ.get("MARATHON_APP_ID", None)
    ver = environ.get("MARATHON_APP_VERSION", None)
    return JsonResponse({"id": app_id, "version": ver})


def detailed_health(request):
    queues = []
    stuck = False

    if settings.RABBITMQ_MANAGEMENT_INTERFACE:
        message = "queues ok"
        for queue in settings.CELERY_QUEUES:
            queue_results = requests.get(
                "{}{}".format(
                    settings.RABBITMQ_MANAGEMENT_INTERFACE, queue.name
                )
            ).json()

            details = {
                "name": queue_results["name"],
                "stuck": False,
                "messages": queue_results.get("messages"),
                "rate": queue_results["messages_details"]["rate"],
            }
            if details["messages"] > 0 and details["rate"] == 0:
                stuck = True
                details["stuck"] = True

            queues.append(details)
    else:
        message = "queues not checked"

    status_code = status.HTTP_200_OK
    if stuck:
        message = "queues stuck"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    db_available = True
    try:
        connections["default"].cursor()
    except OperationalError:
        db_available = False
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JsonResponse(
        {"update": message, "queues": queues, "db_available": db_available},
        status=status_code,
    )


class SendWhatsAppTemplateMessageView(APIView):
    def get(self, request, *args, **kwargs):
        data = request.GET.dict()

        required_params = ["org_id", "wa_id", "namespace", "element_name"]

        missing_params = [key for key in required_params if key not in data]
        if missing_params:
            return JsonResponse(
                {
                    "error": "Missing fields: {}".format(
                        ", ".join(missing_params)
                    )
                },
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

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(
                data={
                    "error": "Authenticated user does not belong to specified Organization"
                },
                status=status.HTTP_401_UNAUTHORIZED,
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

        return JsonResponse(
            json.loads(result.content), status=result.status_code
        )


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
        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(
                data={
                    "error": "Authenticated user does not belong to specified Organization"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        turn_response = get_whatsapp_contacts(org, [msisdn])
        if not (
            200 <= turn_response.status_code and turn_response.status_code < 300
        ):
            return JsonResponse(
                {"error": turn_response.content.decode("utf-8")},
                status=turn_response.status_code,
            )

        return JsonResponse(
            json.loads(turn_response.content)["contacts"][0],
            status=status.HTTP_200_OK,
        )


class GoogleAuthorizeView(LoginRequiredMixin, View):
    def get(self, request):
        redirect_url = None
        if "next" in request.GET and "scope" in request.GET:
            redirect_url = request.GET["next"]
            request.session["google_auth_redirect"] = redirect_url

            scopes = request.GET.getlist("scope")
            request.session["scopes"] = scopes
        else:
            HttpResponse(
                "Configuration Error: please pass in a 'next' and 'scope' query params"
            )

        authorization_url, state = get_authorization_url(request, scopes=scopes)
        request.session["state"] = state
        return redirect(to=authorization_url)


class OAuth2Callback(LoginRequiredMixin, View):
    def get(self, request):
        if "scopes" in request.session and request.session["scopes"] != []:
            flow = get_flow(
                request,
                scopes=request.session["scopes"],
                state=request.session["state"],
            )
            del request.session["scopes"]
        else:
            return HttpResponse(
                "You have not declared a scope for authentication"
            )

        # Note: to test this locally, set OAUTHLIB_INSECURE_TRANSPORT=1 in your .env file
        flow.fetch_token(authorization_response=request.get_raw_uri())

        save_credentials(user=request.user, credentials=flow.credentials)
        if "google_auth_redirect" in request.session:
            url = request.session["google_auth_redirect"]
            del request.session["google_auth_redirect"]
            return redirect(to=url)
        return redirect(to="/health/")
