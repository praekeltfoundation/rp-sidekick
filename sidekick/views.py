import json
from os import environ
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, reverse
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.views import APIView
from temba_client.exceptions import TembaConnectionError, TembaRateExceededError

from .models import Consent, Organization
from .serializers import (
    URN_REGEX,
    ArchiveTurnConversationSerializer,
    LabelTurnConversationSerializer,
    RapidProFlowWebhookSerializer,
)
from .tasks import (
    add_label_to_turn_conversation,
    archive_turn_conversation,
    start_flow_task,
)
from .utils import clean_message, get_whatsapp_contacts, send_whatsapp_template_message


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
                f"{settings.RABBITMQ_MANAGEMENT_INTERFACE}{queue.name}"
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
                    "error": "Authenticated user does not belong to specified "
                    "Organization"
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


class LabelTurnCoversationPermission(DjangoModelPermissions):
    """
    Allows POST requests if the user has the label_turn_conversation permission
    """

    perms_map = {"POST": ["%(app_label)s.label_turn_conversation"]}


class LabelTurnConversationView(GenericAPIView):
    queryset = Organization.objects.all()
    permission_classes = (LabelTurnCoversationPermission,)
    serializer_class = RapidProFlowWebhookSerializer

    def post(self, request, pk):
        self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match = URN_REGEX.match(serializer.validated_data["contact"]["urn"])
        address = match.group("address").lstrip("+")

        qs_serializer = LabelTurnConversationSerializer(data=request.query_params)
        qs_serializer.is_valid(raise_exception=True)
        labels = qs_serializer.validated_data["label"]

        task = add_label_to_turn_conversation.delay(pk, address, labels)
        return Response({"task_id": task.id}, status=status.HTTP_201_CREATED)


class ArchiveTurnCoversationPermission(DjangoModelPermissions):
    """
    Allows POST requests if the user has the archive_turn_conversation permission
    """

    perms_map = {"POST": ["%(app_label)s.archive_turn_conversation"]}


class ArchiveTurnConversationView(GenericAPIView):
    queryset = Organization.objects.all()
    permission_classes = (ArchiveTurnCoversationPermission,)
    serializer_class = RapidProFlowWebhookSerializer

    def post(self, request, pk):
        self.get_object()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match = URN_REGEX.match(serializer.validated_data["contact"]["urn"])
        address = match.group("address").lstrip("+")

        qs_serializer = ArchiveTurnConversationSerializer(data=request.query_params)
        qs_serializer.is_valid(raise_exception=True)
        reason = qs_serializer.validated_data["reason"]

        task = archive_turn_conversation.delay(pk, address, reason)
        return Response({"task_id": task.id}, status=status.HTTP_201_CREATED)


class ListContactsView(GenericAPIView):
    """
    Accepts Org id and multiple key, value query parameters to filter by
    Uses the query parameters to filter RapidPro contacts
    Returns a JsonResponse listing just the uuids of matching contacts
    Accepts fields handled by the RapidPro API as well as custom contact fields
    """

    queryset = Organization.objects.all()

    def get(self, request, pk, *args, **kwargs):
        org = self.get_object()
        rapidpro_api_fields = ["uuid", "urn", "group", "deleted", "before", "after"]

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(
                data={
                    "error": "Authenticated user does not belong to specified "
                    "Organization"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        filter_kwargs = {}
        fields = list(request.GET.keys())
        for field in fields:
            if field in rapidpro_api_fields:
                filter_kwargs.update({field: request.GET[field]})

        client = org.get_rapidpro_client()
        contact_batches = client.get_contacts(**filter_kwargs).iterfetches()

        uuids = []
        try:
            for contact_batch in contact_batches:
                for contact in contact_batch:
                    match = True
                    for field in fields:
                        value = request.GET[field]
                        if field in rapidpro_api_fields:
                            # get_contacts already filtered on this field
                            continue
                        elif (
                            field not in contact.fields.keys()
                            or str(contact.fields[field]) != value
                        ):
                            match = False
                            break
                    if match:
                        uuids.append(contact.uuid)
        except (TembaRateExceededError, TembaConnectionError):
            return JsonResponse(
                {
                    "error": "An error occured fulfilling your request. "
                    "You may have exceeded the rate limit. "
                    "Please try again later."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return JsonResponse({"contacts": uuids}, status=status.HTTP_200_OK)


class RapidproFlowsView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        user = get_user_model().objects.get(id=request.user.id)
        org = user.org_users.first()

        if not org:
            return JsonResponse(
                {"error": "Organization not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {org.token}",
        }
        response = requests.get(urljoin(org.url, "api/v2/flows.json"), headers=headers)

        return JsonResponse(response.json(), status=response.status_code)


class RapidproFlowStartView(GenericAPIView):
    def post(self, request):
        """
        Starts the specified flow
        """
        user = get_user_model().objects.get(id=request.user.id)
        org = user.org_users.first()

        if not org:
            return JsonResponse(
                {"error": "Organization not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {org.token}",
        }
        response = requests.post(
            urljoin(org.url, "api/v2/flow_starts.json"),
            json=request.data,
            headers=headers,
        )

        return JsonResponse(response.json(), status=response.status_code)


class RapidproContactView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        user = get_user_model().objects.get(id=request.user.id)
        org = user.org_users.first()

        if not org:
            return JsonResponse(
                {"error": "Organization not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {org.token}",
        }
        response = requests.get(
            urljoin(org.url, "api/v2/contacts.json"),
            params=request.GET,
            headers=headers,
        )

        contact_data = response.json()

        if org.filter_rapidpro_fields:
            filter_fields = org.filter_rapidpro_fields.split(",")
            for contact in contact_data.get("results", []):
                new_fields = {}
                for field, value in contact["fields"].items():
                    if field in filter_fields:
                        new_fields[field] = value
                contact["fields"] = new_fields

        return JsonResponse(contact_data, status=response.status_code)
