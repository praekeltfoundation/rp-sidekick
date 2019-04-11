import json
from os import environ

import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, reverse
from django.views.generic import TemplateView, View
from requests.exceptions import RequestException
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import OrgForm, WhatsAppTemplateForm, language_codes
from .models import Consent, Organization
from .serializers import RapidProFlowWebhookSerializer
from .tasks import start_flow_task
from .utils import (
    clean_message,
    get_whatsapp_contacts,
    send_whatsapp_template_message,
    submit_whatsapp_template_message,
)


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
                "{}{}".format(settings.RABBITMQ_MANAGEMENT_INTERFACE, queue.name)
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
        from pprint import pprint

        pprint(data)

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
                {"error": "Organization not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(
                data={
                    "error": "Authenticated user does not belong to specified Organization"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        result = send_whatsapp_template_message(
            org, wa_id, namespace, element_name, localizable_params
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
                {"error": "Organization not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(
                data={
                    "error": "Authenticated user does not belong to specified Organization"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        turn_response = get_whatsapp_contacts(org, [msisdn])
        if not (200 <= turn_response.status_code and turn_response.status_code < 300):
            return JsonResponse(
                {"error": turn_response.content.decode("utf-8")},
                status=turn_response.status_code,
            )

        return JsonResponse(
            json.loads(turn_response.content)["contacts"][0], status=status.HTTP_200_OK
        )


class GetConsentURLView(GenericAPIView):
    queryset = Consent.objects.all()
    permission_classes = (DjangoModelPermissions,)
    serializer_class = RapidProFlowWebhookSerializer

    def post(self, request, pk):
        """
        Returns the URL that the user can visit to give their consent
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        consent = self.get_object()
        contact_uuid = serializer.validated_data["contact"]["uuid"]
        return JsonResponse({"url": consent.generate_url(request, contact_uuid)})


class ConsentRedirectView(TemplateView):
    """
    This is a view to redirect the user to the actual consent page. This is done using
    a meta refresh tag, so that only when the user visits using a browser does it count
    as consent. This is to avoid the request from WhatsApp to get the media-embed tags
    counting as an opt-in.
    """

    template_name = "sidekick/consent.html"

    def get(self, request, code):
        try:
            consent, _ = Consent.from_code(code)
        except (ValueError, Consent.DoesNotExist):
            return HttpResponse("invalid code", status=status.HTTP_400_BAD_REQUEST)
        return super().get(request, code=code, consent=consent)

    def get_context_data(self, code, consent, **kwargs):
        context = super().get_context_data(**kwargs)
        context["url"] = reverse("provide-consent", args=[code])
        context["consent"] = consent
        return context


class ProvideConsentView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, code):
        """
        The user visiting the URL counts as consent. We should run the configured flow
        and redirect the user to the configured URL.
        """
        try:
            consent, contact_uuid = Consent.from_code(code)
        except (ValueError, Consent.DoesNotExist):
            return Response("invalid code", status=status.HTTP_400_BAD_REQUEST)

        if consent.flow_id:
            start_flow_task.delay(
                consent.org_id, str(contact_uuid), str(consent.flow_id)
            )
        if consent.redirect_url:
            return redirect(consent.redirect_url)

        return Response()


class TemplateCreationView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(
            request,
            "sidekick/create_templates.html",
            {"form": WhatsAppTemplateForm(user=request.user)},
        )

    def post(self, request, *args, **kwargs):
        # check the user from the request is legitimate
        form = WhatsAppTemplateForm(request.POST)

        # print(form.non_field_errors())

        if form.is_valid():
            # add the necessary items to the request
            # send the request
            response = submit_whatsapp_template_message(**form.cleaned_data)
            try:
                response.raise_for_status()
            except RequestException as e:
                if "errors" in response.json():
                    [form.add_error(None, error) for error in response.json()["errors"]]
                else:
                    form.add_error(None, "error: {}".format(e))
                return render(request, "sidekick/create_templates.html", {"form": form})
            # redirect them to list of templates if successful
            return redirect(reverse("view_template"))
        return render(request, "sidekick/create_templates.html", {"form": form})


class TemplateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(
            request, "sidekick/get_templates.html", {"form": OrgForm(user=request.user)}
        )

    def post(self, request, *args, **kwargs):
        form = OrgForm(request.POST)
        if form.is_valid():
            org = form.cleaned_data["org"]

            # might want to move this to a form field thing
            if not org.users.filter(id=request.user.id).exists():
                return HttpResponse(
                    "Unauthorized: user does not belong to organization", status=401
                )

            url = "https://whatsapp.praekelt.org/v1/message_templates"
            headers = {
                "Authorization": "Bearer {}".format(org.engage_token),
                "Accept": "application/vnd.v1+json",
            }
            response = requests.request("GET", url, headers=headers)
            response.raise_for_status()

            data = response.json()["data"]

            updated_data = [
                {
                    **blob,
                    # display only message body, this will change in the future
                    "content": blob["components"][0]["text"],
                    # replace language code with language string
                    "language": language_codes[blob["language"]],
                }
                for blob in data
            ]

            return render(
                request,
                "sidekick/get_templates.html",
                {"data": updated_data, "form": form},
            )
        return render(request, "sidekick/get_templates.html", {"form": form})
