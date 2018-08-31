from django.test import TestCase
from mock import patch
import datetime
import responses
import json

from rp_redcap.models import Survey, Contact, SurveyAnswer
from rp_redcap.tasks import project_check

from .base import RedcapBaseTestCase


def override_get_today():
    return datetime.datetime.strptime("2018-06-06", "%Y-%m-%d").date()


class MockRedCap(object):
    def export_metadata(self, forms=None):
        metadata = [
            {
                "field_name": "name",
                "field_label": "Name",
                "required_field": "y",
                "branching_logic": "",
            },
            {
                "field_name": "email",
                "field_label": "Email",
                "required_field": "y",
                "branching_logic": "[role(1)] = '1'",
            },
            {
                "field_name": "surname",
                "field_label": "Surname",
                "required_field": "y",
                "branching_logic": "[role(0)] = '1' or [role(1)] = '1'",
            },
            {
                "field_name": "follow_up",
                "field_label": "Follow Up",
                "required_field": "y",
                "branching_logic": "[role(1)] = '1'",
            },
            {
                "field_name": "consent",
                "field_label": "Consent?",
                "required_field": "y",
                "branching_logic": "",
            },
            {
                "field_name": "title",
                "field_label": "Title",
                "required_field": "",
                "branching_logic": "",
                "select_choices_or_calculations": "1, Ms | 2, Mr | 3, Dr | 4, Prof",  # noqa
            },
        ]

        if "survey_1" in forms:
            metadata.append(
                {
                    "field_name": "role",
                    "field_label": "Role",
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

        if "survey_3" in forms:
            return [
                {
                    "record_id": "1",
                    "mobile": "+27123",
                    "name": "Tony",
                    "role___0": "1",
                    "role___1": "1",
                    "email": "tony@test.com",
                    "surname": "Test",
                    "survey_3_complete": "0",
                }
            ]

        if "survey_2" in forms:
            return [
                {
                    "record_id": "1",
                    "follow_up": "",
                    "consent": "y",
                    "survey_2_complete": "0",
                },
                {
                    "record_id": "2",
                    "follow_up": "",
                    "consent": "",
                    "survey_2_complete": "0",
                },
            ]

        if "survey_ONE" in forms:
            return [
                {
                    "record_id": "1",
                    "survey_ONE_complete": "0",
                    "mobile": "+27123",
                    "role___0": "0",
                    "role___1": "0",
                    "name": "",
                }
            ]
        if "survey_TWO" in forms:
            return [
                {
                    "record_id": "1",
                    "follow_up": "",
                    "consent": "",
                    "survey_TWO_complete": "0",
                }
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
                "survey_A_complete": "0",
            },
            {
                "record_id": "2",
                "mobile": "+27234",
                "name": "",
                "role___0": "1",
                "role___1": "0",
                "email": "",
                "surname": "",
                "survey_A_complete": "0",
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
    @patch("rp_redcap.models.Project.get_redcap_client")
    def test_project_check_multiple_incomplete(self, mock_get_redcap_client):
        """
        Survey task test.

        The task should check for incomplete surveys and start a rapidpro flow
        for all the urns.
        """
        self.mock_start_flow()
        mock_get_redcap_client.return_value = MockRedCap()

        Survey.objects.create(
            name="survey_ONE",
            description="Survey One",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
            sequence=1,
        )

        Survey.objects.create(
            name="survey_TWO",
            description="Survey Two",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
            sequence=2,
        )

        with patch("sidekick.utils.get_today", override_get_today):
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
                    "missing_fields": "Survey One\nSurvey Two",
                    "missing_fields_count": "Survey One: 1 missing field\nSurvey Two: 1 missing field",  # noqa
                    "name": "",
                    "surname": "",
                    "title": "",
                    "role": "",
                    "week": 23,
                },
            },
        )

        self.assertEqual(Contact.objects.count(), 1)
        contact = Contact.objects.get(record_id=1)
        self.assertEqual(contact.urn, "tel:+27123")
        self.assertEqual(contact.project, self.project)

        self.assertEqual(SurveyAnswer.objects.count(), 3)

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
            description="Survey One",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
            sequence=1,
        )

        Survey.objects.create(
            name="survey_2",
            description="Survey Two",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
            sequence=2,
        )

        with patch("sidekick.utils.get_today", override_get_today):
            project_check(str(self.project.id))

        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27123"],
                "extra": {
                    "missing_fields_count": "Survey Two: 1 missing field",
                    "missing_fields": "Survey Two",
                    "project_name": "Test Project",
                    "role": "Investigator",
                    "name": "",
                    "surname": "",
                    "title": "",
                    "week": 23,
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
                    "missing_fields_count": "Survey Two: 1 missing field",
                    "missing_fields": "Survey Two",
                    "project_name": "Test Project",
                    "role": "Lead Investigator",
                    "name": "",
                    "surname": "",
                    "title": "",
                    "week": 23,
                },
            },
        )

        contact = Contact.objects.get(record_id=1)
        self.assertEqual(contact.role, "Investigator")

    @responses.activate
    @patch("rp_redcap.models.Project.get_redcap_client")
    def test_project_check_with_ignore_fields(self, mock_get_redcap_client):
        """
        Project task test with ignore_fields.

        The task should check for incomplete surveys and start a rapidpro flow
        for all the urns. The missing fields should be determined based on the
        metadata. Any required fields should be ignored if they are in the
        ignore_fields list.
        """
        self.mock_start_flow()

        mock_get_redcap_client.return_value = MockRedCap()

        Survey.objects.create(
            name="survey_A",
            description="Best Survey",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
            ignore_fields="surname, test_field",
        )

        with patch("sidekick.utils.get_today", override_get_today):
            project_check(str(self.project.id))

        self.assertEqual(len(responses.calls), 2)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "f5901b62",
                "restart_participants": 1,
                "urns": ["tel:+27123"],
                "extra": {
                    "missing_fields_count": "Best Survey: 1 missing field",
                    "missing_fields": "Best Survey",
                    "project_name": "Test Project",
                    "name": "Peter",
                    "surname": "",
                    "title": "Ms",
                    "role": "",
                    "week": 23,
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
                    "missing_fields_count": "Best Survey: 1 missing field",
                    "missing_fields": "Best Survey",
                    "project_name": "Test Project",
                    "name": "",
                    "surname": "",
                    "title": "",
                    "role": "",
                    "week": 23,
                },
            },
        )

    @responses.activate
    @patch("rp_redcap.models.Project.get_redcap_client")
    def test_project_check_no_missing(self, mock_get_redcap_client):
        """
        Project task no missing fields test.

        The task should not send a reminder if there are no missing fields.
        """
        self.mock_start_flow()

        mock_get_redcap_client.return_value = MockRedCap()

        Survey.objects.create(
            name="survey_3",
            description="Another Survey",
            rapidpro_flow="f5901b62",
            urn_field="mobile",
            project=self.project,
            sequence=1,
        )

        project_check(str(self.project.id))

        self.assertEqual(len(responses.calls), 0)

    def test_get_choices(self):

        metadata = [
            {
                "field_name": "role",
                "field_label": "Role",
                "required_field": "y",
                "branching_logic": "",
                "select_choices_or_calculations": "0, Lead (Investigator, Detective) | 1, Investigator",  # noqa
            }
        ]

        roles = project_check.get_choices(metadata, "role")

        self.assertEqual(roles["0"], "Lead (Investigator, Detective)")
        self.assertEqual(roles["1"], "Investigator")
