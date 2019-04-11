import json

import pkg_resources
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

    def test_build_turn_headers(self):
        distribution = pkg_resources.get_distribution("rp-sidekick")

        headers = utils.build_turn_headers("FAKE_TOKEN")

        self.assertEqual(headers["Authorization"], "Bearer FAKE_TOKEN")
        self.assertEqual(
            headers["User-Agent"], "rp-sidekick/{}".format(distribution.version)
        )
        self.assertEqual(headers["Content-Type"], "application/json")

    @responses.activate
    def test_send_whatsapp_group_message(self):
        group_id = "group_1"
        message = "Hey!"

        responses.add(
            method=responses.POST,
            url="http://whatsapp/v1/messages",
            json={"messages": [{"id": "gBEGkYiEB1VXAglK1ZEqA1YKPrU"}]},
            status=200,
        )

        result = utils.send_whatsapp_group_message(self.org, group_id, message)

        self.assertEqual(result.status_code, 200)

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

    @responses.activate
    def test_create_whatsapp_group(self):
        responses.add(
            method=responses.POST,
            url="http://whatsapp/v1/groups",
            json={
                "groups": [
                    {
                        "creation_time": timezone.now().strftime(
                            "%Y-%m-%d %H:%M:%S %z"
                        ),
                        "id": "my-group-id",
                    }
                ]
            },
            status=200,
        )

        group_id = utils.create_whatsapp_group(self.org, "My Test Group")

        self.assertEqual(group_id, "my-group-id")

        self.assertEqual(len(responses.calls), 1)
        request = responses.calls[-1].request
        self.assertEqual(json.loads(request.body), {"subject": "My Test Group"})

    @responses.activate
    def test_get_whatsapp_group_invite_link(self):
        group_id = "group_1"

        responses.add(
            method=responses.GET,
            url="http://whatsapp/v1/groups/{}/invite".format(group_id),
            json={"groups": [{"link": "group-invite-link"}]},
            status=200,
        )

        link = utils.get_whatsapp_group_invite_link(self.org, group_id)

        self.assertEqual(link, "group-invite-link")

    @responses.activate
    def test_get_whatsapp_group_info(self):
        group_id = "group_1"
        group_info = {
            "admins": ["whatsapp-id-1", "whatsapp-id-2"],
            "creation_time": "",
            "creator": "whatsapp-id-1",
            "participants": ["whatsapp-id-3", "whatsapp-id-4", "whatsapp-id-5"],
            "subject": "your-group-subject",
        }

        responses.add(
            method=responses.GET,
            url="http://whatsapp/v1/groups/{}".format(group_id),
            json={"groups": [group_info]},
            status=200,
        )

        result = utils.get_whatsapp_group_info(self.org, group_id)

        self.assertEqual(result, group_info)

    @responses.activate
    def test_add_whatsapp_group_admin(self):
        group_id = "group_1"

        responses.add(
            method=responses.PATCH,
            url="http://whatsapp/v1/groups/{}/admins".format(group_id),
            json={},
            status=200,
        )

        result = utils.add_whatsapp_group_admin(self.org, group_id, "wa_id_1")

        self.assertEqual(json.loads(result.content), {})

        self.assertEqual(len(responses.calls), 1)
        request = responses.calls[-1].request
        self.assertEqual(json.loads(request.body), {"wa_ids": ["wa_id_1"]})

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
