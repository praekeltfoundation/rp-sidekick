import datetime
from collections import defaultdict

import responses
from django.test import TestCase
from django.test.utils import override_settings
from mock import ANY, call, patch

from rp_asos.models import Hospital, PatientRecord, PatientValue
from rp_asos.tasks import patient_data_check, create_hospital_groups
from sidekick import utils

from rp_redcap.tests.base import RedcapBaseTestCase


def override_get_today():
    return datetime.datetime.strptime("2018-06-06", "%Y-%m-%d").date()


class MockRedCapPatients(object):
    def export_metadata(self, forms=None):
        metadata = [
            {
                "field_name": "pre_op_field_1",
                "field_label": "Pre Field 1",
                "required_field": "y",
                "branching_logic": "",
            },
            {
                "field_name": "pre_op_field_2",
                "field_label": "Pre Field 2",
                "required_field": "y",
                "branching_logic": "",
            },
            {
                "field_name": "post_op_field_1",
                "field_label": "Post Field 1",
                "required_field": "y",
                "branching_logic": "",
            },
            {
                "field_name": "post_op_field_2",
                "field_label": "Post Field 2",
                "required_field": "y",
                "branching_logic": "",
            },
        ]

        return metadata

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
        if "'2018-01-16'" in filter_logic or "'2018-01-15'" in filter_logic:
            # test_get_reminders_no_errors
            if "screening_tool" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_eligible": "5",
                        "day1": "1",
                        "day2": "1",
                        "day3": "1",
                        "day4": "",
                        "day5": "1",
                        "redcap_data_access_group": "my_test_hospital",
                    }
                ]
            if "asos2_crf" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                        "pre_op_field_1": "value",
                        "pre_op_field_2": "value",
                        "post_op_field_1": "value",
                        "post_op_field_2": "value",
                    }
                ]
        elif "'2018-01-09'" in filter_logic or "'2018-01-08'" in filter_logic:
            # test_get_reminders_empty_screening_record
            if "screening_tool" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_eligible": "5",
                        "day1": "",
                        "day2": "",
                        "day3": "",
                        "day4": "",
                        "day5": "",
                        "redcap_data_access_group": "my_test_hospital",
                    }
                ]
        elif "'2018-02-20'" in filter_logic or "'2018-02-19'" in filter_logic:
            # test_get_reminders_no_screening_record
            if "screening_tool" in forms:
                return []
        elif "'2018-03-20'" in filter_logic or "'2018-03-19'" in filter_logic:
            # test_get_reminders_eligible_mismatch
            if "screening_tool" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_eligible": "6",
                        "day1": "1",
                        "day2": "2",
                        "day3": "1",
                        "day4": "1",
                        "day5": "1",
                        "redcap_data_access_group": "my_test_hospital",
                    }
                ]
            if "asos2_crf" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                        "pre_op_field_1": "value",
                        "pre_op_field_2": "value",
                        "post_op_field_1": "value",
                        "post_op_field_2": "value",
                    }
                ]
        elif "'2018-04-20'" in filter_logic or "'2018-04-16'" in filter_logic:
            # test_get_reminders_patients_incomplete
            if "screening_tool" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_eligible": "10",
                        "day1": "2",
                        "day2": "2",
                        "day3": "2",
                        "day4": "2",
                        "day5": "2",
                        "redcap_data_access_group": "my_test_hospital",
                    }
                ]
            if "asos2_crf" in forms:
                return [
                    {
                        "record_id": "1999-1",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                        "pre_op_field_1": "value",
                        "pre_op_field_2": "value",
                        "post_op_field_1": "value",
                        "post_op_field_2": "value",
                    },
                    {
                        "record_id": "1999-2",
                        "asos2_crf_complete": PatientRecord.INCOMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                        "pre_op_field_1": "",
                        "pre_op_field_2": "",
                        "post_op_field_1": "",
                        "post_op_field_2": "",
                    },
                ]
        elif "'2018-05-18'" in filter_logic or "'2018-05-14'" in filter_logic:
            # test_get_reminders_patients_multiple_hospitals
            if "screening_tool" in forms:
                return [
                    {
                        "record_id": "1",
                        "asos2_eligible": "10",
                        "day1": "2",
                        "day2": "2",
                        "day3": "2",
                        "day4": "2",
                        "day5": "2",
                        "redcap_data_access_group": "my_test_hospital",
                    },
                    {
                        "record_id": "1",
                        "asos2_eligible": "10",
                        "day1": "2",
                        "day2": "2",
                        "day3": "2",
                        "day4": "2",
                        "day5": "2",
                        "redcap_data_access_group": "another_hosp",
                    },
                ]
            if "asos2_crf" in forms:
                return [
                    {
                        "record_id": "1888-1",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                        "pre_op_field_1": "value",
                        "pre_op_field_2": "value",
                        "post_op_field_1": "value",
                        "post_op_field_2": "value",
                    },
                    {
                        "record_id": "1888-2",
                        "asos2_crf_complete": PatientRecord.INCOMPLETE_STATUS,
                        "redcap_data_access_group": "my_test_hospital",
                        "pre_op_field_1": "",
                        "pre_op_field_2": "",
                        "post_op_field_1": "",
                        "post_op_field_2": "",
                    },
                    {
                        "record_id": "1888-3",
                        "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                        "redcap_data_access_group": "another_hosp",
                        "pre_op_field_1": "value",
                        "pre_op_field_2": "value",
                        "post_op_field_1": "value",
                        "post_op_field_2": "value",
                    },
                ]
        return []


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
            hospital_lead_name="Tony Test",
            nomination_urn=nomination_urn,
            nomination_name="Peter Test",
        )

    def create_patient_records(self, date):
        patient_record = PatientRecord.objects.create(
            **{
                "project": self.project,
                "date": date,
                "record_id": "1",
                "pre_operation_status": PatientRecord.INCOMPLETE_STATUS,
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
    @patch("rp_asos.tasks.patient_data_check.get_reminders_for_date")
    @patch("rp_asos.tasks.patient_data_check.refresh_historical_data")
    @patch("rp_asos.tasks.patient_data_check.send_reminders")
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

        required_fields = {
            "pre_op_field_1": {"condition": "True", "label": "Pre Field 1"},
            "pre_op_field_2": {"condition": "True", "label": "Pre Field 2"},
            "post_op_field_1": {"condition": "True", "label": "Post Field 1"},
            "post_op_field_2": {"condition": "True", "label": "Post Field 2"},
        }

        calls = [
            call(
                date - datetime.timedelta(days=1),
                self.project,
                ANY,
                ANY,
                required_fields,
            ),
            call(
                date - datetime.timedelta(days=2),
                self.project,
                ANY,
                ANY,
                required_fields,
            ),
            call(
                date - datetime.timedelta(days=3),
                self.project,
                ANY,
                ANY,
                required_fields,
            ),
        ]
        mock_get_reminders_for_date.assert_has_calls(calls)
        self.assertEqual(len(mock_get_reminders_for_date.mock_calls), 3)

        mock_refresh_historical_data.assert_called_with(
            self.project, ANY, required_fields
        )

        mock_get_redcap_crf_client.assert_called_once()
        mock_get_redcap_client.assert_called_once()

        return_data[hospital][date].append("test notification")
        return_data[hospital][date].append("test notification")

        mock_send_reminders.assert_called_with(return_data, ANY, self.org)

    @override_settings(ASOS_HISTORICAL_DAYS=1)
    @patch("rp_redcap.models.Project.get_redcap_crf_client")
    @patch("rp_redcap.models.Project.get_redcap_client")
    @patch("rp_asos.tasks.patient_data_check.get_reminders_for_date")
    @patch("rp_asos.tasks.patient_data_check.refresh_historical_data")
    @patch("rp_asos.tasks.patient_data_check.send_reminders")
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

        required_fields = {
            "pre_op_field_1": {"condition": "True", "label": "Pre Field 1"},
            "pre_op_field_2": {"condition": "True", "label": "Pre Field 2"},
            "post_op_field_1": {"condition": "True", "label": "Post Field 1"},
            "post_op_field_2": {"condition": "True", "label": "Post Field 2"},
        }

        mock_get_reminders_for_date.assert_called_with(
            date - datetime.timedelta(days=1),
            self.project,
            ANY,
            ANY,
            required_fields,
        )
        self.assertEqual(len(mock_get_reminders_for_date.mock_calls), 1)

        mock_refresh_historical_data.assert_called_with(
            self.project, ANY, required_fields
        )

        mock_send_reminders.assert_called_with(return_data, ANY, self.org)

    def test_save_patient_records_existing(self):
        date = utils.get_today()

        # create records to update
        self.create_patient_records(date)

        # update records
        new_data = {
            "record_id": "1",
            "pre_operation_status": PatientRecord.COMPLETE_STATUS,
            "post_operation_status": PatientRecord.INCOMPLETE_STATUS,
            "field_one": "new_value",
            "missing_pre_op_fields": [],
            "missing_post_op_fields": [],
        }

        patient_data_check.save_patient_records(self.project, [new_data])

        # check
        patient_record = PatientRecord.objects.all()[0]
        patient_value = PatientValue.objects.all()[0]

        self.assertEqual(PatientValue.objects.all().count(), 1)

        self.assertEqual(
            patient_record.pre_operation_status, PatientRecord.COMPLETE_STATUS
        )
        self.assertEqual(
            patient_record.post_operation_status,
            PatientRecord.INCOMPLETE_STATUS,
        )
        self.assertEqual(patient_value.value, "new_value")

    def test_save_patient_records_existing_update(self):
        date = utils.get_today()

        # create records to update
        self.create_patient_records(date)

        # update records
        new_data = {
            "record_id": "1",
            "pre_operation_status": PatientRecord.COMPLETE_STATUS,
            "post_operation_status": PatientRecord.INCOMPLETE_STATUS,
            "field_one": "new_value",
        }

        patient_data_check.save_patient_records(self.project, [new_data])

        # check
        patient_record = PatientRecord.objects.all()[0]
        patient_value = PatientValue.objects.all()[0]

        self.assertEqual(
            patient_record.post_operation_status,
            PatientRecord.INCOMPLETE_STATUS,
        )
        self.assertEqual(patient_value.value, "new_value")

    def test_save_patient_records_new(self):
        date = utils.get_today()
        data = {
            "record_id": "1",
            "pre_operation_status": PatientRecord.COMPLETE_STATUS,
            "post_operation_status": PatientRecord.INCOMPLETE_STATUS,
            "field_one": "new_value",
        }

        patient_data_check.save_patient_records(self.project, [data], date)

        patient_record = PatientRecord.objects.all()[0]
        patient_value = PatientValue.objects.all()[0]

        self.assertEqual(
            patient_record.pre_operation_status, PatientRecord.COMPLETE_STATUS
        )
        self.assertEqual(patient_value.value, "new_value")

    @patch("rp_asos.tasks.patient_data_check.save_patient_records")
    def test_refresh_historical_data_no_records(
        self, mock_save_patient_records
    ):

        patient_data_check.refresh_historical_data(self.project, None, {})
        mock_save_patient_records.assert_not_called()

    @patch("rp_asos.tasks.patient_data_check.save_patient_records")
    def test_refresh_historical_data_with_records(
        self, mock_save_patient_records
    ):
        self.create_patient_records(utils.get_today())
        client = MockRedCapPatients()
        patient_data_check.refresh_historical_data(self.project, client, {})

        mock_save_patient_records.assert_called_with(
            self.project,
            [
                {
                    "record_id": 1,
                    "asos2_crf_complete": int(PatientRecord.COMPLETE_STATUS),
                    "field_one": "new_value",
                    "pre_operation_status": "2",
                    "post_operation_status": "2",
                    "missing_pre_op_fields": [],
                    "missing_post_op_fields": [],
                }
            ],
        )

    def test_get_reminders_no_errors(self):
        hospital = self.create_hospital()
        date = datetime.date(2018, 1, 16)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client, {}
        )

        self.assertEqual(messages[hospital][date], [])

    def test_get_reminders_no_screening_record(self):
        hospital = self.create_hospital()

        date = datetime.date(2018, 2, 20)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client, {}
        )

        check_messages = defaultdict(lambda: defaultdict(list))
        check_messages[hospital][date].append(
            "No screening records found.(2018-02-20)"
        )

        self.assertEqual(messages, check_messages)

    def test_get_reminders_empty_screening_record(self):
        hospital = self.create_hospital()

        date = datetime.date(2018, 1, 9)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client, {}
        )

        check_messages = defaultdict(lambda: defaultdict(list))
        check_messages[hospital][date].append(
            "No screening records found.(2018-01-09)"
        )

        self.assertEqual(messages, check_messages)

    def test_get_reminders_eligible_mismatch(self):
        hospital = self.create_hospital()
        date = datetime.date(2018, 3, 20)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client, {}
        )

        check_messages = defaultdict(lambda: defaultdict(list))
        check_messages[hospital][date].append("Not all patients captured.(1/2)")

        self.assertEqual(messages, check_messages)

    def test_get_reminders_patients_incomplete(self):
        hospital = self.create_hospital()

        date = datetime.date(2018, 4, 20)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date,
            self.project,
            screening_client,
            patient_client,
            {
                "pre_op_field_1": {"condition": "True", "label": "Pre Field 1"},
                "pre_op_field_2": {"condition": "True", "label": "Pre Field 2"},
                "post_op_field_1": {
                    "condition": "True",
                    "label": "Post Field 1",
                },
                "post_op_field_2": {
                    "condition": "True",
                    "label": "Post Field 2",
                },
            },
        )

        check_messages = defaultdict(lambda: defaultdict(list))
        check_messages[hospital][date].append(
            "1999-2: 2 preoperative, 2 postoperative fields missing"
        )
        self.assertEqual(messages, check_messages)

    def test_get_reminders_patients_multiple_hospitals(self):
        hospital1 = self.create_hospital()
        hospital2 = self.create_hospital(
            "Another Test Hospital", "another_hosp"
        )

        date = datetime.date(2018, 5, 18)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date,
            self.project,
            screening_client,
            patient_client,
            {
                "pre_op_field_1": {"condition": "True", "label": "Pre Field 1"},
                "pre_op_field_2": {"condition": "True", "label": "Pre Field 2"},
                "post_op_field_1": {
                    "condition": "True",
                    "label": "Post Field 1",
                },
                "post_op_field_2": {
                    "condition": "True",
                    "label": "Post Field 2",
                },
            },
        )

        self.assertEqual(
            messages[hospital1][date],
            ["1888-2: 2 preoperative, 2 postoperative fields missing"],
        )
        self.assertEqual(
            messages[hospital2][date], ["Not all patients captured.(1/2)"]
        )

    @patch("rp_asos.tasks.patient_data_check.get_redcap_records")
    def test_get_reminders_patients_weekend(self, mock_get_redcap_records):
        hospital = self.create_hospital()

        date = datetime.date(2018, 6, 17)
        screening_client = MockRedCapPatients()
        patient_client = MockRedCapPatients()

        messages = patient_data_check.get_reminders_for_date(
            date, self.project, screening_client, patient_client, {}
        )

        self.assertEqual(messages[hospital][date], [])
        mock_get_redcap_records.assert_not_called()

    @responses.activate
    @patch("rp_asos.models.Hospital.send_message")
    def test_send_reminders(self, mock_send_message):
        date = override_get_today()
        hospital = self.create_hospital()
        rapidpro_client = self.org.get_rapidpro_client()

        messages = defaultdict(lambda: defaultdict(list))
        messages[hospital][date].append("A test message")

        with patch("sidekick.utils.get_today", override_get_today):
            patient_data_check.send_reminders(
                messages, rapidpro_client, self.org
            )

        mock_send_message.assert_called_once()

    @responses.activate
    @patch("rp_asos.models.Hospital.send_message")
    def test_send_reminders_empty(self, mock_send_message):
        date = override_get_today()
        hospital = self.create_hospital(nomination_urn=None)
        rapidpro_client = self.org.get_rapidpro_client()

        messages = defaultdict(lambda: defaultdict(list))
        messages[hospital][date] = []

        patient_data_check.send_reminders(messages, rapidpro_client, self.org)

        mock_send_message.assert_not_called()

    def test_check_patients_status(self):

        patients = [
            {
                "record_id": "1999-1",
                "pre_op_field_1": "",
                "pre_op_field_2": "",
                "post_op_field_1": "",
                "post_op_field_2": "",
            }
        ]
        required_fields = {
            "pre_op_field_1": {
                "condition": 'data[row["record_id"]]["pre_op_field_1"] > 0',
                "label": "Pre Field 1",
            },
            "pre_op_field_2": {"condition": "True", "label": "Pre Field 2"},
            "post_op_field_1": {"condition": "True", "label": "Post Field 1"},
            "post_op_field_2": {"condition": "True", "label": "Post Field 2"},
        }

        patients = patient_data_check.check_patients_status(
            self.project, patients, required_fields
        )

        self.assertEqual(patients[0]["missing_pre_op_fields"], ["Pre Field 2"])
        self.assertEqual(
            patients[0]["missing_post_op_fields"],
            ["Post Field 1", "Post Field 2"],
        )


