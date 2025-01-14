import re

from django.http import JsonResponse
from prometheus_client import Counter
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from sidekick.models import Organization
from turn_alerts.serializers import TurnOutboundSerializer, WhatsAppWebhookSerializer

from .models import TurnActions
from .tasks import start_turn_journey
from .utils import validate_signature

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
    [
        "message_status",
        "error_code",
        "conversation_id",
        "conversation_type",
        "on_fallback_channel",
    ],
)


class TurnAlertsLayerView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        validate_signature(request)
        try:
            webhook_type = request.headers["X-Turn-Hook-Subscription"]
        except KeyError:
            return Response(
                {"X-Turn-Hook-Subscription": ["This header is required."]},
                status.HTTP_400_BAD_REQUEST,
            )
        org_id = kwargs["org_id"]

        try:
            organization = Organization.objects.get(id=org_id)
            turn_alerts = TurnActions.objects.filter(org=organization)
        except Organization.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

        on_fallback_channel = request.headers.get("X-Turn-Fallback-Channel", "0") == "1"
        is_turn_event = request.headers.get("X-Turn-Event", "0") == "1"

        for alert in turn_alerts:
            journey_id = alert.journey_id
            org_error_code = alert.error_code
            engage_token = organization.engage_token
            engage_url = organization.engage_url

        if webhook_type == "whatsapp" or is_turn_event:
            WhatsAppWebhookSerializer(data=request.data).is_valid(raise_exception=True)
            for inbound in request.data.get("messages", []):

                message_type = inbound.pop("type")
                direction = inbound["_vnd"]["v1"]["direction"]
                message_requests_total.labels(
                    fallback_channel=on_fallback_channel,
                    direction=direction,
                    message_type=message_type,
                ).inc()
            for statuses in request.data.get("statuses", []):
                message_status = statuses.get("status")

                if "errors" in statuses:
                    recipient_id = statuses.get("recipient_id")
                    error_code = statuses["errors"][0].get("code")
                    event_count.labels(
                        message_status=message_status,
                        error_code=error_code,
                        conversation_id=None,
                        conversation_type=None,
                        on_fallback_channel=on_fallback_channel,
                    ).inc()
                    if error_code == org_error_code:
                        match = re.match(
                            (
                                r"^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]"
                                r"*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$"
                            ),
                            recipient_id,
                        )
                        if match:
                            start_turn_journey(
                                recipient_id, journey_id, engage_url, engage_token
                            )

                else:
                    conversation_id = statuses.get("conversation").get("id")
                    conversation_type = (
                        statuses.get("conversation").get("origin").get("type")
                    )
                    event_count.labels(
                        message_status=message_status,
                        error_code=None,
                        conversation_id=conversation_id,
                        conversation_type=conversation_type,
                        on_fallback_channel=on_fallback_channel,
                    ).inc()

        elif webhook_type == "turn":
            TurnOutboundSerializer(data=request.data).is_valid(raise_exception=True)
            outbound = request.data
            direction = outbound["_vnd"]["v1"]["direction"]
            message_type = outbound.get("type")
            message_requests_total.labels(
                fallback_channel=on_fallback_channel,
                direction=direction,
                message_type=message_type,
            ).inc()
        else:
            return Response(
                {
                    "X-Turn-Hook-Subscription": [
                        f'"{webhook_type}" is not a valid choice for this header.'
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({}, status=status.HTTP_200_OK)
