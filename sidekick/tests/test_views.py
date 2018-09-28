import json
import responses
from os import environ
from urllib.parse import urlencode

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from ..models import Organization


class SurveyCheckViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_endpoint(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)

        self.assertTrue("id" in result)
        self.assertEqual(result["id"], None)

        self.assertTrue("version" in result)
        self.assertEqual(result["version"], None)

    def test_health_endpoint_with_vars(self):
        environ["MARATHON_APP_ID"] = "marathon-app-id"
        environ["MARATHON_APP_VERSION"] = "marathon-app-version"

        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)

        self.assertTrue("id" in result)
        self.assertEqual(result["id"], environ["MARATHON_APP_ID"])

        self.assertTrue("version" in result)
        self.assertEqual(result["version"], environ["MARATHON_APP_VERSION"])

    @responses.activate
    def test_send_wa_template_message(self):

        org = Organization.objects.create(
            name="Test Organization",
            url="http://localhost:8002/",
            token="REPLACEME",
            engage_url="http://localhost:8005",
            engage_token="REPLACEME",
        )

        responses.add(
            responses.POST,
            "http://localhost:8005/v1/messages",
            json={
                "messages": [{"id": "sdkjfgksjfgoksdflgs"}],
                "meta": {"api_status": "stable", "version": "2.19.4"},
            },
            status=201,
            match_querystring=True,
        )

        params = {
            "org_id": org.id,
            "wa_id": "1234",
            "namespace": "test.namespace",
            "element_name": "el",
            "message": "hey!",
        }

        url = "{}?{}".format(reverse("send_template"), urlencode(params))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        request_body = json.loads(responses.calls[0].request.body)
        self.assertEqual(
            request_body,
            {
                "to": "1234",
                "type": "hsm",
                "hsm": {
                    "namespace": "test.namespace",
                    "element_name": "el",
                    "language": {"policy": "fallback", "code": "en_US"},
                    "localizable_params": [{"default": "hey!"}],
                },
            },
        )

    @responses.activate
    def test_send_wa_template_message_invalid_chars(self):

        org = Organization.objects.create(
            name="Test Organization",
            url="http://localhost:8002/",
            token="REPLACEME",
            engage_url="http://localhost:8005",
            engage_token="REPLACEME",
        )

        responses.add(
            responses.POST,
            "http://localhost:8005/v1/messages",
            json={
                "messages": [{"id": "sdkjfgksjfgoksdflgs"}],
                "meta": {"api_status": "stable", "version": "2.19.4"},
            },
            status=201,
            match_querystring=True,
        )

        params = {
            "org_id": org.id,
            "wa_id": "1234",
            "namespace": "test.namespace",
            "element_name": "el",
            "message": "No new lines\nNo tabs\t              No huge spaces",
        }

        url = "{}?{}".format(reverse("send_template"), urlencode(params))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        request_body = json.loads(responses.calls[0].request.body)

        self.assertEqual(
            request_body["hsm"]["localizable_params"][0]["default"],
            "No new lines No tabs No huge spaces",
        )

    def test_send_wa_template_message_no_org(self):
        params = {
            "org_id": "2",
            "wa_id": "1234",
            "namespace": "test.namespace",
            "element_name": "el",
            "message": "hey!",
        }

        url = "{}?{}".format(reverse("send_template"), urlencode(params))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_wa_template_message_missing_params(self):
        params = {
            "org_id": "2",
            "wa_id": "1234",
            "namespace": "test.namespace",
            "element_name": "el",
        }

        url = "{}?{}".format(reverse("send_template"), urlencode(params))

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
