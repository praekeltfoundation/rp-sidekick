import json
from os import environ
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import urlencode
from uuid import uuid4

import responses
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.utils import OperationalError
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase
from temba_client.exceptions import TembaConnectionError

from sidekick.models import Consent, Organization

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

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
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

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
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
                    "language": {"policy": "fallback", "code": "en"},
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
                    "language": {"policy": "fallback", "code": "en"},
                    "localizable_params": [{"default": "Ola"}, {"default": "R25"}],
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
        self.assertEqual(content["error"], "Organization not found")

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
        self.assertEqual(
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
        self.assertEqual(content["error"], "Missing fields: element_name")


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
            turn_request_body, {"blocking": "wait", "contacts": [telephone_number]}
        )

        # inspect response from Sidekick
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertTrue("status" in content)
        self.assertEqual(content["status"], "valid")

    @responses.activate
    def test_wa_check_contact_invalid(self):
        # set up
        telephone_number = "+27820000001"

        responses.add(
            responses.POST,
            "{}/v1/contacts".format(FAKE_ENGAGE_URL),
            json={"contacts": [{"input": telephone_number, "status": "invalid"}]},
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
            turn_request_body, {"blocking": "wait", "contacts": [telephone_number]}
        )

        # inspect response from Sidekick
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertTrue("status" in content)
        self.assertEqual(content["status"], "invalid")

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
        self.assertEqual(content["error"], "Invalid WhatsApp Token")

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
        self.assertEqual(content["error"], "Organization not found")

    def test_wa_check_contact_does_not_belong_to_org(self):
        self.org.users.remove(self.user)
        # get result
        response = self.api_client.get(
            reverse(
                "check_contact", kwargs={"org_id": self.org.id, "msisdn": "16315551003"}
            )
        )

        # inspect response from Sidekick
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        content = json.loads(response.content)
        self.assertTrue("error" in content)
        self.assertEqual(
            content["error"],
            "Authenticated user does not belong to specified Organization",
        )


