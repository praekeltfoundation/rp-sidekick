import json

import responses
from django.test import TestCase
from django.utils import timezone
from mock import patch

from sidekick import utils

from .utils import create_org


class UtilsTests(TestCase):
    def setUp(self):
        self.org = create_org()

    def mock_rapidpro_contact_get(self, msisdn, count=1, wa_id=None):
        urns = ["tel:{}".format(msisdn)]
        if wa_id:
            urns.append("whatsapp:{}".format(wa_id))

        responses.add(
            method=responses.GET,
            url="http://localhost:8002/api/v2/contacts.json?urn=tel:{}".format(
                msisdn
            ),
            json={
                "count": count,
                "next": None,
                "previous": None,
                "results": [
                    {
                        "uuid": "bfff9984-38f4-4e59-998d-3663ec3c650d",
                        "name": "John Smith",
                        "language": None,
                        "group_uuids": ["04a4752b-0f49-480e-ae60-3a3f2bea485c"],
                        "urns": urns,
                        "fields": {"nickname": "Hannibal"},
                        "blocked": False,
                        "failed": False,
                        "stopped": False,
                        "modified_on": "2014-10-01T06:54:09.817Z",
                        "created_on": "2014-10-01T06:54:09.817Z",
                        "phone": "+27820001001",
                        "groups": [],
                    }
                ]
                * count,
            },
            status=200,
        )

    def mock_rapidpro_contact_post(self, msisdn, uuid=None, wa_id=None):
        urns = ["tel:{}".format(msisdn)]
        if wa_id:
            urns.append("whatsapp:{}".format(wa_id))

        url = "http://localhost:8002/api/v2/contacts.json"
        if uuid:
            url = "{}?uuid={}".format(url, uuid)

        responses.add(
            method=responses.POST,
            url=url,
            json={
                "uuid": "09d23a05-47fe-11e4-bfe9-b8f6b119e9ab",
                "name": "Ben Haggerty",
                "language": "eng",
                "urns": urns,
                "groups": [
                    {
                        "name": "Devs",
                        "uuid": "6685e933-26e1-4363-a468-8f7268ab63a9",
                    }
                ],
                "fields": {"nickname": "Macklemore", "side_kick": "Ryan Lewis"},
                "blocked": False,
                "stopped": False,
                "created_on": "2015-11-11T13:05:57.457742Z",
                "modified_on": "2015-11-11T13:05:57.576056Z",
            },
            status=200,
        )

    def test_get_today(self):

        self.assertEqual(utils.get_today(), timezone.now().date())

    def test_clean_message(self):

        self.assertEqual(
            utils.clean_message(
                "No new lines\nNo tabs\t              No huge spaces"
            ),
            "No new lines No tabs No huge spaces",
        )

    @responses.activate
    def test_get_whatsapp_contact_id_exists(self):
        responses.add(
            method=responses.POST,
            url="http://whatsapp/v1/contacts",
            json={
                "contacts": [
                    {
                        "input": "+27820001001",
                        "status": "valid",
                        "wa_id": "27820001001",
                    }
                ]
            },
            status=200,
        )

        self.assertEqual(
            utils.get_whatsapp_contact_id(self.org, "+27820001001"),
            "27820001001",
        )
        request = responses.calls[-1].request
        self.assertEqual(request.headers["Authorization"], "Bearer test-token")
        self.assertEqual(
            json.loads(request.body),
            {"blocking": "wait", "contacts": ["+27820001001"]},
        )

    @responses.activate
    def test_get_whatsapp_contact_id_not_exists(self):
        responses.add(
            method=responses.POST,
            url="http://whatsapp/v1/contacts",
            json={"contacts": [{"input": "+27820001001", "status": "invalid"}]},
            status=200,
        )

        self.assertEqual(
            utils.get_whatsapp_contact_id(self.org, "+27820001001"), None
        )
        request = responses.calls[-1].request
        self.assertEqual(request.headers["Authorization"], "Bearer test-token")
        self.assertEqual(
            json.loads(request.body),
            {"blocking": "wait", "contacts": ["+27820001001"]},
        )

    @responses.activate
    @patch("sidekick.utils.get_whatsapp_contact_id")
    def test_update_rapidpro_whatsapp_urn_no_wa_id(
        self, mock_get_whatsapp_contact_id
    ):
        msisdn = "+27820001001"

        mock_get_whatsapp_contact_id.return_value = None

        utils.update_rapidpro_whatsapp_urn(self.org, msisdn)

        self.assertEqual(len(responses.calls), 0)
        mock_get_whatsapp_contact_id.assert_called_with(self.org, msisdn)

    @responses.activate
    @patch("sidekick.utils.get_whatsapp_contact_id")
    def test_update_rapidpro_whatsapp_existing_contact_new_wa(
        self, mock_get_whatsapp_contact_id
    ):
        msisdn = "+27820001001"

        mock_get_whatsapp_contact_id.return_value = msisdn.replace("+", "")

        self.mock_rapidpro_contact_get(msisdn)
        self.mock_rapidpro_contact_post(
            msisdn, uuid="123", wa_id=msisdn.replace("+", "")
        )

        utils.update_rapidpro_whatsapp_urn(self.org, "+27820001001")

        self.assertEqual(len(responses.calls), 2)
        request = responses.calls[-1].request
        self.assertEqual(
            json.loads(request.body),
            {
                "urns": [
                    "tel:{}".format(msisdn),
                    "whatsapp:{}".format(msisdn.replace("+", "")),
                ]
            },
        )

    @responses.activate
    @patch("sidekick.utils.get_whatsapp_contact_id")
    def test_update_rapidpro_whatsapp_existing_contact_and_wa(
        self, mock_get_whatsapp_contact_id
    ):
        msisdn = "+27820001001"

        mock_get_whatsapp_contact_id.return_value = msisdn.replace("+", "")

        self.mock_rapidpro_contact_get(msisdn, wa_id=msisdn.replace("+", ""))
        self.mock_rapidpro_contact_post(
            msisdn, uuid="123", wa_id=msisdn.replace("+", "")
        )

        utils.update_rapidpro_whatsapp_urn(self.org, "+27820001001")

        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    @patch("sidekick.utils.get_whatsapp_contact_id")
    def test_update_rapidpro_whatsapp_new_contact_and_wa(
        self, mock_get_whatsapp_contact_id
    ):
        msisdn = "+27820001001"

        mock_get_whatsapp_contact_id.return_value = msisdn.replace("+", "")

        self.mock_rapidpro_contact_get(msisdn, count=0)
        self.mock_rapidpro_contact_post(msisdn, wa_id=msisdn.replace("+", ""))

        utils.update_rapidpro_whatsapp_urn(self.org, "+27820001001")

        self.assertEqual(len(responses.calls), 2)
        request = responses.calls[-1].request
        self.assertEqual(
            json.loads(request.body),
            {
                "urns": [
                    "tel:{}".format(msisdn),
                    "whatsapp:{}".format(msisdn.replace("+", "")),
                ]
            },
        )

    def test_clean_msisdn_1(self):
        self.assertEqual(utils.clean_msisdn("+2782653"), "2782653")

    def test_clean_msisdn_2(self):
        self.assertEqual(utils.clean_msisdn("2782653"), "2782653")

    def test_get_flow_url_1(self):
        base_url = "https://textit.io"
        flow_uuid = "1234-asdf"
        test_org = create_org(url=base_url)
        self.assertEqual(
            utils.get_flow_url(test_org, flow_uuid),
            "{}/flow/editor/{}".format(base_url, flow_uuid),
        )

    def test_get_flow_url_2(self):
        base_url = "https://textit.io/"
        flow_uuid = "1234-asdf"
        test_org = create_org(url=base_url)
        self.assertEqual(
            utils.get_flow_url(test_org, flow_uuid),
            "{}flow/editor/{}".format(base_url, flow_uuid),
        )
