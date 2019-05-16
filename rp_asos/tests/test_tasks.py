import datetime
from freezegun import freeze_time
from mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from rp_asos.models import (
    Hospital,
    PatientRecord,
    PatientValue,
    ScreeningRecord,
)
from rp_asos.tasks import (
    patient_data_check,
    create_hospital_groups,
    screening_record_check,
)
from sidekick import utils

from rp_redcap.tests.base import RedcapBaseTestCase

SCREENING_RECORD_TEMPLATE = {}
for i in range(1, 29):
    SCREENING_RECORD_TEMPLATE["day{}".format(i)] = "1"
for i in range(1, 5):
    SCREENING_RECORD_TEMPLATE["week_{}_case_count".format(i)] = "7"


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
        if "screening_tool" in forms:

            record1 = SCREENING_RECORD_TEMPLATE.copy()
            record1.update(
                {
                    "record_id": "1",
                    "date": "2018-06-06",
                    "day4": "",
                    "week_1_case_count": "6",
                    "redcap_data_access_group": "my_test_hospital",
                }
            )

            record2 = SCREENING_RECORD_TEMPLATE.copy()
            record2.update(
                {
                    "record_id": "1",
                    "date": "2017-06-06",
                    "day4": "",
                    "week_1_case_count": "6",
                    "redcap_data_access_group": "other_hospital",
                }
            )

            return [record1, record2]
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
                    "date_surg": "2018-11-20",
                },
                {
                    "record_id": "1",
                    "asos2_crf_complete": PatientRecord.COMPLETE_STATUS,
                    "redcap_data_access_group": "other_hospital",
                    "pre_op_field_1": "value",
                    "pre_op_field_2": "value",
                    "post_op_field_1": "value",
                    "post_op_field_2": "value",
                    "date_surg": "2017-11-20",
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
        tz_code="CAT",
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
            tz_code=tz_code,
        )

    def create_patient_records(self, date, hospital, record_id="1"):
        patient_record = PatientRecord.objects.create(
            **{
                "project": self.project,
                "hospital": hospital,
                "date": date,
                "record_id": record_id,
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
        return patient_record

    @patch("rp_asos.tasks.patient_data_check.save_all_data_from_redcap")
    @patch("rp_asos.models.Hospital.send_message")
    def test_patient_check_no_data(
        self, mock_send_message, mock_save_all_data_from_redcap
    ):
        self.create_hospital()

        patient_data_check(
            {"project_id": str(self.project.id), "tz_code": "CAT"}
        )

        message = (
            "Daily data update for My Test Hospital:\n"
            "0 eligible operations have been reported on your screening log.\n"
            "The screening log has not been updated.\n"
            "Please update your screening log today or WhatsApp us if "
            "there is a problem.\n\n"
            "0 CRFs have been captured on REDCap.\n"
            "0 CRFs have incomplete data fields.\n"
            "The following CRFs have incomplete data fields on REDCap:\n"
        )

        mock_send_message.assert_called_with(message)
        mock_save_all_data_from_redcap.assert_called_with(self.project, "CAT")

    @freeze_time("2019-01-01")
    @patch("rp_asos.tasks.patient_data_check.save_all_data_from_redcap")
    @patch("rp_asos.models.Hospital.send_message")
    def test_patient_check_with_data(
        self, mock_send_message, mock_save_all_data_from_redcap
    ):
        hospital = self.create_hospital()

        ScreeningRecord.objects.create(
            **{
                "hospital": hospital,
                "date": datetime.date(2019, 1, 16),
                "total_eligible": 2,
            }
        )

        self.create_patient_records(datetime.date(2018, 1, 16), hospital)
        patient = self.create_patient_records(
            datetime.date(2018, 1, 16), hospital, "2"
        )
        self.create_patient_records(datetime.date(2018, 1, 16), hospital, "3")

        patient.pre_operation_status = PatientRecord.COMPLETE_STATUS
        patient.post_operation_status = PatientRecord.COMPLETE_STATUS
        patient.save()

        patient_data_check(
            {"project_id": str(self.project.id), "tz_code": "CAT"}
        )

        message = (
            "Daily data update for My Test Hospital:\n"
            "2 eligible operations have been reported on your screening log.\n"
            "The last screening log update was on 01 January 2019.\n\n"
            "3 CRFs have been captured on REDCap.\n"
            "2 CRFs have incomplete data fields.\n"
            "The following CRFs have incomplete data fields on REDCap:\n"
            "1; 3"
        )

        mock_send_message.assert_called_with(message)
        mock_save_all_data_from_redcap.assert_called_with(self.project, "CAT")

    @freeze_time("2019-02-01")
    @patch("rp_asos.models.Hospital.check_and_update_status")
    @patch("rp_asos.tasks.patient_data_check.save_all_data_from_redcap")
    @patch("rp_asos.models.Hospital.send_message")
    def test_patient_check_with_data_no_warning(
        self,
        mock_send_message,
        mock_save_all_data_from_redcap,
        mock_check_and_update_status,
    ):
        hospital = self.create_hospital()

        ScreeningRecord.objects.create(
            **{
                "hospital": hospital,
                "date": datetime.date(2019, 1, 16),
                "total_eligible": 2,
            }
        )
        ScreeningRecord.objects.all().update(
            updated_at=datetime.datetime(2018, 12, 20, tzinfo=timezone.utc)
        )

        self.create_patient_records(datetime.date(2018, 1, 16), hospital)
        patient = self.create_patient_records(
            datetime.date(2018, 1, 16), hospital, "2"
        )
        self.create_patient_records(datetime.date(2018, 1, 16), hospital, "3")

        patient.pre_operation_status = PatientRecord.COMPLETE_STATUS
        patient.post_operation_status = PatientRecord.COMPLETE_STATUS
        patient.save()

        patient_data_check(
            {"project_id": str(self.project.id), "tz_code": "CAT"}
        )

        message = (
            "Daily data update for My Test Hospital:\n"
            "2 eligible operations have been reported on your screening log.\n"
            "The last screening log update was on 20 December 2018.\n"
            "Please update your screening log today or WhatsApp us if "
            "there is a problem.\n\n"
            "3 CRFs have been captured on REDCap.\n"
            "2 CRFs have incomplete data fields.\n"
            "The following CRFs have incomplete data fields on REDCap:\n"
            "1; 3"
        )

        mock_check_and_update_status.assert_called_once()
        mock_send_message.assert_called_with(message)
        mock_save_all_data_from_redcap.assert_called_with(self.project, "CAT")

    def test_save_patient_records_existing(self):
        date = utils.get_today()

        hospital = self.create_hospital()

        # create records to update
        self.create_patient_records(date, hospital)

        # update records
        new_data = {
            "record_id": "1",
            "pre_operation_status": PatientRecord.COMPLETE_STATUS,
            "post_operation_status": PatientRecord.INCOMPLETE_STATUS,
            "field_one": "new_value",
            "missing_pre_op_fields": [],
            "missing_post_op_fields": [],
            "redcap_data_access_group": "my_test_hospital",
            "date_surg": "2018-10-24",
        }

        patient_data_check.save_patient_records(
            self.project, hospital, [new_data]
        )

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

        hospital = self.create_hospital()

        # create records to update
        self.create_patient_records(date, hospital)

        # update records
        new_data = {
            "record_id": "1",
            "pre_operation_status": PatientRecord.COMPLETE_STATUS,
            "post_operation_status": PatientRecord.INCOMPLETE_STATUS,
            "field_one": "new_value",
            "redcap_data_access_group": "my_test_hospital",
            "date_surg": "2018-10-24",
        }

        patient_data_check.save_patient_records(
            self.project, hospital, [new_data]
        )

        # check
        patient_record = PatientRecord.objects.all()[0]
        patient_value = PatientValue.objects.all()[0]

        self.assertEqual(
            patient_record.post_operation_status,
            PatientRecord.INCOMPLETE_STATUS,
        )
        self.assertEqual(patient_value.value, "new_value")

    def test_save_patient_records_new(self):
        hospital = self.create_hospital()
        data = {
            "record_id": "1",
            "pre_operation_status": PatientRecord.COMPLETE_STATUS,
            "post_operation_status": PatientRecord.INCOMPLETE_STATUS,
            "field_one": "new_value",
            "redcap_data_access_group": "my_test_hospital",
            "date_surg": "",
        }

        patient_data_check.save_patient_records(self.project, hospital, [data])

        patient_record = PatientRecord.objects.all()[0]
        patient_value = PatientValue.objects.all()[0]

        self.assertEqual(
            patient_record.pre_operation_status, PatientRecord.COMPLETE_STATUS
        )
        self.assertEqual(patient_value.value, "new_value")

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

    def test_save_screening_records_empty(self):
        hospital = self.create_hospital()

        patient_data_check.save_screening_records(hospital, [])

        self.assertEqual(ScreeningRecord.objects.all().count(), 0)

    def test_save_screening_records_existing(self):
        hospital = self.create_hospital()

        date = datetime.datetime.strptime("2018-06-06", "%Y-%m-%d").date()

        ScreeningRecord.objects.create(hospital=hospital, date=date)

        record = SCREENING_RECORD_TEMPLATE.copy()
        record.update(
            {
                "date": "",
                "day2": "",
                "day3": "",
                "week_1_case_count": "4",
                "week_4_case_count": "",
            }
        )

        patient_data_check.save_screening_records(hospital, [record])

        screening_record = ScreeningRecord.objects.all()[0]
        self.assertEqual(ScreeningRecord.objects.all().count(), 1)
        self.assertEqual(screening_record.total_eligible, 26)
        self.assertEqual(screening_record.week_1_case_count, 4)
        self.assertEqual(screening_record.week_2_case_count, 7)
        self.assertEqual(screening_record.date, date)

    def test_save_screening_records_updated_at(self):
        hospital = self.create_hospital()
        date = datetime.datetime.strptime("2018-06-06", "%Y-%m-%d").date()
        screening_record = ScreeningRecord.objects.create(
            hospital=hospital,
            date=date,
            week_1_case_count=7,
            week_2_case_count=7,
            week_3_case_count=7,
            week_4_case_count=7,
            total_eligible=28,
        )

        ScreeningRecord.objects.all().update(
            updated_at=datetime.datetime(2019, 1, 9, tzinfo=timezone.utc)
        )

        # nothing changes, updated_at should stay the same
        record = SCREENING_RECORD_TEMPLATE.copy()
        record.update({"date": "2018-06-06"})
        patient_data_check.save_screening_records(hospital, [record])

        screening_record = ScreeningRecord.objects.all()[0]
        self.assertEqual(ScreeningRecord.objects.all().count(), 1)
        self.assertEqual(
            screening_record.updated_at,
            datetime.datetime(2019, 1, 9, tzinfo=timezone.utc),
        )

        # something will change, updated_at should have new timestamp
        record.update({"day1": "100"})
        patient_data_check.save_screening_records(hospital, [record])

        screening_record = ScreeningRecord.objects.all()[0]
        self.assertEqual(ScreeningRecord.objects.all().count(), 1)
        self.assertNotEqual(
            screening_record.updated_at,
            datetime.datetime(2019, 1, 9, tzinfo=timezone.utc),
        )

    def test_save_screening_records_new(self):
        hospital = self.create_hospital()

        record = SCREENING_RECORD_TEMPLATE.copy()
        record.update(
            {
                "date": "2018-06-06",
                "day2": "",
                "day3": "",
                "day4": "",
                "day5": "",
                "week_1_case_count": "3",
            }
        )

        patient_data_check.save_screening_records(hospital, [record])

        self.assertEqual(ScreeningRecord.objects.all().count(), 1)

        screening_record = ScreeningRecord.objects.all()[0]
        self.assertEqual(screening_record.total_eligible, 24)
        self.assertEqual(screening_record.week_1_case_count, 3)
        self.assertEqual(screening_record.week_2_case_count, 7)
        self.assertEqual(screening_record.date, datetime.date(2018, 6, 6))

    @patch("rp_redcap.models.Project.get_redcap_crf_client")
    @patch("rp_redcap.models.Project.get_redcap_client")
    def test_save_all_data_from_redcap(
        self, mock_get_redcap_client, mock_get_redcap_crf_client
    ):
        hospital = self.create_hospital()

        mock_get_redcap_client.return_value = MockRedCapPatients()
        mock_get_redcap_crf_client.return_value = MockRedCapPatients()

        patient_data_check.save_all_data_from_redcap(self.project, "CAT")

        mock_get_redcap_client.assert_called_once()

        self.assertEqual(ScreeningRecord.objects.all().count(), 1)
        self.assertEqual(PatientRecord.objects.all().count(), 1)
        self.assertEqual(PatientValue.objects.all().count(), 4)

        screening = ScreeningRecord.objects.all()[0]
        self.assertEqual(screening.hospital.id, hospital.id)
        self.assertEqual(screening.total_eligible, 27)
        self.assertEqual(screening.date, datetime.date(2018, 6, 6))

        patient = PatientRecord.objects.all()[0]
        self.assertEqual(patient.hospital.id, hospital.id)
        self.assertEqual(patient.date, datetime.date(2018, 11, 20))

        for field in [
            "pre_op_field_1",
            "pre_op_field_2",
            "post_op_field_1",
            "post_op_field_2",
        ]:
            self.assertEqual(
                PatientValue.objects.filter(name=field, value="value").count(),
                1,
            )


class CreateHospitalGroupsTaskTests(RedcapBaseTestCase, TestCase):
    def setUp(self):
        self.org = self.create_org()
        self.project = self.create_project(self.org)

    def create_hospital(
        self, nomination_urn="+27321", whatsapp_group_id=None, tz_code="CAT"
    ):
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
            tz_code=tz_code,
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
        self.create_hospital(tz_code="NOT_CAT")

        create_hospital_groups(str(self.project.id), "CAT")

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
        mock_send_invites.return_value = ["+27123", "+27321"]

        create_hospital_groups(str(self.project.id), "CAT")

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
        mock_send_invites.return_value = ["+27123"]

        create_hospital_groups(str(self.project.id), "CAT")

        mock_create_group.assert_called_with()
        mock_get_info.assert_called_with()
        mock_send_invites.assert_called_with({"id": "group-id-a"}, ["+27123"])
        mock_add_admins.assert_called_with({"id": "group-id-a"}, ["+27123"])


class ScreeningRecordTaskTests(RedcapBaseTestCase, TestCase):
    def setUp(self):
        self.org = self.create_org()
        project = self.create_project(self.org)

        self.hospitals = []
        for i in range(0, 2):
            self.hospitals.append(
                Hospital.objects.create(
                    name="Test Hospital {}".format(i),
                    project_id=project.id,
                    data_access_group="test",
                    hospital_lead_urn="+27123",
                    hospital_lead_name="Tony Test",
                    is_active=i == 0,
                )
            )

    def create_screening_record(self):
        for hospital in self.hospitals:
            ScreeningRecord.objects.create(
                **{
                    "hospital": hospital,
                    "date": datetime.date(2019, 1, 16),
                    "total_eligible": 2,
                }
            )

        ScreeningRecord.objects.all().update(
            updated_at=datetime.datetime(2019, 1, 9, tzinfo=timezone.utc)
        )

    @freeze_time("2019-01-13")
    @patch("sidekick.utils.send_whatsapp_group_message")
    def test_screening_record_check_not_updated(self, mock_send_group):
        self.create_screening_record()

        screening_record_check(self.org.id)

        mock_send_group.assert_called_with(
            self.org,
            settings.ASOS_ADMIN_GROUP_ID,
            "Hospitals with outdated screening records:\nTest Hospital 0",
        )

    @freeze_time("2019-01-10")
    @patch("sidekick.utils.send_whatsapp_group_message")
    def test_screening_record_check_updated(self, mock_send_group):
        self.create_screening_record()
        screening_record_check(self.org.id)

        mock_send_group.assert_not_called()

    @patch("sidekick.utils.send_whatsapp_group_message")
    def test_screening_record_check_no_screening_record(self, mock_send_group):
        screening_record_check(self.org.id)

        mock_send_group.assert_called_with(
            self.org,
            settings.ASOS_ADMIN_GROUP_ID,
            "Hospitals with outdated screening records:\nTest Hospital 0",
        )
