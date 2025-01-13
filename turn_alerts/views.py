import re

from django.http import JsonResponse
from prometheus_client import Counter
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from sidekick.models import Organization
from turn_alerts.serializers import (
    ContactsPayloadSerializer,
    Status_ErrorPayloadSerializer,
    StatusPayloadSerializer,
    VendorPayloadSerializer,
)

from .models import TurnActions
from .tasks import start_turn_journey

message_requests_total = Counter(
    "turn_alerts_message_requests_total",
    "Total number of message requests",
    [
        "fallback_channel",
        "direction",
        "message_type",
    ],
)


event_count = Counter(
    "turn_alerts_event_count",
    "Number of events",
    ["message_status", "error_code", "conversation_id", "conversation_type"],
)


class TurnAlertsLayerView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        org_id = kwargs["org_id"]
        try:
            organization = Organization.objects.get(id=org_id)
            turn_alerts = TurnActions.objects.filter(org=organization)
        except Organization.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

        body = request.data
        request_type = list(body.keys())[0]

        org_id = kwargs["org_id"]

        for alert in turn_alerts:
            journey_id = alert.journey_id
            org_error_code = alert.error_code
            engage_token = organization.engage_token
            engage_url = organization.engage_url

        if request_type in ["contacts", "_vnd"]:
            if request_type == "contacts":
                serializer = ContactsPayloadSerializer(data=body)
            else:
                serializer = VendorPayloadSerializer(data=body)
            serializer.is_valid(raise_exception=True)
            message_requests_total.labels(
                fallback_channel=serializer.get_fallback_channel(),
                direction=serializer.get_direction(),
                message_type=serializer.get_message_type(),
            ).inc()

        else:
            if body["statuses"][0]["status"].upper() == "FAILED":
                serializer = Status_ErrorPayloadSerializer(data=body)
                serializer.is_valid(raise_exception=True)
                error_code = serializer.get_error_code()
                message_status = serializer.get_message_status()
                whatsappid = serializer.get_recipient_id()
                event_count.labels(
                    message_status=message_status,
                    error_code=error_code,
                    conversation_id=None,
                    conversation_type=None,
                ).inc()
                if error_code == org_error_code:
                    match = re.match(
                        (
                            r"^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]"
                            r"*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$"
                        ),
                        whatsappid,
                    )
                    if match:
                        start_turn_journey(
                            whatsappid, journey_id, engage_url, engage_token
                        )
            else:
                serializer = StatusPayloadSerializer(data=body)
                serializer.is_valid(raise_exception=True)
                whatsappid = serializer.get_recipient_id()
                conversation_type = serializer.get_conversation_type()
                message_status = serializer.get_message_status()
                conversation_id = serializer.get_conversation_id()
                event_count.labels(
                    message_status=message_status,
                    error_code=None,
                    conversation_id=conversation_id,
                    conversation_type=conversation_type,
                ).inc()

        return Response({}, status=status.HTTP_200_OK)