class GetConsentURLViewTest(APITestCase):
    def test_auth_required(self):
        """
        Authorization is required to access the endpoint
        """
        url = reverse("get-consent-url", args=[1])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_required(self):
        """
        The user needs the appropriate permission to access the endpoint
        """
        url = reverse("get-consent-url", args=[1])
        user = get_user_model().objects.create_user("test")
        self.client.force_authenticate(user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def login_user(self):
        user = get_user_model().objects.create_user("test")
        permission = Permission.objects.get(name="Can add consent")
        user.user_permissions.add(permission)
        user.save()
        self.client.force_authenticate(user)

    def test_invalid_body(self):
        """
        If the body of the request is invalid, we should return a Bad Request error
        """
        url = reverse("get-consent-url", args=[1])
        self.login_user()

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_id(self):
        """
        If a Consent with the specified ID doesn't exist in the database, we should
        return a Not Found
        """
        url = reverse("get-consent-url", args=[1])
        self.login_user()

        response = self.client.post(
            url,
            {"contact": {"uuid": str(uuid4()), "urn": "whatsapp:27820001001"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_url(self):
        """
        A successful request should return a valid URL
        """
        org = Organization.objects.create()
        consent = Consent.objects.create(org=org, flow_id=uuid4())
        url = reverse("get-consent-url", args=[consent.id])
        self.login_user()

        contact_uuid = uuid4()
        response = self.client.post(
            url,
            {"contact": {"uuid": str(contact_uuid), "urn": "whatsapp:27820001001"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json()["url"],
            consent.generate_url(response.wsgi_request, contact_uuid),
        )


class ConsentRedirectViewTests(TestCase):
    def test_bad_code(self):
        """
        A 400 error should be returned for an invalid code
        """
        url = reverse("redirect-consent", args=["foo"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_redirects(self):
        """
        The response should contain a redirect meta tag
        """
        org = Organization.objects.create()
        consent = Consent.objects.create(org=org, flow_id=uuid4())
        contact_uuid = uuid4()
        code = consent.generate_code(contact_uuid)
        url = reverse("redirect-consent", args=[code])
        redirect_url = reverse("provide-consent", args=[code])

        response = self.client.get(url)
        self.assertContains(response, redirect_url)

    def test_metadata(self):
        """
        The response should contain all the configured metadata
        """
        org = Organization.objects.create()
        consent = Consent.objects.create(
            org=org,
            flow_id=uuid4(),
            preview_title="test title",
            preview_description="test description",
            preview_url="example.org/preview",
            preview_image_url="example.org/image",
        )
        contact_uuid = uuid4()
        code = consent.generate_code(contact_uuid)
        url = reverse("redirect-consent", args=[code])

        response = self.client.get(url)
        self.assertContains(response, "test title")
        self.assertContains(response, "test description")
        self.assertContains(response, "example.org/preview")
        self.assertContains(response, "example.org/image")


class ProvideConsentViewTest(APITestCase):
    def test_invalid_code(self):
        """
        If an invalid code is given, we should respond with a Bad Request error
        """
        url = reverse("provide-consent", args=["foo"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("sidekick.tasks.start_flow")
    def test_flow_id(self, start_flow_mock):
        """
        If there's a flow id configured on the Consent, then we should trigger that flow
        """
        org = Organization.objects.create()
        consent = Consent.objects.create(org=org, flow_id=uuid4())
        contact_uuid = uuid4()
        code = consent.generate_code(contact_uuid)

        url = reverse("provide-consent", args=[code])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        start_flow_mock.assert_called_once_with(
            org, str(contact_uuid), str(consent.flow_id)
        )

    def test_redirect_url(self):
        """
        If the Consent has a redirect url configured, we should redirect to that URL
        """
        org = Organization.objects.create()
        consent = Consent.objects.create(org=org, redirect_url="http://example.org")
        contact_uuid = uuid4()
        code = consent.generate_code(contact_uuid)

        url = reverse("provide-consent", args=[code])
        response = self.client.get(url)
        self.assertRedirects(
            response, "http://example.org", fetch_redirect_response=False
        )


class LabelTurnConversationViewTests(SidekickAPITestCase):
    def test_auth_required(self):
        """
        Authorization is required to access the endpoint
        """
        url = reverse("label-turn-conversation", args=[1])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_required(self):
        """
        The user needs the appropriate permission to access the endpoint
        """
        url = reverse("label-turn-conversation", args=[1])
        user = get_user_model().objects.create_user("test")
        self.client.force_authenticate(user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def login_user(self):
        user = get_user_model().objects.create_user("test")
        permission = Permission.objects.get(name="Can label a Turn Conversation")
        user.user_permissions.add(permission)
        user.save()
        self.client.force_authenticate(user)

    def test_invalid_id(self):
        """
        If an Org with the specified ID doesn't exist in the database, we should return
        a Not Found
        """
        url = reverse("label-turn-conversation", args=[0])
        self.login_user()

        response = self.client.post(
            url,
            {"contact": {"uuid": str(uuid4()), "urn": "whatsapp:27820001001"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_body(self):
        """
        If the body of the request is invalid, we should return a Bad Request error
        """
        url = reverse("label-turn-conversation", args=[self.org.id])
        self.login_user()

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("sidekick.views.add_label_to_turn_conversation")
    def test_post_url(self, task):
        """
        A successful request should start the task and return the task ID
        """
        task_instance = MagicMock()
        task_instance.id = "test-task-id"
        task.delay.return_value = task_instance

        url = reverse("label-turn-conversation", args=[self.org.id])
        url = "{}?{}".format(url, urlencode((("label", "foo"), ("label", "bar"))))
        self.login_user()

        response = self.client.post(
            url,
            {"contact": {"uuid": str(uuid4()), "urn": "whatsapp:27820001001"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {"task_id": "test-task-id"})
        task.delay.assert_called_once_with(self.org.id, "27820001001", ["foo", "bar"])


class ArchiveTurnConversationViewTests(SidekickAPITestCase):
    def test_auth_required(self):
        """
        Authorization is required to access the endpoint
        """
        url = reverse("archive-turn-conversation", args=[1])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permission_required(self):
        """
        The user needs the appropriate permission to access the endpoint
        """
        url = reverse("archive-turn-conversation", args=[1])
        user = get_user_model().objects.create_user("test")
        self.client.force_authenticate(user)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def login_user(self):
        user = get_user_model().objects.create_user("test")
        permission = Permission.objects.get(name="Can archive a Turn Conversation")
        user.user_permissions.add(permission)
        user.save()
        self.client.force_authenticate(user)

    def test_invalid_id(self):
        """
        If an Org with the specified ID doesn't exist in the database, we should return
        a Not Found
        """
        url = reverse("archive-turn-conversation", args=[0])
        self.login_user()

        response = self.client.post(
            url,
            {"contact": {"uuid": str(uuid4()), "urn": "whatsapp:27820001001"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_body(self):
        """
        If the body of the request is invalid, we should return a Bad Request error
        """
        url = reverse("archive-turn-conversation", args=[self.org.id])
        self.login_user()

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("sidekick.views.archive_turn_conversation")
    def test_post_url(self, task):
        """
        A successful request should start the task and return the task ID
        """
        task_instance = MagicMock()
        task_instance.id = "test-task-id"
        task.delay.return_value = task_instance

        url = reverse("archive-turn-conversation", args=[self.org.id])
        url = "{}?{}".format(url, urlencode({"reason": "Test reason"}))
        self.login_user()

        response = self.client.post(
            url,
            {"contact": {"uuid": str(uuid4()), "urn": "whatsapp:27820001001"}},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {"task_id": "test-task-id"})
        task.delay.assert_called_once_with(self.org.id, "27820001001", "Test reason")


class ListContactsViewTests(SidekickAPITestCase):
    def test_non_existent_org_raises_error(self):
        """
        If an Org with the specified ID doesn't exist in the database, return 404
        """
        self.client.force_authenticate(self.user)

        url = reverse("list_contacts", args=[0])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_not_in_org_raises_error(self):
        """
        If the authenticated user isn't associated with the Org, return 401
        """
        self.org.users.remove(self.user)
        self.client.force_authenticate(self.user)

        url = reverse("list_contacts", args=[self.org.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("temba_client.v2.TembaClient.get_contacts")
    def test_params_are_passed_to_get_contact_for_valid_rp_fields(
        self, mock_get_contacts
    ):
        """
        All query parameters for valid RP fields should be passed to get_contacts
        """
        self.client.force_authenticate(self.user)

        # Iterfetches returns batches of returned objects
        mock_get_contacts.return_value.iterfetches.return_value = [[]]

        url = reverse("list_contacts", args=[self.org.pk])
        response = self.client.get("{}?group=special&deleted=true".format(url))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_get_contacts.assert_called_once_with(
            **{"group": "special", "deleted": "true"}
        )

    @patch("temba_client.v2.TembaClient.get_contacts")
    def test_endpoint_returns_contact_uuids(self, mock_get_contacts):
        """
        A list containing the uuids of the found contacts should be returned
        """
        self.client.force_authenticate(self.user)

        # Create mock contacts
        mock_contact_object1 = Mock()
        mock_contact_object1.uuid = "123456"
        mock_contact_object1.fields = {
            "something_else": "stuuuuff",
            "empty": None,
            "some_date": "2018-05-17T00:00:00.000000+02:00",
        }
        mock_contact_object2 = Mock()
        mock_contact_object2.uuid = "7890123"
        mock_contact_object2.fields = {"something_else": "different", "empty": None}
        # Iterfetches returns batches of returned objects
        mock_get_contacts.return_value.iterfetches.return_value = [
            [mock_contact_object1, mock_contact_object2]
        ]

        url = reverse("list_contacts", args=[self.org.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"contacts": ["123456", "7890123"]})

    @patch("temba_client.v2.TembaClient.get_contacts")
    def test_non_rp_fields_filter_on_contact_fields(self, mock_get_contacts):
        """
        Any query parameters that are not options allowed by the RP API should be used
        to filter the returned contacts
        """
        self.client.force_authenticate(self.user)

        # Create mock contacts
        mock_contact_object1 = Mock()
        mock_contact_object1.uuid = "123456"
        mock_contact_object1.fields = {
            "something": "special",
            "empty": "0",
            "some_date": "2018-05-17T00:00:00.000000+02:00",
        }
        mock_contact_object2 = Mock()
        mock_contact_object2.uuid = "7890123"
        mock_contact_object2.fields = {"something": "special", "empty": "1"}
        mock_contact_object3 = Mock()
        mock_contact_object3.uuid = "3210987"
        mock_contact_object3.fields = {"something": "different", "empty": "0"}
        mock_contact_object4 = Mock()
        mock_contact_object4.uuid = "621951621"
        mock_contact_object4.fields = {"something": "special"}
        # Iterfetches returns batches of returned objects
        mock_get_contacts.return_value.iterfetches.return_value = [
            [
                mock_contact_object1,
                mock_contact_object2,
                mock_contact_object3,
                mock_contact_object4,
            ]
        ]

        url = reverse("list_contacts", args=[self.org.pk])
        response = self.client.get("{}?something=special&empty=0".format(url))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_get_contacts.assert_called_once_with()
        self.assertEqual(response.json(), {"contacts": ["123456"]})

    @patch("temba_client.v2.TembaClient.get_contacts")
    def test_rp_and_non_rp_fields_filter(self, mock_get_contacts):
        """
        If both RP and non RP allowed query parameters are supplied, the RP ones should be
        passed to get contacts while the non RP ones are used to filter on fields
        """
        self.client.force_authenticate(self.user)

        # Create mock contacts
        mock_contact_object1 = Mock()
        mock_contact_object1.uuid = "123456"
        mock_contact_object1.fields = {
            "something": "special",
            "empty": "0",
            "some_date": "2018-05-17T00:00:00.000000+02:00",
        }
        mock_contact_object2 = Mock()
        mock_contact_object2.uuid = "7890123"
        mock_contact_object2.fields = {"something": "different", "empty": "1"}
        # Iterfetches returns batches of returned objects
        mock_get_contacts.return_value.iterfetches.return_value = [
            [mock_contact_object1, mock_contact_object2]
        ]

        url = reverse("list_contacts", args=[self.org.pk])
        response = self.client.get("{}?something=special&deleted=true".format(url))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_get_contacts.assert_called_once_with(**{"deleted": "true"})
        self.assertEqual(response.json(), {"contacts": ["123456"]})

    @patch("temba_client.clients.CursorIterator.__next__")
    def test_endpoint_forwards_some_http_errors(self, mock_next):
        """
        HTTP Connection errors should be caught and an error returned to the client
        """
        self.client.force_authenticate(self.user)

        # Iterfetches returns batches of returned objects
        mock_next.side_effect = TembaConnectionError()

        url = reverse("list_contacts", args=[self.org.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(
            response.json(),
            {
                "error": "An error occured fulfilling your request. You "
                "may have exceeded the rate limit. Please try again later."
            },
        )


class RapidproFlowsViewTests(SidekickAPITestCase):
    @responses.activate
    def test_get_rapidpro_flows(self):
        """
        Get flows from rapidpro
        """
        response_body = {
            "results": [
                {
                    "uuid": "flow-1-uuid",
                    "name": "Flow 1",
                },
                {
                    "uuid": "flow-2-uuid",
                    "name": "Flow 2",
                },
            ]
        }
        responses.add(
            responses.GET,
            "http://localhost:8002/api/v2/flows.json",
            json=response_body,
            status=200,
            match_querystring=True,
        )

        self.client.force_authenticate(self.user)

        url = reverse("rapidpro-flows", args=[self.org.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), response_body)


class RapidproContactViewTests(SidekickAPITestCase):
    @responses.activate
    def test_get_rapidpro_contact(self):
        """
        Get contact from rapidpro
        """

        response_body = {
            "results": [
                {
                    "uuid": "49e49903-5a4e-464c-9e6b-f93b6e845e2e",
                    "name": "Test Contact",
                    "fields": {
                        "whatsapp_consent": "TRUE",
                        "identification_type": "sa_id",
                        "public_messaging": "TRUE",
                        "loss_start_date": None,
                    },
                }
            ]
        }
        responses.add(
            responses.GET,
            "http://localhost:8002/api/v2/contacts.json",
            json=response_body,
            status=200,
            match_querystring=True,
        )

        self.client.force_authenticate(self.user)

        url = reverse("rapidpro-contact", args=[self.org.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json(), response_body)

    @responses.activate
    def test_get_rapidpro_contact_with_field_filter(self):
        """
        Get contact from rapidpro and filter fields
        """
        self.org.filter_rapidpro_fields = "whatsapp_consent,public_messaging"
        self.org.save()

        response_body = {
            "results": [
                {
                    "uuid": "49e49903-5a4e-464c-9e6b-f93b6e845e2e",
                    "name": "Test Contact",
                    "fields": {
                        "whatsapp_consent": "TRUE",
                        "identification_type": "sa_id",
                        "public_messaging": "TRUE",
                        "loss_start_date": None,
                    },
                }
            ]
        }
        responses.add(
            responses.GET,
            "http://localhost:8002/api/v2/contacts.json",
            json=response_body,
            status=200,
            match_querystring=True,
        )

        self.client.force_authenticate(self.user)

        url = reverse("rapidpro-contact", args=[self.org.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_body["results"][0]["fields"].pop("identification_type")
        response_body["results"][0]["fields"].pop("loss_start_date")

        self.assertEqual(response.json(), response_body)
