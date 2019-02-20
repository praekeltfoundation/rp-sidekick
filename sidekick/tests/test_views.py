import json
import responses
from os import environ
from urllib.parse import urlencode

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token

from ..models import Organization


FAKE_ENGAGE_URL = "http://localhost:8005"


class HealthViewTest(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

    def test_health_endpoint(self):
        response = self.api_client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)

        self.assertTrue("id" in result)
        self.assertEqual(result["id"], None)

        self.assertTrue("version" in result)
        self.assertEqual(result["version"], None)

    def test_health_endpoint_with_vars(self):
        environ["MARATHON_APP_ID"] = "marathon-app-id"
        environ["MARATHON_APP_VERSION"] = "marathon-app-version"

        response = self.api_client.get(reverse("health"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = json.loads(response.content)

        self.assertTrue("id" in result)
        self.assertEqual(result["id"], environ["MARATHON_APP_ID"])

        self.assertTrue("version" in result)
        self.assertEqual(result["version"], environ["MARATHON_APP_VERSION"])


class SidekickAPITestCase(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

        self.user = get_user_model().objects.create_superuser(
            username="superuser", email="superuser@email.com", password="pass"
        )
        token = Token.objects.create(user=self.user)
        self.token = token.key
        self.api_client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

    def mk_org(self):
        return Organization.objects.create(
            name="Test Organization",
            url="http://localhost:8002/",
            token="REPLACEME",
            engage_url=FAKE_ENGAGE_URL,
            engage_token="REPLACEME",
        )


class TestSendTemplateView(SidekickAPITestCase):
    def add_whatsapp_messages_200_response(self, responses):
        """
        Keep things DRY by reusing this snippet when testing WA response
        """
        responses.add(
            responses.POST,
            "{}/v1/messages".format(FAKE_ENGAGE_URL),
            json={
                "messages": [{"id": "sdkjfgksjfgoksdflgs"}],
                "meta": {"api_status": "stable", "version": "2.19.4"},
            },
            status=201,
            match_querystring=True,
        )

    @responses.activate
    def test_send_wa_template_message_success_no_params(self):
        org = self.mk_org()
        self.add_whatsapp_messages_200_response(responses)

        params = {
            "org_id": org.id,
            "wa_id": "1234",
            "namespace": "test.namespace",
            "element_name": "el",
        }

        url = "{}?{}".format(reverse("send_template"), urlencode(params))

        response = self.api_client.get(url)
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
                    "localizable_params": [],
                },
            },
        )

    @responses.activate
    def test_send_wa_template_message_success_params(self):
        org = self.mk_org()
        self.add_whatsapp_messages_200_response(responses)

        params = {
            "org_id": org.id,
            "wa_id": "1234",
            "namespace": "test.namespace",
            "element_name": "el",
            "1": "R25",
            "0": "Ola",
        }

        url = "{}?{}".format(reverse("send_template"), urlencode(params))

        response = self.api_client.get(url)
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
                    "localizable_params": [
                        {"default": "Ola"},
                        {"default": "R25"},
                    ],
                },
            },
        )

    def test_send_wa_template_message_no_org(self):
        params = {
            "org_id": "2",
            "wa_id": "1234",
            "namespace": "test.namespace",
            "element_name": "el",
            "0": "hey!",
        }

        url = "{}?{}".format(reverse("send_template"), urlencode(params))

        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertTrue("error" in content)
        self.assertEquals(content["error"], "Organization not found")

    def test_send_wa_template_message_missing_params(self):
        org = self.mk_org()
        params = {
            "org_id": org.id,
            "wa_id": "1234",
            "namespace": "test.namespace",
            #  missing param:
            #  "element_name": "el",
        }

        url = "{}?{}".format(reverse("send_template"), urlencode(params))

        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertTrue("error" in content)
        self.assertEquals(content["error"], "Missing fields: element_name")


class TestCheckContactView(SidekickAPITestCase):
    @responses.activate
    def test_wa_check_contact_valid(self):
        # set up
        org = self.mk_org()
        telephone_number = "+27820000001"

        responses.add(
            responses.POST,
            "{}/v1/contacts".format(FAKE_ENGAGE_URL),
            json={
                "contacts": [
                    {
                        "input": telephone_number,
                        "status": "valid",
                        "wa_id": telephone_number.replace("+", ""),
                    }
                ]
            },
            status=201,
            match_querystring=True,
        )

        # get result
        response = self.api_client.get(
            reverse(
                "check_contact",
                kwargs={"org_id": org.id, "msisdn": telephone_number},
            )
        )

        # inspect request to Turn
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        turn_request_body = json.loads(responses.calls[0].request.body)
        self.assertEqual(
            turn_request_body,
            {"blocking": "wait", "contacts": [telephone_number]},
        )

        # inspect response from Sidekick
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertTrue("status" in content)
        self.assertEquals(content["status"], "valid")

    @responses.activate
    def test_wa_check_contact_invalid(self):
        # set up
        org = self.mk_org()
        telephone_number = "+27820000001"

        responses.add(
            responses.POST,
            "{}/v1/contacts".format(FAKE_ENGAGE_URL),
            json={
                "contacts": [{"input": telephone_number, "status": "invalid"}]
            },
            status=201,
            match_querystring=True,
        )

        # get result
        response = self.api_client.get(
            reverse(
                "check_contact",
                kwargs={"org_id": org.id, "msisdn": telephone_number},
            )
        )

        # inspect request to Turn
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        turn_request_body = json.loads(responses.calls[0].request.body)
        self.assertEqual(
            turn_request_body,
            {"blocking": "wait", "contacts": [telephone_number]},
        )

        # inspect response from Sidekick
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertTrue("status" in content)
        self.assertEquals(content["status"], "invalid")

    @responses.activate
    def test_wa_check_contact_error(self):
        # set up
        org = self.mk_org()
        telephone_number = "+27820000001"

        responses.add(
            responses.POST,
            "{}/v1/contacts".format(FAKE_ENGAGE_URL),
            "Invalid WhatsApp Token",
            status=status.HTTP_403_FORBIDDEN,
            match_querystring=True,
        )

        # get result
        response = self.api_client.get(
            reverse(
                "check_contact",
                kwargs={"org_id": org.id, "msisdn": telephone_number},
            )
        )

        # inspect response from Sidekick
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        content = json.loads(response.content)
        self.assertTrue("error" in content)
        self.assertEquals(content["error"], "Invalid WhatsApp Token")

    def test_wa_check_contact_no_org(self):
        # get result
        response = self.api_client.get(
            reverse(
                "check_contact", kwargs={"org_id": 99, "msisdn": "16315551003"}
            )
        )

        # inspect response from Sidekick
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertTrue("error" in content)
        self.assertEquals(content["error"], "Organization not found")
