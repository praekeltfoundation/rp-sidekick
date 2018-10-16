import datetime
import json
from collections import defaultdict

import responses
from django.test import TestCase
from django.test.utils import override_settings
from mock import ANY, call, patch

from rp_redcap.models import (
    Contact,
    Hospital,
    PatientRecord,
    PatientValue,
    Survey,
    SurveyAnswer,
)
from rp_redcap.tasks import patient_data_check, project_check
from sidekick import utils

from .base import RedcapBaseTestCase


def override_get_today():
    return datetime.datetime.strptime("2018-06-06", "%Y-%m-%d").date()


class MockRedCapSurveys(object):
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


class MockRedCapPatients(object):
    def export_records(
        self,
        records=[],
        forms=[],
        export_survey_fields=True,
        export_data_access_groups=False,
        export_checkbox_labels=False,
        filter_logic=None,
    ):
        if records:
            # test_refresh_historical_data_with_records
            return [
                {
                    "record_id": "1",
                    "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                    "field_one": "new_value",
                }
            ]
        if "'2018-01-01'" in filter_logic:
            # test_get_reminders_no_errors
            if "screening_tool" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_eligible": 1,
                        "redcap_data_access_group": "my_test_hospital",
                    }
                ]
            if "asos2_crf" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                    }
                ]
        elif "'2018-01-02'" in filter_logic:
            # test_get_reminders_no_screening_record
            if "screening_tool" in forms:
                return []
        elif "'2018-01-03'" in filter_logic:
            # test_get_reminders_eligible_mismatch
            if "screening_tool" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_eligible": 2,
                        "redcap_data_access_group": "my_test_hospital",
                    }
                ]
            if "asos2_crf" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                    }
                ]
        elif "'2018-01-04'" in filter_logic:
            # test_get_reminders_patients_incomplete
            if "screening_tool" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_eligible": 2,
                        "redcap_data_access_group": "my_test_hospital",
                    }
                ]
            if "asos2_crf" in forms:
                return [
                    {
                        "record_id": "1999-1",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                    },
                    {
                        "record_id": "1999-2",
                        "asos2_crf_complete": PatientRecord.INCOMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                    },
                ]
        elif "'2018-01-05'" in filter_logic:
            # test_get_reminders_patients_multiple_hospitals
            if "screening_tool" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_eligible": 2,
                        "redcap_data_access_group": "my_test_hospital",
                    },
                    {
                        "record_id": "1",
                        "asos2_eligible": 2,
                        "redcap_data_access_group": "another_hosp",
                    },
                ]
            if "asos2_crf" in forms:
                return [
                    {
                        "record_id": "1888-1",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                    },
                    {
                        "record_id": "1888-2",
                        "asos2_crf_complete": PatientRecord.INCOMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                    },
                    {
                        "record_id": "1888-3",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "another_hosp",
                    },
                ]
        return []


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
        mock_get_redcap_client.return_value = MockRedCapSurveys()

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

        mock_get_redcap_client.return_value = MockRedCapSurveys()

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

        mock_get_redcap_client.return_value = MockRedCapSurveys()

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

        mock_get_redcap_client.return_value = MockRedCapSurveys()

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

    @responses.activate
    @patch("rp_redcap.tasks.project_check.get_records")
    @patch("rp_redcap.models.Project.get_redcap_client")
    def test_project_check_no_urn(
        self, mock_get_redcap_client, mock_get_records
    ):
        """
        Project task no missing fields test.

        The task should not send a reminder if the record/contact has no urn.
        """
        self.mock_start_flow()

        mock_get_redcap_client.return_value = MockRedCapSurveys()

        mock_get_records.return_value = [
            {
                "record_id": "1",
                "mobile": "",
                "survey_3_complete": "0",
                "name": "",
            }
        ]

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


