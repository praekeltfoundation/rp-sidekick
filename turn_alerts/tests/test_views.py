import json

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from sidekick.tests.utils import create_org

from .utils import create_turnalerts_account


class TestAlertsViewAbstract(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("test")
        self.client.force_authenticate(user)

        self.org = create_org()
        self.turnalerts_account = create_turnalerts_account(org=self.org)

    def test_org_does_not_exist(self):
        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id + 1}),
            (
                {
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
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(json.loads(response.content), {})


class TestAlertsRoundTrip(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("test")
        self.client.force_authenticate(user)

        self.org = create_org()
        self.turnalerts_account = create_turnalerts_account(org=self.org)

    def test_fail_status_payload_roundtrip(self):
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

        json_data = json.dumps(data)

        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id}),
            content_type="application/json",
            data=json_data.encode("utf-8"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_status_payload_roundtrip(self):
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

        json_data = json.dumps(data)

        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id}),
            content_type="application/json",
            data=json_data.encode("utf-8"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_vendor_payload_roundtrip(self):
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

        json_data = json.dumps(data)

        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id}),
            content_type="application/json",
            data=json_data.encode("utf-8"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_contacts_payload_roundtrip(self):
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

        json_data = json.dumps(data)

        response = self.client.post(
            reverse("turn-messages", kwargs={"org_id": self.org.id}),
            content_type="application/json",
            data=json_data.encode("utf-8"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
