import base64
import hmac
import json
from hashlib import sha256
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.test import APIRequestFactory, APITestCase

from sidekick.models import Organization
from sidekick.tests.utils import create_org
from turn_alerts.models import TurnActions
from turn_alerts.views import TurnAlertsLayerView

from .utils import create_turnalerts_account


class TestAlertsViewAbstract(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("test")
        self.client.force_authenticate(user)

        self.org = create_org()
        self.turnalerts_account = create_turnalerts_account(org=self.org)

    def generate_hmac_signature(self, data, key):
        data = JSONRenderer().render(data)
        h = hmac.new(key.encode(), data, sha256)
        return base64.b64encode(h.digest()).decode()

    def test_signature_required(self):
        """
        Should return 400 if signature is not provided
        """

        data = {
            "statuses": [
                {
                    "errors": [
                        {
                            "code": 131026,
                            "error_data": {"details": "Message Undeliverable."},
                            "message": "Message undeliverable",
                            "title": "Message undeliverable",
                        }
                    ],
                    "id": "wamid.HBgFMzE1MzEVAgARGBIzMzQ2RUY0MUU4OTJGOEM5MjAA",
                    "recipient_id": "31531",
                    "status": "failed",
                    "timestamp": "1735425598",
                }
            ]
        }
        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id + 1}),
            data,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"X-Turn-Hook-Subscription": ["This header is required."]}
        )

    def test_org_does_not_exist(self):
        """
        Should return 400 if org does not exist
        """

        data = {
            "statuses": [
                {
                    "errors": [
                        {
                            "code": 131026,
                            "error_data": {"details": "Message Undeliverable."},
                            "message": "Message undeliverable",
                            "title": "Message undeliverable",
                        }
                    ],
                    "id": "wamid.HBgFMzE1MzEVAgARGBIzMzQ2RUY0MUU4OTJGOEM5MjAA",
                    "recipient_id": "31531",
                    "status": "failed",
                    "timestamp": "1735425598",
                }
            ]
        }
        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id + 1}),
            data,
            format="json",
            HTTP_X_TURN_HOOK_SIGNATURE=self.generate_hmac_signature(data, "REPLACEME"),
            HTTP_X_TURN_HOOK_SUBSCRIPTION="whatsapp",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestAlertsRoundTrip(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("test")
        self.client.force_authenticate(user)

        self.org = create_org()
        self.turnalerts_account = create_turnalerts_account(org=self.org)

    def generate_hmac_signature(self, data, key):
        data = JSONRenderer().render(data)
        h = hmac.new(key.encode(), data, sha256)
        return base64.b64encode(h.digest()).decode()

    def test_fail_status_payload_roundtrip(self):
        """
        Test roundtrip for status failed event
        """
        data = {
            "statuses": [
                {
                    "errors": [
                        {
                            "code": 131026,
                            "error_data": {"details": "Message Undeliverable."},
                            "message": "Message undeliverable",
                            "title": "Message undeliverable",
                        }
                    ],
                    "id": "wamid.HBgFMzE1MzEVAgARGBIzMzQ2RUY0MUU4OTJGOEM5MjAA",
                    "recipient_id": "31531",
                    "status": "failed",
                    "timestamp": "1735425598",
                }
            ]
        }

        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id}),
            data,
            format="json",
            HTTP_X_TURN_HOOK_SIGNATURE=self.generate_hmac_signature(data, "REPLACEME"),
            HTTP_X_TURN_HOOK_SUBSCRIPTION="whatsapp",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_status_payload_roundtrip(self):
        """
        Test roundtrip for status payload
        """
        data = {
            "statuses": [
                {
                    "conversation": {
                        "expiration_timestamp": "1735510680",
                        "id": "57f7d7d4d255f4c7987ac3557bf536e3",
                        "origin": {"type": "service"},
                    },
                    "id": "wamid.HBgNMjM0OTAzOTc1NjYyOBUCABEYEjdCMTJFNUZDNzNFQjkxQ0IyRQA=",
                    "pricing": {
                        "billable": True,
                        "category": "service",
                        "pricing_model": "CBP",
                    },
                    "recipient_id": "2349039756628",
                    "status": "sent",
                    "timestamp": "1735424268",
                }
            ]
        }

        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id}),
            data,
            format="json",
            HTTP_X_TURN_HOOK_SIGNATURE=self.generate_hmac_signature(data, "REPLACEME"),
            HTTP_X_TURN_HOOK_SUBSCRIPTION="whatsapp",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vendor_payload_roundtrip(self):
        """
        Test roundtrip for vnd payload
        """
        data = {
            "_vnd": {
                "v1": {
                    "author": {
                        "id": "d2e805b5-4a25-4102-a629-e6b67c798ad6",
                        "name": "WhatsApp Business Cloud API",
                        "request_id": "GBV3LTlUEUtfjuMHaDYi",
                        "type": "SYSTEM",
                    },
                    "card_uuid": None,
                    "chat": {
                        "assigned_to": {
                            "id": "78c711b6-2673-cd8b-0fd9-9a6f03bbcdc5",
                            "name": "Chima Chinda",
                            "type": "OPERATOR",
                        },
                        "contact_uuid": "5ba732cf-d424-4163-9d73-98680d4f53f9",
                        "inserted_at": "2022-05-10T10:15:38.808899Z",
                        "owner": "+2349039756628",
                        "permalink": "https://whatsapp-praekelt-cloud.turn.io/app/c/ebd12728-e787-4f29-b938-1059b67f4abd",
                        "state": "OPEN",
                        "state_reason": "Re-opened by inbound message.",
                        "unread_count": 18,
                        "updated_at": "2024-12-28T22:17:48.825870Z",
                        "uuid": "ebd12728-e787-4f29-b938-1059b67f4abd",
                    },
                    "direction": "outbound",
                    "faq_uuid": None,
                    "in_reply_to": None,
                    "inserted_at": "2024-12-28T22:17:48.817259Z",
                    "labels": [],
                    "last_status": None,
                    "last_status_timestamp": None,
                    "on_fallback_channel": False,
                    "rendered_content": None,
                    "uuid": "7d5fc64e-fd77-325f-8a50-6475e4496775",
                }
            },
            "from": "27726968450",
            "id": "wamid.HBgNMjM0OTAzOTc1NjYyOBUCABEYEjdCMTJFNUZDNzNFQjkxQ0IyRQA=",
            "preview_url": False,
            "recipient_type": "individual",
            "text": {
                "body": "The MomConnect ADA Symptom Checker is unfortunately no longer available. \n\nPlease reply *ASK* if you have questions or need help."
            },
            "timestamp": "1735424268",
            "to": "2349039756628",
            "type": "text",
        }

        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id}),
            data,
            format="json",
            HTTP_X_TURN_HOOK_SIGNATURE=self.generate_hmac_signature(data, "REPLACEME"),
            HTTP_X_TURN_HOOK_SUBSCRIPTION="turn",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contacts_payload_roundtrip(self):
        """
        Test roundtrip for contacts payload
        """
        data = {
            "contacts": [
                {"profile": {"name": "Chima Chinda"}, "wa_id": "2349039756628"}
            ],
            "messages": [
                {
                    "_vnd": {
                        "v1": {
                            "author": {
                                "id": "2349039756628",
                                "name": "Chima Chinda",
                                "type": "OWNER",
                            },
                            "card_uuid": None,
                            "chat": {
                                "assigned_to": {
                                    "id": "78c711b6-2673-cd8b-0fd9-9a6f03bbcdc5",
                                    "name": "Chima Chinda",
                                    "type": "OPERATOR",
                                },
                                "contact_uuid": "5ba732cf-d424-4163-9d73-98680d4f53f9",
                                "inserted_at": "2022-05-10T10:15:38.808899Z",
                                "owner": "+2349039756628",
                                "permalink": "https://whatsapp-praekelt-cloud.turn.io/app/c/ebd12728-e787-4f29-b938-1059b67f4abd",
                                "state": "OPEN",
                                "state_reason": "Re-opened by inbound message.",
                                "unread_count": 18,
                                "updated_at": "2024-12-28T22:17:48.825870Z",
                                "uuid": "ebd12728-e787-4f29-b938-1059b67f4abd",
                            },
                            "direction": "inbound",
                            "faq_uuid": None,
                            "in_reply_to": None,
                            "inserted_at": "2024-12-28T22:17:54.617573Z",
                            "labels": [],
                            "last_status": None,
                            "last_status_timestamp": None,
                            "on_fallback_channel": False,
                            "rendered_content": None,
                            "uuid": "4e29c576-5901-4aaa-22bb-9887e0c5bc98",
                        }
                    },
                    "from": "2349039756628",
                    "id": "wamid.HBgNMjM0OTAzOTc1NjYyOBUCABIYFDNGODg1NDQxRDE0MjFGOURBOUY1AA==",
                    "text": {"body": "Testing"},
                    "timestamp": "1735424273",
                    "type": "text",
                }
            ],
        }

        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id}),
            data,
            format="json",
            HTTP_X_TURN_HOOK_SIGNATURE=self.generate_hmac_signature(data, "REPLACEME"),
            HTTP_X_TURN_HOOK_SUBSCRIPTION="whatsapp",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TurnAlertsLayerViewTest(TestCase):

    def generate_hmac_signature(self, data, key):
        data = JSONRenderer().render(data)
        h = hmac.new(key.encode(), data, sha256)
        return base64.b64encode(h.digest()).decode()

    """
    Mock data for Turn failed event and assert that Turn journey
    is called with the expected arguments
    """

    @patch("turn_alerts.views.start_turn_journey")
    def test_start_turn_journey_called_with_correct_arguments(
        self, mock_start_turn_journey
    ):
        request_data = {
            "statuses": [
                {
                    "errors": [
                        {
                            "code": 131026,
                            "error_data": {"details": "Message Undeliverable."},
                            "message": "Message undeliverable",
                            "title": "Message undeliverable",
                        }
                    ],
                    "id": "wamid.HBgFMzE1MzEVAgARGBIzMzQ2RUY0MUU4OTJGOEM5MjAA",
                    "recipient_id": "27796312456",
                    "status": "failed",
                    "timestamp": "1735425598",
                }
            ]
        }
        self.org = create_org()
        turn_action = Mock()
        turn_action.journey_id = "journey_id"
        turn_action.error_code = 131026

        rf = APIRequestFactory()
        request = rf.post(
            "/1/api/v2/messages",
            data=json.dumps(request_data),
            content_type="application/json",
        )

        request.META["HTTP_X_TURN_HOOK_SIGNATURE"] = self.generate_hmac_signature(
            request_data, "REPLACEME"
        )
        request.META["HTTP_X_TURN_HOOK_SUBSCRIPTION"] = "whatsapp"

        request.data = json.loads(request.body)

        with patch.object(TurnActions.objects, "filter", return_value=[turn_action]):
            with patch.object(Organization.objects, "get", return_value=self.org):
                view = TurnAlertsLayerView()
                response = view.post(request, org_id=1)

        mock_start_turn_journey.assert_called_once_with(
            "27796312456", "journey_id", "http://whatsapp/", "test-token"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