class SurveyCheckPatientTaskTests(RedcapBaseTestCase, TestCase):
    def setUp(self):
        self.org = self.create_org()
        self.project = self.create_project(self.org)

    def create_hospital(
        self,
        name="My Test Hospital",
        dag="my_test_hospital",
        nomination_urn="+27321",
    ):
        return Hospital.objects.create(
            name=name,
            project_id=self.project.id,
            data_access_group=dag,
            rapidpro_flow="123123123",
            hospital_lead_urn="+27123",
            nomination_urn=nomination_urn,
        )

    def create_patient_records(self, date):
        patient_record = PatientRecord.objects.create(
            **{
                "project": self.project,
                "date": date,
                "record_id": "1",
                "status": PatientRecord.INCOMPLETE_STATUS,
            }
        )
        PatientValue.objects.create(
            **{
                "patient": patient_record,
                "name": "field_one",
                "value": "original_value",
            }
        )

    @patch("rp_redcap.models.Project.get_redcap_crf_client")
    @patch("rp_redcap.models.Project.get_redcap_client")
    @patch("rp_redcap.tasks.patient_data_check.get_reminders_for_date")
    @patch("rp_redcap.tasks.patient_data_check.refresh_historical_data")
    @patch("rp_redcap.tasks.patient_data_check.send_reminders")
    def test_patient_check(
        self,
        mock_send_reminders,
        mock_refresh_historical_data,
        mock_get_reminders_for_date,
        mock_get_redcap_client,
        mock_get_redcap_crf_client,
    ):
        hospital = self.create_hospital()
        date = override_get_today()

        return_data = defaultdict(lambda: defaultdict(list))
        return_data[hospital][date].append("test notification")
        mock_get_reminders_for_date.return_value = return_data

        mock_get_redcap_client.return_value = MockRedCapPatients()
        mock_get_redcap_crf_client.return_value = MockRedCapPatients()

        with patch("sidekick.utils.get_today", override_get_today):
            patient_data_check(str(self.project.id))

        calls = [
            call(date - datetime.timedelta(days=1), self.project, ANY, ANY),
            call(date - datetime.timedelta(days=2), self.project, ANY, ANY),
            call(date - datetime.timedelta(days=3), self.project, ANY, ANY),
        ]
        mock_get_reminders_for_date.assert_has_calls(calls)
        self.assertEqual(len(mock_get_reminders_for_date.mock_calls), 3)

        mock_refresh_historical_data.assert_called_with(self.project, ANY)

        mock_get_redcap_crf_client.assert_called_once()
        mock_get_redcap_client.assert_called_once()

        return_data[hospital][date].append("test notification")
        return_data[hospital][date].append("test notification")

        mock_send_reminders.assert_called_with(return_data, ANY)

    @override_settings(REDCAP_HISTORICAL_DAYS=1)
    @patch("rp_redcap.models.Project.get_redcap_crf_client")
    @patch("rp_redcap.models.Project.get_redcap_client")
    @patch("rp_redcap.tasks.patient_data_check.get_reminders_for_date")
    @patch("rp_redcap.tasks.patient_data_check.refresh_historical_data")
    @patch("rp_redcap.tasks.patient_data_check.send_reminders")
    def test_patient_check_one_day(
        self,
        mock_send_reminders,
        mock_refresh_historical_data,
        mock_get_reminders_for_date,
        mock_get_redcap_client,
        mock_get_redcap_crf_client,
    ):
        hospital = self.create_hospital()
        date = override_get_today()

        return_data = defaultdict(lambda: defaultdict(list))
        return_data[hospital][date].append("test notification")
        mock_get_reminders_for_date.return_value = return_data

        mock_get_redcap_client.return_value = MockRedCapPatients()
        mock_get_redcap_crf_client.return_value = MockRedCapPatients()

        with patch("sidekick.utils.get_today", override_get_today):
            patient_data_check(str(self.project.id))

        mock_get_reminders_for_date.assert_called_with(
            date - datetime.timedelta(days=1), self.project, ANY, ANY
        )
        self.assertEqual(len(mock_get_reminders_for_date.mock_calls), 1)

        mock_refresh_historical_data.assert_called_with(self.project, ANY)

        mock_send_reminders.assert_called_with(return_data, ANY)

    def test_save_patient_records_existing(self):
        date = utils.get_today()

        # create records to update
        self.create_patient_records(date)

        # update records
        new_data = {
            "record_id": "1",
            "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
            "field_one": "new_value",
        }

        patient_data_check.save_patient_records(self.project, [new_data])

        # check
        patient_record = PatientRecord.objects.all()[0]
        patient_value = PatientValue.objects.all()[0]

        self.assertEqual(patient_record.status, PatientRecord.COMPLETE_STATUS)
        self.assertEqual(patient_value.value, "new_value")

    def test_save_patient_records_new(self):
        date = utils.get_today()
        data = {
            "record_id": "1",
            "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
            "field_one": "new_value",
        }

        patient_data_check.save_patient_records(self.project, [data], date)

        patient_record = PatientRecord.objects.all()[0]
        patient_value = PatientValue.objects.all()[0]

        self.assertEqual(patient_record.status, PatientRecord.COMPLETE_STATUS)
        self.assertEqual(patient_value.value, "new_value")

    @patch("rp_redcap.tasks.patient_data_check.save_patient_records")
    def test_refresh_historical_data_no_records(
        self, mock_save_patient_records
    ):

        patient_data_check.refresh_historical_data(self.project, None)
        mock_save_patient_records.assert_not_called()

    @patch("rp_redcap.tasks.patient_data_check.save_patient_records")
    def test_refresh_historical_data_with_records(
        self, mock_save_patient_records
    ):
        self.create_patient_records(utils.get_today())
        client = MockRedCapPatients()
        patient_data_check.refresh_historical_data(self.project, client)

        mock_save_patient_records.assert_called_with(
            self.project,
            [
                {
                    "record_id": "1",
                    "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                    "field_one": "new_value",
                }
            ],
        )

    def test_get_reminders_no_errors(self):
        self.create_hospital()
        date = datetime.date(2018, 1, 1)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client
        )

        self.assertEqual(messages, defaultdict(list))

    def test_get_reminders_no_screening_record(self):
        hospital = self.create_hospital()

        date = datetime.date(2018, 1, 2)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client
        )

        check_messages = defaultdict(lambda: defaultdict(list))
        check_messages[hospital][date].append(
            "No screening records found.(2018-01-02)"
        )

        self.assertEqual(messages, check_messages)

    def test_get_reminders_eligible_mismatch(self):
        hospital = self.create_hospital()
        date = datetime.date(2018, 1, 3)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client
        )

        check_messages = defaultdict(lambda: defaultdict(list))
        check_messages[hospital][date].append("Not all patients captured.(1/2)")

        self.assertEqual(messages, check_messages)

    def test_get_reminders_patients_incomplete(self):
        hospital = self.create_hospital()

        date = datetime.date(2018, 1, 4)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client
        )

        check_messages = defaultdict(lambda: defaultdict(list))
        check_messages[hospital][date].append(
            "Incomplete patient data.(1999-2)"
        )

        self.assertEqual(messages, check_messages)

    def test_get_reminders_patients_multiple_hospitals(self):
        hospital1 = self.create_hospital()
        hospital2 = self.create_hospital(
            "Another Test Hospital", "another_hosp"
        )

        date = datetime.date(2018, 1, 5)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client
        )

        self.assertEqual(
            messages[hospital1][date], ["Incomplete patient data.(1888-2)"]
        )
        self.assertEqual(
            messages[hospital2][date], ["Not all patients captured.(1/2)"]
        )

    @responses.activate
    def test_send_reminders(self):
        date = override_get_today()
        hospital = self.create_hospital()
        rapidpro_client = self.org.get_rapidpro_client()

        messages = defaultdict(lambda: defaultdict(list))
        messages[hospital][date].append("A test message")

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

        patient_data_check.send_reminders(messages, rapidpro_client)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "123123123",
                "restart_participants": 1,
                "urns": ["tel:+27123", "tel:+27321"],
                "extra": {
                    "hospital_name": "My Test Hospital",
                    "week": 42,
                    "reminder": "2018-06-06\nA test message",
                },
            },
        )

    @responses.activate
    def test_send_reminders_no_nomination_urn(self):
        date = override_get_today()
        hospital = self.create_hospital(nomination_urn=None)
        rapidpro_client = self.org.get_rapidpro_client()

        messages = defaultdict(lambda: defaultdict(list))
        messages[hospital][date].append("A test message")

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

        patient_data_check.send_reminders(messages, rapidpro_client)

        self.assertEqual(len(responses.calls), 1)
        self.assertEqual(
            json.loads(responses.calls[0].request.body),
            {
                "flow": "123123123",
                "restart_participants": 1,
                "urns": ["tel:+27123"],
                "extra": {
                    "hospital_name": "My Test Hospital",
                    "week": 42,
                    "reminder": "2018-06-06\nA test message",
                },
            },
        )

    @responses.activate
    def test_send_reminders_empty(self):
        date = override_get_today()
        hospital = self.create_hospital(nomination_urn=None)
        rapidpro_client = self.org.get_rapidpro_client()

        messages = defaultdict(lambda: defaultdict(list))
        messages[hospital][date] = []

        patient_data_check.send_reminders(messages, rapidpro_client)

        self.assertEqual(len(responses.calls), 0)
