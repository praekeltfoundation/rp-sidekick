import uuid
from unittest.mock import Mock, patch
from urllib.parse import urlencode

from django.test import TestCase
from django.urls import reverse
from requests.exceptions import RequestException
from rest_framework import status
from temba_client.exceptions import TembaBadRequestError

from sidekick.tests.utils import assertCallMadeWith

from ..forms import SignupForm
from ..views import (
    MISSING_DATA_ERROR,
    RAPIDPRO_CREATE_OR_START_FAILURE,
    WA_CHECK_FORM_ERROR,
)
from .utils import create_recruitment


class TestRecruitViews(TestCase):
    def setUp(self):
        pass

    def test_recruit_view_get_404(self):
        url = reverse("recruit", kwargs={"recruitment_uuid": str(uuid.uuid4())})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_recruit_view_get_200(self):
        recruitment_campaign = create_recruitment()
        url = reverse("recruit", kwargs={"recruitment_uuid": recruitment_campaign.uuid})
        response = self.client.get(url)
        self.assertTrue(isinstance(response.context["form"], SignupForm))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_recruit_view_post_201(self):
        recruitment_campaign = create_recruitment()
        url = reverse("recruit", kwargs={"recruitment_uuid": recruitment_campaign.uuid})
        response = self.client.post(url)
        self.assertTrue(isinstance(response.context["form"], SignupForm))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch(
        "rp_recruit.views.get_whatsapp_contact_id",
        autospec=True,
        side_effect=RequestException(),
    )
    def test_recruit_view_post_500(self, fake_get_whatsapp_contact_id):
        recruitment_campaign = create_recruitment()
        url = reverse("recruit", kwargs={"recruitment_uuid": recruitment_campaign.uuid})

        response = self.client.post(
            url, {"msisdn": "+27821111111", "name": "test user"}
        )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFormError(response, "form", None, [WA_CHECK_FORM_ERROR])

    @patch("rp_recruit.views.get_whatsapp_contact_id", autospec=True, return_value=None)
    def test_recruit_view_post_400(self, mock_get_whatsapp_contact_id):

        recruitment_campaign = create_recruitment()
        msisdn = "+27821111111"
        mock_get_whatsapp_contact_id.return_value = None

        url = reverse("recruit", kwargs={"recruitment_uuid": recruitment_campaign.uuid})

        response = self.client.post(
            url, {"msisdn": "+27821111111", "name": "test user"}
        )
        self.assertFormError(
            response,
            "form",
            "msisdn",
            [f"{msisdn} is not a valid WhatsApp contact number"],
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("rp_recruit.views.get_whatsapp_contact_id", autospec=True, return_value=None)
    def test_recruit_view_post_400_rp_contact_exists(
        self, mock_get_whatsapp_contact_id, mock_get_contacts
    ):
        recruitment_campaign = create_recruitment()
        msisdn = "+27821111111"
        wa_id = msisdn.replace("+", "")

        mock_get_whatsapp_contact_id.return_value = wa_id
        mock_get_contacts.return_value.first.return_value = Mock("fake_contact_object")

        url = reverse("recruit", kwargs={"recruitment_uuid": recruitment_campaign.uuid})

        response = self.client.post(
            url, {"msisdn": "+27821111111", "name": "test user"}
        )

        self.assertFormError(
            response, "form", "msisdn", [f"{msisdn} is not a valid contact number"]
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        assertCallMadeWith(mock_get_contacts.call_args, urn=f"whatsapp:{wa_id}")

    @patch("rp_recruit.views.sentry_client.captureException", autospec=True)
    @patch("temba_client.v2.TembaClient.create_flow_start", autospec=True)
    @patch("temba_client.v2.TembaClient.create_contact", autospec=True)
    @patch("random.randint", autospec=True)
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("rp_recruit.views.get_whatsapp_contact_id", autospec=True, return_value=None)
    def test_recruit_view_post_500_rp_create_failure(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_contacts,
        mock_randint,
        mock_create_contact,
        mock_create_flow_start,
        mock_capture_exception,
    ):
        recruitment_campaign = create_recruitment()
        msisdn = "+27821111111"
        wa_id = msisdn.replace("+", "")
        test_name = "test user"
        pin = 1111

        mock_get_whatsapp_contact_id.return_value = wa_id
        mock_get_contacts.return_value.first.return_value = None
        mock_randint.return_value = pin
        mock_create_contact.side_effect = TembaBadRequestError(
            "rapidpro field does not exist"
        )

        url = reverse("recruit", kwargs={"recruitment_uuid": recruitment_campaign.uuid})

        response = self.client.post(url, {"msisdn": msisdn, "name": test_name})

        mock_capture_exception.assert_called_once()

        self.assertFormError(response, "form", None, [RAPIDPRO_CREATE_OR_START_FAILURE])
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        assertCallMadeWith(mock_get_contacts.call_args, urn=f"whatsapp:{wa_id}")
        assertCallMadeWith(
            mock_create_contact.call_args,
            name=test_name,
            urns=[f"whatsapp:{wa_id}"],
            groups=[recruitment_campaign.rapidpro_group_name],
            fields={recruitment_campaign.rapidpro_pin_key_name: pin},
        )
        mock_create_flow_start.assert_not_called()

    @patch("temba_client.v2.TembaClient.create_flow_start", autospec=True)
    @patch("temba_client.v2.TembaClient.create_contact", autospec=True)
    @patch("random.randint", autospec=True)
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("rp_recruit.views.get_whatsapp_contact_id", autospec=True, return_value=None)
    def test_recruit_view_post_300_success(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_contacts,
        mock_randint,
        mock_create_contact,
        mock_create_flow_start,
    ):
        recruitment_campaign = create_recruitment()
        msisdn = "+27821111111"
        wa_id = msisdn.replace("+", "")
        test_name = "joe blog"
        pin = 1111
        uuid = "1234"

        mock_get_whatsapp_contact_id.return_value = wa_id
        mock_get_contacts.return_value.first.return_value = None
        mock_randint.return_value = pin

        fake_contact = Mock()
        fake_contact.uuid = uuid
        mock_create_contact.return_value = fake_contact

        url = reverse("recruit", kwargs={"recruitment_uuid": recruitment_campaign.uuid})

        response = self.client.post(url, {"msisdn": msisdn, "name": test_name})
        expected_query_params = {"name": test_name, "pin": pin}
        expected_url = (
            f"{reverse('recruit_success')}?{urlencode(expected_query_params)}"
        )
        self.assertRedirects(
            response,
            expected_url=expected_url,
            status_code=302,
            target_status_code=200,
            fetch_redirect_response=True,
        )

        response_2 = self.client.get(expected_url)
        self.assertContains(response_2, test_name)
        self.assertContains(response_2, pin)

        assertCallMadeWith(mock_get_contacts.call_args, urn=f"whatsapp:{wa_id}")
        assertCallMadeWith(
            mock_create_contact.call_args,
            name=test_name,
            urns=[f"whatsapp:{wa_id}"],
            groups=[recruitment_campaign.rapidpro_group_name],
            fields={recruitment_campaign.rapidpro_pin_key_name: pin},
        )
        assertCallMadeWith(
            mock_create_flow_start.call_args,
            flow=str(recruitment_campaign.rapidpro_flow_uuid),
            urns=[f"whatsapp:{wa_id}"],
            restart_participants=False,
        )

    def test_recruit_view_get_success_error_400_no_args(self):
        response = self.client.get(reverse("recruit_success"))
        self.assertContains(
            response,
            MISSING_DATA_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            html=True,
        )

    def test_recruit_view_get_success_error_400_no_name(self):
        response = self.client.get(
            f"{reverse('recruit_success')}?{urlencode({'pin':'1234'})}"
        )
        self.assertContains(
            response,
            MISSING_DATA_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            html=True,
        )

    def test_recruit_view_get_success_error_400_no_pin(self):
        response = self.client.get(
            f"{reverse('recruit_success')}?{urlencode({'name':'foo'})}"
        )
        self.assertContains(
            response,
            MISSING_DATA_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            html=True,
        )
