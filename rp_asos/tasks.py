import datetime
from collections import defaultdict

from celery.utils.log import get_task_logger
from django.conf import settings

from sidekick import utils

from .models import PatientRecord, PatientValue
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

    def save_patient_records(self, project, patients, date=None):
        for patient in patients:
            patient_defaults = {
                "pre_operation_status": patient["pre_operation_status"],
                "post_operation_status": patient["post_operation_status"],
            }

            if date:
                patient_defaults.update({"date": date})

            patient_obj, created = PatientRecord.objects.get_or_create(
                project=project,
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
        self, date, project, screening_client, patient_client, required_fields
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

        for hospital in project.hospitals.all():

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

            if hospital_screening_records:
                patient_count = int(
                    hospital_screening_records[0][screening_field] or "0"
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
                urns = ["tel:{}".format(hospital.hospital_lead_urn)]
                utils.update_rapidpro_whatsapp_urn(
                    org, hospital.hospital_lead_urn
                )

                extra_info = {
                    "hospital_name": hospital.name,
                    "week": utils.get_current_week_number(),
                    "reminder": "\n".join(reminders),
                    "contact_name": hospital.hospital_lead_name,
                }

                rapidpro_client.create_flow_start(
                    hospital.rapidpro_flow,
                    urns,
                    restart_participants=True,
                    extra=extra_info,
                )

                if hospital.nomination_urn:
                    urns = ["tel:{}".format(hospital.nomination_urn)]
                    utils.update_rapidpro_whatsapp_urn(
                        org, hospital.nomination_urn
                    )
                    extra_info["contact_name"] = hospital.nomination_name
                    rapidpro_client.create_flow_start(
                        hospital.rapidpro_flow,
                        urns,
                        restart_participants=True,
                        extra=extra_info,
                    )

    def run(self, project_id, **kwargs):
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
                date, project, screening_client, patient_client, required_fields
            )

            for hospital, date_messages in new_messages.items():
                for date, hospital_messages in date_messages.items():
                    messages[hospital][date] += hospital_messages

        self.send_reminders(messages, rapidpro_client, project.org)

        self.refresh_historical_data(project, patient_client, required_fields)


patient_data_check = PatientDataCheck()