import base64
import hmac
import json
from hashlib import sha256

import responses
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from rp_interceptors.models import Interceptor
from sidekick.tests.utils import create_org


def generate_hmac_signature(body: str, secret: str) -> str:
    h = hmac.new(secret.encode(), body.encode(), sha256)
    return base64.b64encode(h.digest()).decode()


class InterceptorViewTests(APITestCase):
    def setUp(self):
        self.org = create_org()

    def test_hmac_missing(self):
        """
        If the HMAC secret is configured, and there's no HMAC header, or it's invalid,
        then we should return a 403
        """
        interceptor = Interceptor.objects.create(
            org=self.org, hmac_secret="test-secret"
        )
        url = reverse("interceptor-status", args=[interceptor.pk])
        data = {"test": "body"}

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.client.post(
            url, data, format="json", HTTP_X_TURN_HOOK_SIGNATURE="invalid"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @responses.activate
    def test_status_request(self):
        """
        If the request is a status that doesn't have the recipient_id then the recipient_id
        should be pulled from the message object and the request forwarded to the Org URL
        """
        interceptor: Interceptor = Interceptor.objects.create(
            org=self.org, hmac_secret="test-secret"
        )
        url: str = reverse("interceptor-status", args=[interceptor.pk])
        data = {
            "statuses": [
                {
                    "id": "gBEGRHQnRBM2AglN0MpYOUgzMWo",
                    "message": {"recipient_id": "1234567890"},
                    "status": "delivered",
                    "timestamp": "1680519050",
                }
            ]
        }
        body = json.dumps(data, separators=(",", ":"))
        signature = generate_hmac_signature(body, interceptor.hmac_secret)
        expected_data = {
            "statuses": [
                {
                    "id": "gBEGRHQnRBM2AglN0MpYOUgzMWo",
                    "message": {"recipient_id": "1234567890"},
                    "recipient_id": "1234567890",
                    "status": "delivered",
                    "timestamp": "1680519050",
                }
            ]
        }

        responses.add(
            method=responses.POST,
            url="http://localhost:8002/",
            match=[responses.matchers.json_params_matcher(expected_data)],
        )

        response = self.client.post(
            url, data, format="json", HTTP_X_TURN_HOOK_SIGNATURE=signature
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        [call] = responses.calls
        self.assertEqual(
            call.request.headers["X-Turn-Hook-Signature"],
            generate_hmac_signature(
                call.request.body.decode(), interceptor.hmac_secret
            ),
        )

    @responses.activate
    def test_non_status_request(self):
        """
        If the request does not contain a status object then it should be forwarded as is to the Org URL
        """
        interceptor: Interceptor = Interceptor.objects.create(
            org=self.org, hmac_secret="test-secret"
        )
        url: str = reverse("interceptor-status", args=[interceptor.pk])
        data = {
            "messages": [
                {
                    "text": {"body": "No"},
                    "from": "16505551234",
                    "id": "ABGGFmkiWVVPAgo-sKD87hgxPHdF",
                    "timestamp": "1591210827",
                    "type": "text",
                }
            ]
        }
        body = json.dumps(data, separators=(",", ":"))
        signature = generate_hmac_signature(body, interceptor.hmac_secret)

        responses.add(
            method=responses.POST,
            url="http://localhost:8002/",
            match=[responses.matchers.json_params_matcher(data)],
        )

        response = self.client.post(
            url, data, format="json", HTTP_X_TURN_HOOK_SIGNATURE=signature
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        [call] = responses.calls
        self.assertEqual(call.request.headers["X-Turn-Hook-Signature"], signature)

    @responses.activate
    def test_status_request_contains_recipient_id(self):
        """
        If the status in the request already contains the recipient_id then it should be forwarded
        as is to the Org URL
        """
        interceptor: Interceptor = Interceptor.objects.create(
            org=self.org, hmac_secret="test-secret"
        )
        url: str = reverse("interceptor-status", args=[interceptor.pk])
        data = {
            "statuses": [
                {
                    "id": "gBEGRHQnRBM2AglN0MpYOUgzMWo",
                    "message": {"recipient_id": "1234567890"},
                    "recipient_id": "1234567890",
                    "status": "delivered",
                    "timestamp": "1680519050",
                }
            ]
        }
        body = json.dumps(data, separators=(",", ":"))
        signature = generate_hmac_signature(body, interceptor.hmac_secret)

        responses.add(
            method=responses.POST,
            url="http://localhost:8002/",
            match=[responses.matchers.json_params_matcher(data)],
        )

        response = self.client.post(
            url, data, format="json", HTTP_X_TURN_HOOK_SIGNATURE=signature
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        [call] = responses.calls
        self.assertEqual(call.request.headers["X-Turn-Hook-Signature"], signature)

    @responses.activate
    def test_status_request_msg_has_no_recipient_id(self):
        """
        If the message in the status in the request does not contain the recipient_id then we still add
        the recipient_id key to the status object and forwarded it on to the Org URL
        """
        interceptor: Interceptor = Interceptor.objects.create(
            org=self.org, hmac_secret="test-secret"
        )
        url: str = reverse("interceptor-status", args=[interceptor.pk])
        data = {
            "statuses": [
                {
                    "id": "gBEGRHQnRBM2AglN0MpYOUgzMWo",
                    "message": {"text": "blablablabla"},
                    "status": "delivered",
                    "timestamp": "1680519050",
                }
            ]
        }
        body = json.dumps(data, separators=(",", ":"))
        signature = generate_hmac_signature(body, interceptor.hmac_secret)
        expected_data = {
            "statuses": [
                {
                    "id": "gBEGRHQnRBM2AglN0MpYOUgzMWo",
                    "message": {"text": "blablablabla"},
                    "recipient_id": "",
                    "status": "delivered",
                    "timestamp": "1680519050",
                }
            ]
        }

        responses.add(
            method=responses.POST,
            url="http://localhost:8002/",
            match=[responses.matchers.json_params_matcher(expected_data)],
        )

        response = self.client.post(
            url, data, format="json", HTTP_X_TURN_HOOK_SIGNATURE=signature
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        [call] = responses.calls
        self.assertEqual(
            call.request.headers["X-Turn-Hook-Signature"],
            generate_hmac_signature(
                call.request.body.decode(), interceptor.hmac_secret
            ),
        )
