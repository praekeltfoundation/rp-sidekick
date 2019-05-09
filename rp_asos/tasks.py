import datetime
from collections import defaultdict

from celery.task import Task
from celery.utils.log import get_task_logger
from django.conf import settings

from sidekick import utils

from .models import PatientRecord, PatientValue, ScreeningRecord, Hospital
from rp_redcap.models import Project
from rp_redcap.tasks import BaseTask


class PatientDataCheck(BaseTask):
    """Remind hospital leads about missing patient data."""

    name = "rp_redcap.tasks.patient_data_check"
    log = get_task_logger(__name__)

    def get_redcap_records(
        self, redcap_client, form, filter=None, record_ids=None
    ):
        return redcap_client.export_records(
            forms=[form],
            export_survey_fields=True,
            export_data_access_groups=True,
            filter_logic=filter,
            export_checkbox_labels=True,
            records=record_ids,
        )

    def save_screening_records(self, hospital, date, records):
        for record in records:
            data = {"total_eligible": record["asos2_eligible"]}
            for i in range(1, 6):
                if record["day{}".format(i)]:
                    data["week_day_{}".format(i)] = record["day{}".format(i)]
            screening_record, _ = ScreeningRecord.objects.update_or_create(
                hospital=hospital, date=date, defaults=data
            )

    def save_patient_records(self, project, patients, date=None):
        for patient in patients:
            patient_defaults = {
                "pre_operation_status": patient["pre_operation_status"],
                "post_operation_status": patient["post_operation_status"],
            }

            if date:
                patient_defaults.update({"date": date})

            hospital = Hospital.objects.get(
                project=project,
                data_access_group=patient["redcap_data_access_group"],
            )

            patient_obj, created = PatientRecord.objects.get_or_create(
                project=project,
                hospital=hospital,
                record_id=patient["record_id"],
                defaults=patient_defaults,
            )

            if not created and (
                patient_obj.pre_operation_status
                != patient["pre_operation_status"]
                or patient_obj.post_operation_status
                != patient["post_operation_status"]
            ):
                patient_obj.pre_operation_status = patient[
                    "pre_operation_status"
                ]
                patient_obj.post_operation_status = patient[
                    "post_operation_status"
                ]
                patient_obj.save()

            for field, value in patient.items():
                if (
                    field
                    not in [
                        "record_id",
                        "asos2_crf_complete",
                        "pre_operation_status",
                        "post_operation_status",
                        "missing_pre_op_fields",
                        "missing_post_op_fields",
                        "redcap_data_access_group",
                    ]
                    and value != ""
                ):
                    obj, created = PatientValue.objects.get_or_create(
                        patient=patient_obj,
                        name=field,
                        defaults={"value": value},
                    )

                    if not created and obj.value != value:
                        obj.value = value
                        obj.save()

    def refresh_historical_data(self, project, patient_client, required_fields):
        record_ids = []

        for patient_record in PatientRecord.objects.filter(
            project=project
        ).exclude(
            pre_operation_status=PatientRecord.COMPLETE_STATUS,
            post_operation_status=PatientRecord.COMPLETE_STATUS,
        ):
            record_ids.append(patient_record.record_id)

        if record_ids:
            patient_records = self.get_redcap_records(
                patient_client, "asos2_crf", record_ids=record_ids
            )

            patient_records = self.check_patients_status(
                project, patient_records, required_fields
            )

            self.save_patient_records(project, patient_records)

    def check_patients_status(self, project, patients, required_fields):

        pre_op_fields = project.pre_operation_fields.split(",")
        post_op_fields = project.post_operation_fields.split(",")

        data = {}
        for row in patients:
            for field, value in row.items():
                try:
                    row[field] = int(value)
                except Exception:
                    pass
            data[row["record_id"]] = row

        def check_field(field, status_fields, row, data):
            if (
                value == ""
                and field in status_fields
                and field in required_fields
            ):
                try:
                    return eval(required_fields[field]["condition"])
                except TypeError:
                    pass

            return False

        for row in patients:
            row["pre_operation_status"] = PatientRecord.COMPLETE_STATUS
            row["post_operation_status"] = PatientRecord.COMPLETE_STATUS
            row["missing_pre_op_fields"] = []
            row["missing_post_op_fields"] = []
            for field, value in row.items():
                if check_field(field, pre_op_fields, row, data):
                    row[
                        "pre_operation_status"
                    ] = PatientRecord.INCOMPLETE_STATUS
                    row["missing_pre_op_fields"].append(
                        required_fields[field]["label"]
                    )

                if check_field(field, post_op_fields, row, data):
                    row[
                        "post_operation_status"
                    ] = PatientRecord.INCOMPLETE_STATUS
                    row["missing_post_op_fields"].append(
                        required_fields[field]["label"]
                    )

        return patients

    def get_reminders_for_date(
        self,
        date,
        project,
        screening_client,
        patient_client,
        required_fields,
        tz_code,
    ):
        messages = defaultdict(lambda: defaultdict(list))
        if date.weekday() > 4:
            return messages

        screening_date = date - datetime.timedelta(days=date.weekday())
        screening_field = "day{}".format(date.weekday() + 1)

        screening_records = self.get_redcap_records(
            screening_client,
            "screening_tool",
            "[date] = '{}'".format(screening_date),
        )

        patient_records = self.get_redcap_records(
            patient_client, "asos2_crf", "[date_surg] = '{}'".format(date)
        )

        patient_records = self.check_patients_status(
            project, patient_records, required_fields
        )

        for hospital in project.hospitals.filter(
            tz_code=tz_code, is_active=True
        ):

            hospital_screening_records = [
                d
                for d in screening_records
                if d["redcap_data_access_group"] == hospital.data_access_group
            ]
            hospital_patient_records = [
                d
                for d in patient_records
                if d["redcap_data_access_group"] == hospital.data_access_group
            ]

            self.save_screening_records(
                hospital, screening_date, hospital_screening_records
            )

            if (
                hospital_screening_records
                and hospital_screening_records[0][screening_field]
            ):
                patient_count = int(
                    hospital_screening_records[0][screening_field]
                )

                # Check count
                if patient_count != len(hospital_patient_records):
                    messages[hospital][date].append(
                        "Not all patients captured.({}/{})".format(
                            len(hospital_patient_records), patient_count
                        )
                    )

                # check status
                for patient in hospital_patient_records:
                    if (
                        patient.get("pre_operation_status")
                        != PatientRecord.COMPLETE_STATUS
                        or patient.get("post_operation_status")
                        != PatientRecord.COMPLETE_STATUS
                    ):
                        messages[hospital][date].append(
                            "{}: {} preoperative, {} postoperative fields missing".format(
                                patient["record_id"],
                                len(patient["missing_pre_op_fields"]),
                                len(patient["missing_post_op_fields"]),
                            )
                        )
            else:
                messages[hospital][date].append(
                    "No screening records found.({})".format(date)
                )

        self.save_patient_records(project, patient_records, date)

        return messages

    def send_reminders(self, messages, rapidpro_client, org):
        for hospital, msgs in messages.items():
            reminders = []
            for date, hosp_msgs in msgs.items():
                if hosp_msgs:
                    reminders.append(
                        "\nFor surgeries registered on {}:".format(
                            date.strftime("%d %B %Y")
                        )
                    )
                for msg in hosp_msgs:
                    reminders.append(msg)

            if reminders:
                hospital.send_message(reminders)

    def run(self, args, **kwargs):
        project_id = args[0]
        tz_code = args[1]

        project = Project.objects.prefetch_related("hospitals").get(
            id=project_id
        )

        screening_client = project.get_redcap_client()
        patient_client = project.get_redcap_crf_client()
        rapidpro_client = project.org.get_rapidpro_client()

        metadata = self.get_metadata(patient_client)
        required_fields = self.get_required_fields(metadata)

        messages = defaultdict(lambda: defaultdict(list))

        for day in range(0, settings.ASOS_HISTORICAL_DAYS):
            date = utils.get_today() - datetime.timedelta(days=day + 1)

            new_messages = self.get_reminders_for_date(
                date,
                project,
                screening_client,
                patient_client,
                required_fields,
                tz_code,
            )

            for hospital, date_messages in new_messages.items():
                for date, hospital_messages in date_messages.items():
                    messages[hospital][date] += hospital_messages

        self.send_reminders(messages, rapidpro_client, project.org)

        self.refresh_historical_data(project, patient_client, required_fields)


patient_data_check = PatientDataCheck()


class CreateHospitalGroups(Task):
    """
    Creates a WA group per hospital and invite the hospital lead to the group.
    Hospital leads will be changed to group admins after they join the group.
    """

    name = "rp_redcap.tasks.create_hospital_groups"
    log = get_task_logger(__name__)

    def run(self, project_id, tz_code, **kwargs):
        project = Project.objects.prefetch_related("hospitals").get(
            id=project_id
        )

        for hospital in project.hospitals.filter(
            tz_code=tz_code, is_active=True
        ):
            msisdns = [hospital.hospital_lead_urn]
            if hospital.nomination_urn:
                msisdns.append(hospital.nomination_urn)

            hospital.create_hospital_wa_group()
            group_info = hospital.get_wa_group_info()

            wa_ids = hospital.send_group_invites(group_info, msisdns)
            hospital.add_group_admins(group_info, wa_ids)

        return (project_id, tz_code)


create_hospital_groups = CreateHospitalGroups()
