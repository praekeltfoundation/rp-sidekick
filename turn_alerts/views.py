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

from .models import TurnAlerts
from .tasks import start_turn_journey

request_count = Counter(
    "turn_alerts_request_total", "Total number of requests to TurnAlertsLayerView"
)
processing_time = Histogram(
    "turn_alerts_request_processing_seconds", "Processing time of requests in seconds"
)


class TurnAlertsLayerView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        start_time = time.time()  # Start time measurement

        body = request.data
        request_type = list(body.keys())[0]
        if request_type == "contacts":
            serializer = ContactsPayloadSerializer(data=body)
            serializer.is_valid(raise_exception=True)
            whatsappid = serializer.get_recipient_id()
            message_type = serializer.get_message_type()
            assigned_to = serializer.get_assigned_to()
            direction = serializer.get_direction()
            fallback_channel = serializer.get_fallback_channel()
            labels = serializer.get_labels()
            chat_id = serializer.get_chat_id()
            permalink = serializer.get_permalink()
            state = serializer.get_state()
            state_reason = serializer.get_state_reason()
            message_body = serializer.get_message_body
            store_url_entry = TurnAlerts(
                whatsappid=whatsappid,
                message_type=message_type,
                chat_id=chat_id,
                assigned_to=assigned_to,
                message_direction=direction,
                permalink=permalink,
                message_body=message_body,
                labels=labels,
                fallback_channel=fallback_channel,
                state=state,
                state_reason=state_reason,
            )
            store_url_entry.save()

        elif request_type == "_vnd":
            serializer = VendorPayloadSerializer(data=body)
            serializer.is_valid(raise_exception=True)
            whatsappid = serializer.get_recipient_id()
            message_type = serializer.get_message_type()
            message_body = serializer.get_message_body()
            author_id = serializer.get_author_id()
            chat_id = serializer.get_chat_id()
            permalink = serializer.get_permalink()
            state = serializer.get_state()
            state_reason = serializer.get_state_reason()
            direction = serializer.get_direction()
            fallback_channel = serializer.get_fallback_channel()
            labels = serializer.get_labels()
            assigned_to = serializer.get_assigned_to()
            store_url_entry = TurnAlerts(
                whatsappid=whatsappid,
                message_type=message_type,
                chat_id=chat_id,
                assigned_to=assigned_to,
                author_id=author_id,
                message_direction=direction,
                permalink=permalink,
                message_body=message_body,
                labels=labels,
                fallback_channel=fallback_channel,
                state=state,
                state_reason=state_reason,
            )
            store_url_entry.save()

        else:
            if body["statuses"][0]["status"].upper() == "FAILED":
                serializer = Status_ErrorPayloadSerializer(data=body)
                serializer.is_valid(raise_exception=True)
                error_code = serializer.get_error_code()
                error_data = serializer.get_error_data()
                message_status = serializer.get_message_status()
                whatsappid = serializer.get_recipient_id()
                store_url_entry = TurnAlerts(
                    whatsappid=whatsappid,
                    message_status=message_status,
                    error_data=error_data,
                    error_code=error_code,
                )
                store_url_entry.save()

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
                store_url_entry = TurnAlerts(
                    conversation_id=conversation_id,
                    whatsappid=whatsappid,
                    message_status=message_status,
                    message_type=message_type,
                )
                store_url_entry.save()

        processing_time.observe(time.time() - start_time)

        return Response({}, status=status.HTTP_200_OK)
