import json
import responses
from mock import patch
from os import environ
from urllib.parse import urlencode

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError
from django.test.utils import override_settings

from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token

from .utils import create_org


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


class DetailedHealthViewTest(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

    def mock_queue_lookup(self, name="rp_sidekick", messages=1256, rate=1.25):
        responses.add(
            responses.GET,
            "{}{}".format(settings.RABBITMQ_MANAGEMENT_INTERFACE, name),
            json={
                "messages": messages,
                "messages_details": {"rate": rate},
                "name": name,
            },
            status=200,
            match_querystring=True,
        )

    @responses.activate
    def test_detailed_health_endpoint_not_stuck_and_db_available(self):
        self.mock_queue_lookup()

        response = self.api_client.get(reverse("detailed-health"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.json()["queues"][0]["stuck"])
        self.assertTrue(response.json()["db_available"])

    @responses.activate
    def test_detailed_health_endpoint_stuck(self):
        self.mock_queue_lookup(rate=0.0)

        response = self.api_client.get(reverse("detailed-health"))

        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertTrue(response.json()["queues"][0]["stuck"])

    @override_settings(RABBITMQ_MANAGEMENT_INTERFACE=False)
    def test_detailed_health_endpoint_deactivated(self):
        response = self.api_client.get(reverse("detailed-health"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["update"], "queues not checked")
        self.assertEqual(response.json()["queues"], [])

    @patch("django.db.backends.postgresql.base.DatabaseWrapper.cursor")
    @override_settings(RABBITMQ_MANAGEMENT_INTERFACE=False)
    def test_db_connection_down(self, mock_cursor):
        mock_cursor.side_effect = OperationalError()
        response = self.api_client.get(reverse("detailed-health"))

        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        self.assertFalse(response.json()["db_available"])


class SidekickAPITestCase(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

        self.user = get_user_model().objects.create_superuser(
            username="superuser", email="superuser@email.com", password="pass"
        )
        token = Token.objects.get(user=self.user)
        self.token = token.key
        self.api_client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

        self.org = create_org(engage_url=FAKE_ENGAGE_URL)
        self.org.users.add(self.user)


class TestSendTemplateView(SidekickAPITestCase):
    def add_whatsapp_messages_200_response(self):
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
        self.add_whatsapp_messages_200_response()

        params = {
            "org_id": self.org.id,
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
        self.add_whatsapp_messages_200_response()

        params = {
            "org_id": self.org.id,
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

    def test_send_wa_template_message_does_not_belong_to_org(self):
        self.org.users.remove(self.user)
        params = {
            "org_id": self.org.id,
            "wa_id": "1234",
            "namespace": "test.namespace",
            "element_name": "el",
            "0": "hey!",
        }

        url = "{}?{}".format(reverse("send_template"), urlencode(params))

        response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        content = json.loads(response.content)
        self.assertTrue("error" in content)
        self.assertEquals(
            content["error"],
            "Authenticated user does not belong to specified Organization",
        )

    def test_send_wa_template_message_missing_params(self):
        params = {
            "org_id": self.org.id,
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
                kwargs={"org_id": self.org.id, "msisdn": telephone_number},
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
                kwargs={"org_id": self.org.id, "msisdn": telephone_number},
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
                kwargs={"org_id": self.org.id, "msisdn": telephone_number},
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
                "check_contact",
                kwargs={"org_id": self.org.id + 1, "msisdn": "16315551003"},
            )
        )

        # inspect response from Sidekick
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        content = json.loads(response.content)
        self.assertTrue("error" in content)
        self.assertEquals(content["error"], "Organization not found")

    def test_wa_check_contact_does_not_belong_to_org(self):
        self.org.users.remove(self.user)
        # get result
        response = self.api_client.get(
            reverse(
                "check_contact",
                kwargs={"org_id": self.org.id, "msisdn": "16315551003"},
            )
        )

        # inspect response from Sidekick
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        content = json.loads(response.content)
        self.assertTrue("error" in content)
        self.assertEquals(
            content["error"],
            "Authenticated user does not belong to specified Organization",
        )
