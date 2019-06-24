import json
from unittest.mock import Mock, patch

import pkg_resources
import responses
from django.test import TestCase
from django.utils import timezone

from sidekick import utils

from .utils import create_org


class UtilsTests(TestCase):
    def setUp(self):
        self.org = create_org()

    def assertCallMadeWith(self, call, **kwargs):
        """
        Check a sub-list of function calls, rather than the entire function call

        This is particularly useful when a Call contains a reference to self,
        which is difficult to reference in a test
        """
        call_args, call_kwargs = call

        if call_kwargs:
            missing_keys = []
            matching_keys_incorrect_value = []
            for key in kwargs:
                # get a list of all of the keywords that are _not_ in kwargs
                if key not in call_kwargs.keys():
                    missing_keys.append(key)
                # get a list of all of the keywords that do not have matching objects
                elif call_kwargs[key] != kwargs[key]:
                    matching_keys_incorrect_value.append(
                        (key, call_kwargs[key], kwargs[key])
                    )

            error_messages = []
            if any(missing_keys):
                error_messages.append("missing keyword args from call:")
                [
                    error_messages.append(f"\t{missing_key}")
                    for missing_key in missing_keys
                ]
            if any(matching_keys_incorrect_value):
                error_messages.append("incorrect args for given keyword:")
                [
                    error_messages.append(
                        f"{_key}:\n\texpected: {expected_value}\n\tactual: {actual_value}"
                    )
                    for _key, actual_value, expected_value in matching_keys_incorrect_value
                ]
            if error_messages:
                raise AssertionError("\n".join(error_messages))

    def test_get_today(self):

        self.assertEqual(utils.get_today(), timezone.now().date())

    def test_clean_message(self):

        self.assertEqual(
            utils.clean_message("No new lines\nNo tabs\t              No huge spaces"),
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
                    {"input": "+27820001001", "status": "valid", "wa_id": "27820001001"}
                ]
            },
            status=200,
        )

        self.assertEqual(
            utils.get_whatsapp_contact_id(self.org, "+27820001001"), "27820001001"
        )
        request = responses.calls[-1].request
        self.assertEqual(request.headers["Authorization"], "Bearer test-token")
        self.assertEqual(
            json.loads(request.body), {"blocking": "wait", "contacts": ["+27820001001"]}
        )

    @responses.activate
    def test_get_whatsapp_contact_id_not_exists(self):
        responses.add(
            method=responses.POST,
            url="http://whatsapp/v1/contacts",
            json={"contacts": [{"input": "+27820001001", "status": "invalid"}]},
            status=200,
        )

        self.assertEqual(utils.get_whatsapp_contact_id(self.org, "+27820001001"), None)
        request = responses.calls[-1].request
        self.assertEqual(request.headers["Authorization"], "Bearer test-token")
        self.assertEqual(
            json.loads(request.body), {"blocking": "wait", "contacts": ["+27820001001"]}
        )

    @patch("temba_client.v2.TembaClient.create_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.update_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("sidekick.utils.get_whatsapp_contact_id", autospec=True)
    def test_update_rapidpro_whatsapp_urn_no_wa_id(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_contacts,
        mock_update_contact,
        mock_create_contact,
    ):
        msisdn = "+27820001001"

        mock_get_whatsapp_contact_id.return_value = None

        utils.update_rapidpro_whatsapp_urn(self.org, msisdn)

        mock_get_whatsapp_contact_id.assert_called_with(self.org, msisdn)
        mock_get_contacts.assert_not_called()
        mock_update_contact.assert_not_called()
        mock_create_contact.assert_not_called()

    @patch("temba_client.v2.TembaClient.create_contact")
    @patch("temba_client.v2.TembaClient.update_contact")
    @patch("temba_client.v2.TembaClient.get_contacts")
    @patch("sidekick.utils.get_whatsapp_contact_id")
    def test_update_rapidpro_whatsapp_existing_contact_new_wa(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_contacts,
        mock_update_contact,
        mock_create_contact,
    ):
        MSISDN = "+27820001001"
        OLD_URNS = ["tel:{}".format(MSISDN)]

        NEW_WA_MSISDN = MSISDN.replace("+", "")
        NEW_URNS = ["tel:{}".format(MSISDN), "whatsapp:{}".format(NEW_WA_MSISDN)]

        UUID = "1234"

        # mock call to WhatsApp
        mock_get_whatsapp_contact_id.return_value = NEW_WA_MSISDN

        # set up mock responses from RapidPro
        mock_contact_object = Mock()
        mock_contact_object.uuid = UUID
        mock_contact_object.urns = OLD_URNS

        mock_get_contacts.return_value.first.return_value = mock_contact_object

        utils.update_rapidpro_whatsapp_urn(self.org, MSISDN)

        mock_get_whatsapp_contact_id.assert_called_once_with(self.org, MSISDN)

        self.assertEqual(mock_get_contacts.call_count, 1)
        self.assertCallMadeWith(
            mock_update_contact.call_args, contact=UUID, urns=NEW_URNS
        )

        mock_create_contact.assert_not_called()

    @patch("temba_client.v2.TembaClient.create_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.update_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("sidekick.utils.get_whatsapp_contact_id", autospec=True)
    def test_update_rapidpro_whatsapp_existing_contact_and_wa(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_contacts,
        mock_update_contact,
        mock_create_contact,
    ):
        """
        Contact exists and WA remain unchanged
        """
        UUID = "1234"
        MSISDN = "+27822222222"
        WA_MSISDN = MSISDN.replace("+", "")
        URNS = ["tel:{}".format(MSISDN), "whatsapp:{}".format(WA_MSISDN)]

        mock_get_whatsapp_contact_id.return_value = WA_MSISDN

        # return contact
        mock_contact_object = Mock()
        mock_contact_object.uuid = UUID
        mock_contact_object.urns = URNS
        mock_get_contacts.return_value.first.return_value = mock_contact_object

        utils.update_rapidpro_whatsapp_urn(self.org, MSISDN)

        # check function calls
        mock_get_whatsapp_contact_id.assert_called_once_with(self.org, MSISDN)
        mock_get_contacts.assert_called()
        mock_update_contact.assert_not_called()
        mock_create_contact.assert_not_called()

    @patch("temba_client.v2.TembaClient.create_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.update_contact", autospec=True)
    @patch("temba_client.v2.TembaClient.get_contacts", autospec=True)
    @patch("sidekick.utils.get_whatsapp_contact_id", autospec=True)
    def test_update_rapidpro_whatsapp_new_contact_and_wa(
        self,
        mock_get_whatsapp_contact_id,
        mock_get_contacts,
        mock_update_contact,
        mock_create_contact,
    ):
        MSISDN = "+27822222222"
        WA_MSISDN = MSISDN.replace("+", "")
        URNS = ["tel:{}".format(MSISDN), "whatsapp:{}".format(WA_MSISDN)]

        mock_get_whatsapp_contact_id.return_value = WA_MSISDN

        mock_get_contacts.return_value.first.side_effect = [None, None]

        utils.update_rapidpro_whatsapp_urn(self.org, MSISDN)

        self.assertEqual(mock_get_contacts.call_count, 2)
        # check each call was made to the client
        call_1, call_2 = mock_get_contacts.call_args_list
        self.assertCallMadeWith(call_1, urn=f"tel:{MSISDN}")
        self.assertCallMadeWith(call_2, urn=f"whatsapp:{WA_MSISDN}")

        mock_update_contact.assert_not_called()

        self.assertCallMadeWith(mock_create_contact.call_args, urns=URNS)

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

    @responses.activate
    def test_get_whatsapp_contact_messages(self):
        contact_id = "contact_1"

        data = {
            "messages": [
                {
                    "_vnd": {"v1": {"direction": "outbound"}},
                    "id": "ignore_id",
                    "timestamp": "1559793270",
                },
                {
                    "_vnd": {"v1": {"direction": "inbound"}},
                    "id": "return_id",
                    "timestamp": "1558692160",
                },
            ]
        }

        responses.add(
            method=responses.GET,
            url="http://whatsapp/v1/contacts/{}/messages".format(contact_id),
            json=data,
        )

        result = utils.get_whatsapp_contact_messages(self.org, contact_id)
        self.assertEqual(result, data)

    @responses.activate
    def test_label_whatsapp_message(self):
        message_id = "message_1"

        responses.add(
            method=responses.POST,
            url="http://whatsapp/v1/messages/{}/labels".format(message_id),
            json={},
        )

        result = utils.label_whatsapp_message(
            self.org, message_id, ["label1", "label2"]
        )
        self.assertEqual(result, {})

        request = responses.calls[-1].request
        self.assertEqual(json.loads(request.body), {"labels": ["label1", "label2"]})

    @responses.activate
    def test_archive_whatsapp_conversation(self):
        message_id = "message_1"
        wa_id = "contact_1"

        responses.add(
            method=responses.POST,
            url="http://whatsapp/v1/chats/{}/archive".format(wa_id),
            json={},
        )

        result = utils.archive_whatsapp_conversation(
            self.org, wa_id, message_id, "Test reason"
        )
        self.assertEqual(result, {})

        request = responses.calls[-1].request
        self.assertEqual(
            json.loads(request.body), {"before": message_id, "reason": "Test reason"}
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
