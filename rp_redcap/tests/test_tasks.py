from django.test import TestCase
from mock import patch
import responses
import json

from rp_redcap.models import Survey, Contact
from rp_redcap.tasks import project_check
from base import RedcapBaseTestCase


class MockRedCap(object):
    def export_metadata(self, forms=None):
        metadata = [
            {
                "field_name": "name",
                "required_field": "y",
                "branching_logic": "",
            },
            {
                "field_name": "email",
                "required_field": "y",
                "branching_logic": "[role(1)] = '1'",
            },
            {
                "field_name": "surname",
                "required_field": "y",
                "branching_logic": "[role(0)] = '1' or [role(1)] = '1'",
            },
            {
                "field_name": "follow_up",
                "required_field": "y",
                "branching_logic": "[role(1)] = '1'",
            },
            {
                "field_name": "title",
                "required_field": "",
                "branching_logic": "",
                "select_choices_or_calculations": "1, Ms | 2, Mr | 3, Dr | 4, Prof",  # noqa
            },
        ]

        if "survey_1" in forms:
            metadata.append(
                {
                    "field_name": "role",
                    "required_field": "y",
                    "branching_logic": "",
                    "select_choices_or_calculations": "0, Lead Investigator | 1, Investigator",  # noqa
                }
            )

        return metadata

    def export_records(
        self,
        forms=[],
        export_survey_fields=True,
        export_data_access_groups=False,
    ):
        if "survey_1" in forms:
            return [
                {
                    "record_id": "1",
                    "mobile": "+27123",
                    "name": "",
                    "role___0": "1",
                    "role___1": "1",
                    "email": "",
                    "surname": "",
                    "survey_1_complete": "0",
                },
                {
                    "record_id": "2",
                    "mobile": "+27234",
                    "name": "",
                    "role___0": "1",
                    "role___1": "0",
                    "email": "",
                    "surname": "",
                    "survey_1_complete": "0",
                },
            ]

        if "survey_2" in forms:
            return [
                {"record_id": "1", "follow_up": "", "survey_2_complete": "2"},
                {"record_id": "2", "follow_up": "", "survey_2_complete": "2"},
            ]

        return [
            {
                "record_id": "1",
                "mobile": "+27123",
                "name": "Peter",
                "title": "1",
                "role___0": "1",
                "role___1": "1",
                "email": "",
                "surname": "",
                "survey_A_complete": "2",
            },
            {
                "record_id": "2",
                "mobile": "+27234",
                "name": "",
                "role___0": "1",
                "role___1": "0",
                "email": "",
                "surname": "",
                "survey_A_complete": "2",
            },
        ]


class SurveyCheckTaskTests(RedcapBaseTestCase, TestCase):
    def setUp(self):
        self.org = self.create_org()
        self.project = self.create_project(self.org)

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
    @patch("rp_redcap.tasks.project_check.get_records")
    @patch("rp_redcap.models.Project.get_redcap_client")
    def test_project_check(self, mock_get_redcap_client, mock_get_records):
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
            name="survey_1",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
        )

        project_check(str(self.project.id))

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27123"],
                "extra": {
                    "project_name": "Test Project",
                    "survey_name": "survey_1",
                    "name": None,
                    "title": None,
                    "role": None,
                },
            },
        )

        self.assertEqual(Contact.objects.count(), 3)
        contact = Contact.objects.get(record_id=1)
        self.assertEqual(contact.urn, "tel:+27123")
        self.assertEqual(contact.project, self.project)

    @responses.activate
    @patch("rp_redcap.models.Project.get_redcap_client")
    def test_project_check_with_fields(self, mock_get_redcap_client):
        """
        Project task test.

        The task should check for incomplete surveys and start a rapidpro flow
        for all the urns. The missing fields should be determined based on the
        metadata.
        """
        self.mock_start_flow()

        mock_get_redcap_client.return_value = MockRedCap()

        Survey.objects.create(
            name="survey_A",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
            check_fields=True,
        )

        project_check(str(self.project.id))

        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27123"],
                "extra": {
                    "missing_fields": "email, surname",
                    "project_name": "Test Project",
                    "survey_name": "survey_A",
                    "name": "Peter",
                    "title": "Ms",
                    "role": None,
                },
            },
        )
        self.assertEqual(
            json.loads(responses.calls[1].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27234"],
                "extra": {
                    "missing_fields": "name, surname",
                    "project_name": "Test Project",
                    "survey_name": "survey_A",
                    "name": None,
                    "title": None,
                    "role": None,
                },
            },
        )

    @responses.activate
    @patch("rp_redcap.models.Project.get_redcap_client")
    def test_project_check_multiple_surveys(self, mock_get_redcap_client):
        """
        Project task test.

        The task should check for incomplete surveys and start a rapidpro flow
        for all the urns. The missing fields should be determined based on the
        metadata, this could be based on values in previous surveys.
        """
        self.mock_start_flow()

        mock_get_redcap_client.return_value = MockRedCap()

        Survey.objects.create(
            name="survey_1",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
            check_fields=True,
            sequence=1,
        )

        Survey.objects.create(
            name="survey_2",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
            check_fields=True,
            sequence=2,
        )

        project_check(str(self.project.id))

        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27123"],
                "extra": {
                    "missing_fields": "follow_up",
                    "project_name": "Test Project",
                    "survey_name": "survey_2",
                    "role": "Investigator",
                    "name": None,
                    "title": None,
                },
            },
        )
        self.assertEqual(
            json.loads(responses.calls[1].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27234"],
                "extra": {
                    "missing_fields": "",
                    "project_name": "Test Project",
                    "survey_name": "survey_2",
                    "role": "Lead Investigator",
                    "name": None,
                    "title": None,
                },
            },
        )

        contact = Contact.objects.get(record_id=1)
        self.assertEqual(contact.role, "Investigator")
