from django.test import TestCase
from mock import patch
import responses
import json

from rp_redcap.models import Survey, Contact
from rp_redcap.tasks import survey_check


class MockRedCap(object):
    def export_metadata(self, forms=None):
        return [
            {
                "field_name": "name",
                "required_field": "y",
                "branching_logic": "",
            },  # noqa
            {
                "field_name": "email",
                "required_field": "y",
                "branching_logic": "[role(1)] = '1'",
            },  # noqa
            {
                "field_name": "surname",
                "required_field": "y",
                "branching_logic": "[role(0)] = '1' or [role(1)] = '1'",
            },  # noqa
        ]


class SurveyCheckTaskTests(TestCase):
    def mock_start_flow(self):
        responses.add(
            responses.POST,
            "http://localhost:8002/api/v2/flow_starts.json",
            json={
                "uuid": "09d23a05",
                "flow": {"uuid": "f5901b62", "name": "Send Reminder"},
                "groups": [{"uuid": "f5901b62", "name": "Investigators"}],
                "contacts": [{"uuid": "f5901b62", "name": "Ryan Lewis"}],
                "restart_participants": True,
                "status": "complete",
                "extra": {},
                "created_on": "2013-08-19T19:11:21.082Z",
                "modified_on": "2013-08-19T19:11:21.082Z",
            },
            status=200,
            match_querystring=True,
        )

    @responses.activate
    @patch("rp_redcap.tasks.survey_check.get_records")
    @patch("rp_redcap.tasks.survey_check.get_redcap_client")
    def test_survey_check(self, mock_get_redcap_client, mock_get_records):
        """
        Survey task test.

        The task should check for incomplete surveys and start a rapidpro flow
        for all the urns.
        """
        self.mock_start_flow()

        mock_get_records.return_value = [
            {"record_id": "1", "mobile": "+27123", "survey_1_complete": "2"},
            {"record_id": "2", "mobile": "+27234", "survey_1_complete": "0"},
            {"record_id": "3", "mobile": "", "survey_1_complete": "2"},
        ]

        Survey.objects.create(
            name="survey_1", rapidpro_flow="f5901b62", urn_field="mobile"
        )

        survey_check("survey_1")

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27123"],
                "extra": {"missing_fields": ""},
            },
        )

        self.assertEqual(Contact.objects.count(), 3)
        contact = Contact.objects.get(record_id=1)
        self.assertEqual(contact.urn, "tel:+27123")

    @responses.activate
    @patch("rp_redcap.tasks.survey_check.get_records")
    @patch("rp_redcap.tasks.survey_check.get_redcap_client")
    def test_survey_check_with_fields(
        self, mock_get_redcap_client, mock_get_records
    ):
        """
        Survey task test.

        The task should check for incomplete surveys and start a rapidpro flow
        for all the urns. The missing fields should be determined based on the
        metadata.
        """
        self.mock_start_flow()

        mock_get_records.return_value = [
            {
                "record_id": "1",
                "mobile": "+27123",
                "name": "",
                "role___0": "1",
                "role___1": "1",
                "email": "",
                "surname": "",
                "survey_1_complete": "2",
            },
            {
                "record_id": "2",
                "mobile": "+27234",
                "name": "",
                "role___0": "1",
                "role___1": "0",
                "email": "",
                "surname": "",
                "survey_1_complete": "2",
            },
        ]

        mock_get_redcap_client.return_value = MockRedCap()

        Survey.objects.create(
            name="survey_1",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            check_fields=True,
        )

        survey_check("survey_1")

        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27123"],
                "extra": {"missing_fields": "name, email, surname"},
            },
        )
        self.assertEqual(
            json.loads(responses.calls[1].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27234"],
                "extra": {"missing_fields": "name, surname"},
            },
        )
