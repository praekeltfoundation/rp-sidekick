import re
import time

from prometheus_client import Counter, Histogram
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from turn_alerts.serializers import (
    ContactsPayloadSerializer,
    Status_ErrorPayloadSerializer,
    StatusPayloadSerializer,
    VendorPayloadSerializer,
)

from .tasks import start_turn_journey

# Prometheus counters for events and messages
message_requests_total = Counter(
    "turn_alerts_message_requests_total",
    "Total number of message requests",
    [
        "fallback_channel",
        "direction",
        "message_type",
        "message_body",
        "state_reason",
        "state",
        "chat_id",
        "labels",
        "assigned_to",
        "permalink",
    ],
)


event_count = Counter(
    "turn_alerts_event_count",
    "Number of events",
    ["message_status", "error_code", "error_data"],
)

successful_event_count = Counter(
    "turn_alerts_successful_event_count",
    "Number of events",
    ["message_type", "message_status", "conversation_id"],
)


processing_time = Histogram(
    "turn_alerts_request_processing_seconds",
    "Processing time of requests in seconds",
    buckets=(0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)


class TurnAlertsLayerView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        start_time = time.time()

        body = request.data
        request_type = list(body.keys())[0]

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
                message_body=serializer.get_message_body(),
                state_reason=serializer.get_state_reason(),
                state=serializer.get_state(),
                chat_id=serializer.get_chat_id(),
                labels=serializer.get_labels(),
                assigned_to=serializer.get_assigned_to(),
                permalink=serializer.get_permalink(),
            ).inc()

        else:
            if body["statuses"][0]["status"].upper() == "FAILED":
                serializer = Status_ErrorPayloadSerializer(data=body)
                serializer.is_valid(raise_exception=True)
                error_code = serializer.get_error_code()
                error_data = serializer.get_error_data()
                message_status = serializer.get_message_status()
                whatsappid = serializer.get_recipient_id()
                event_count.labels(
                    message_status=message_status,
                    error_code=error_code,
                    error_data=error_data,
                ).inc()

                if error_code == 131026:
                    match = re.match(
                        (
                            r"^\s*(?:\+?(\d{1,3}))?[-. (]*(\d{3})[-. )]"
                            r"*(\d{3})[-. ]*(\d{4})(?: *x(\d+))?\s*$"
                        ),
                        whatsappid,
                    )
                    if match:
                        start_turn_journey(whatsappid)
            else:
                serializer = StatusPayloadSerializer(data=body)
                serializer.is_valid(raise_exception=True)
                whatsappid = serializer.get_recipient_id()
                message_type = serializer.get_message_type()
                message_status = serializer.get_message_status()
                conversation_id = serializer.get_conversation_id()
                successful_event_count.labels(
                    message_type=message_type,
                    message_status=message_status,
                    conversation_id=conversation_id,
                ).inc()

        processing_time.observe(time.time() - start_time)

        return Response({}, status=status.HTTP_200_OK)