class CreateHospitalGroupsTaskTests(RedcapBaseTestCase, TestCase):
    def setUp(self):
        self.org = self.create_org()
        self.project = self.create_project(self.org)

    def create_hospital(self, nomination_urn="+27321", whatsapp_group_id=None):
        return Hospital.objects.create(
            name="Test Hospital One",
            project_id=self.project.id,
            data_access_group="my_test_hospital",
            rapidpro_flow="123123123",
            hospital_lead_urn="+27123",
            hospital_lead_name="Tony Test",
            nomination_urn=nomination_urn,
            nomination_name="Peter Test",
            whatsapp_group_id=whatsapp_group_id,
        )

    @patch("rp_asos.models.Hospital.create_hospital_wa_group")
    @patch("rp_asos.models.Hospital.get_wa_group_info")
    @patch("rp_asos.models.Hospital.send_group_invites")
    @patch("rp_asos.models.Hospital.add_group_admins")
    def test_create_hospitals_group_noop(
        self,
        mock_add_admins,
        mock_send_invites,
        mock_get_info,
        mock_create_group,
    ):
        create_hospital_groups(str(self.project.id))

        mock_add_admins.assert_not_called()
        mock_send_invites.assert_not_called()
        mock_get_info.assert_not_called()
        mock_create_group.assert_not_called()

    @patch("rp_asos.models.Hospital.create_hospital_wa_group")
    @patch("rp_asos.models.Hospital.get_wa_group_info")
    @patch("rp_asos.models.Hospital.send_group_invites")
    @patch("rp_asos.models.Hospital.add_group_admins")
    def test_create_hospitals_group_with_nomination(
        self,
        mock_add_admins,
        mock_send_invites,
        mock_get_info,
        mock_create_group,
    ):
        hospital = self.create_hospital(whatsapp_group_id="group-id-a")

        mock_create_group.return_value = hospital
        mock_get_info.return_value = {"id": "group-id-a"}

        create_hospital_groups(str(self.project.id))

        mock_create_group.assert_called_with()
        mock_get_info.assert_called_with()
        mock_send_invites.assert_called_with(
            {"id": "group-id-a"}, ["+27123", "+27321"]
        )
        mock_add_admins.assert_called_with(
            {"id": "group-id-a"}, ["+27123", "+27321"]
        )

    @patch("rp_asos.models.Hospital.create_hospital_wa_group")
    @patch("rp_asos.models.Hospital.get_wa_group_info")
    @patch("rp_asos.models.Hospital.send_group_invites")
    @patch("rp_asos.models.Hospital.add_group_admins")
    def test_create_hospitals_group_with_lead_only(
        self,
        mock_add_admins,
        mock_send_invites,
        mock_get_info,
        mock_create_group,
    ):
        hospital = self.create_hospital(
            nomination_urn=None, whatsapp_group_id="group-id-a"
        )

        mock_create_group.return_value = hospital
        mock_get_info.return_value = {"id": "group-id-a"}

        create_hospital_groups(str(self.project.id))

        mock_create_group.assert_called_with()
        mock_get_info.assert_called_with()
        mock_send_invites.assert_called_with({"id": "group-id-a"}, ["+27123"])
        mock_add_admins.assert_called_with({"id": "group-id-a"}, ["+27123"])
