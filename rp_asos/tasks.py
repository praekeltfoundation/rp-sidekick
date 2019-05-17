import datetime

from celery.task import Task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db.models import Max, Q, Sum
from rp_redcap.models import Project
from rp_redcap.tasks import BaseTask
from sidekick import utils
from sidekick.models import Organization

from .models import PatientRecord, PatientValue, ScreeningRecord


class PatientDataCheck(BaseTask):
    """Remind hospital leads about missing patient data."""

    name = "rp_redcap.tasks.patient_data_check"
    log = get_task_logger(__name__)

    def get_redcap_records(self, redcap_client, form, filter=None, record_ids=None):
        return redcap_client.export_records(
            forms=[form],
            export_survey_fields=True,
            export_data_access_groups=True,
            filter_logic=filter,
            export_checkbox_labels=True,
            records=record_ids,
        )

    def save_screening_records(self, hospital, records):
        for record in records:

            screening_record, _ = ScreeningRecord.objects.get_or_create(
                hospital=hospital
            )
            new_values = screening_record.as_dict()

            total = 0
            for i in range(1, 29):
                if record["day{}".format(i)]:
                    total += int(record["day{}".format(i)])

            new_values["total_eligible"] = total

            for i in range(1, 5):
                if record["asos2_week{}".format(i)]:
                    new_values["week_{}_case_count".format(i)] = int(
                        record["asos2_week{}".format(i)]
                    )

            if record["date"]:
                new_values["date"] = record["date"]

            if screening_record.as_dict() != new_values:
                for attr, value in new_values.items():
                    setattr(screening_record, attr, value)
                screening_record.save()

    def save_patient_records(self, project, hospital, patients):
        for patient in patients:
            patient_defaults = {
                "pre_operation_status": patient["pre_operation_status"],
                "post_operation_status": patient["post_operation_status"],
            }

            if patient["date_surg"]:
                patient_defaults["date"] = patient["date_surg"]

            patient_obj, created = PatientRecord.objects.get_or_create(
                project=project,
                hospital=hospital,
                record_id=patient["record_id"],
                defaults=patient_defaults,
            )

            if not created and (
                patient_obj.pre_operation_status != patient["pre_operation_status"]
                or patient_obj.post_operation_status != patient["post_operation_status"]
            ):
                patient_obj.pre_operation_status = patient["pre_operation_status"]
                patient_obj.post_operation_status = patient["post_operation_status"]
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
                        "date_surg",
                    ]
                    and value != ""
                ):
                    obj, created = PatientValue.objects.get_or_create(
                        patient=patient_obj, name=field, defaults={"value": value}
                    )

                    if not created and obj.value != value:
                        obj.value = value
                        obj.save()

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
            if value == "" and field in status_fields and field in required_fields:
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
                    row["pre_operation_status"] = PatientRecord.INCOMPLETE_STATUS
                    row["missing_pre_op_fields"].append(required_fields[field]["label"])

                if check_field(field, post_op_fields, row, data):
                    row["post_operation_status"] = PatientRecord.INCOMPLETE_STATUS
                    row["missing_post_op_fields"].append(
                        required_fields[field]["label"]
                    )

        return patients

    def save_all_data_from_redcap(self, project, tz_code):
        screening_client = project.get_redcap_client()
        screening_records = self.get_redcap_records(screening_client, "screening_tool")

        patient_client = project.get_redcap_crf_client()

        metadata = self.get_metadata(patient_client)
        required_fields = self.get_required_fields(metadata)

        patient_records = self.get_redcap_records(patient_client, "asos2_crf")

        patient_records = self.check_patients_status(
            project, patient_records, required_fields
        )

        for hospital in project.hospitals.filter(tz_code=tz_code, is_active=True):

            hospital_screening_records = [
                d
                for d in screening_records
                if d["redcap_data_access_group"] == hospital.data_access_group
            ]
            self.save_screening_records(hospital, hospital_screening_records)

            hospital_patient_records = [
                d
                for d in patient_records
                if d["redcap_data_access_group"] == hospital.data_access_group
            ]

            self.save_patient_records(project, hospital, hospital_patient_records)

    def run(self, context):
        project_id = context["project_id"]
        tz_code = context["tz_code"]

        project = Project.objects.prefetch_related("hospitals").get(id=project_id)

        message_template = (
            "Daily data update for {hospital_name}:\n"
            "{total_eligible} eligible operations have been reported on your screening log.\n"
            "{last_update}\n"  # last update
            "{last_update_warning}"  # last update warning
            "\n"
            "{total_crfs} CRFs have been captured on REDCap.\n"
            "{total_incomplete_crfs} CRFs have incomplete data fields.\n"
            "The following CRFs have incomplete data fields on REDCap:\n"
            "{record_ids}"
        )

        date = utils.get_today() - datetime.timedelta(days=1)

        self.save_all_data_from_redcap(project, tz_code)

        for hospital in project.hospitals.filter(tz_code=tz_code, is_active=True):
            total_screening = 0
            last_update = "The screening log has not been updated."
            update_warning = (
                "Please update your screening log today or WhatsApp us if "
                "there is a problem.\n"
            )
            if hospital.screening_records.exists():
                aggregate_date = hospital.screening_records.aggregate(
                    Sum("total_eligible"), Max("updated_at")
                )

                total_screening = aggregate_date["total_eligible__sum"]
                last_update = "The last screening log update was on {}.".format(
                    aggregate_date["updated_at__max"].strftime("%d %B %Y")
                )

                if (date - aggregate_date["updated_at__max"].date()).days <= 2:
                    update_warning = ""

            crf_total_count = hospital.patients.count()
            record_ids = hospital.patients.exclude(
                Q(pre_operation_status=PatientRecord.COMPLETE_STATUS)
                | Q(post_operation_status=PatientRecord.COMPLETE_STATUS)
            ).values_list("record_id", flat=True)

            hospital.send_message(
                message_template.format(
                    hospital_name=hospital.name,
                    total_eligible=total_screening,
                    last_update=last_update,
                    last_update_warning=update_warning,
                    total_crfs=crf_total_count,
                    total_incomplete_crfs=len(record_ids),
                    record_ids="; ".join(record_ids),
                )
            )

            hospital.check_and_update_status()


patient_data_check = PatientDataCheck()


class CreateHospitalGroups(Task):
    """
    Creates a WA group per hospital and invite the hospital lead to the group.
    Hospital leads will be changed to group admins after they join the group.
    """

    name = "rp_redcap.tasks.create_hospital_groups"
    log = get_task_logger(__name__)

    def run(self, project_id, tz_code, **kwargs):
        project = Project.objects.prefetch_related("hospitals").get(id=project_id)

        for hospital in project.hospitals.filter(tz_code=tz_code, is_active=True):
            msisdns = [hospital.hospital_lead_urn]
            if hospital.nomination_urn:
                msisdns.append(hospital.nomination_urn)

            hospital.create_hospital_wa_group()
            group_info = hospital.get_wa_group_info()

            wa_ids = hospital.send_group_invites(group_info, msisdns)
            hospital.add_group_admins(group_info, wa_ids)

        return {"project_id": project_id, "tz_code": tz_code}


create_hospital_groups = CreateHospitalGroups()


class ScreeningRecordCheck(Task):
    """
    Checks all the active screening records linked to the organisation and
    notifies the steering group of records that have not been updated in the
    last 3 days.
    """

    name = "rp_asos.tasks.screening_record_check"
    log = get_task_logger(__name__)

    def run(self, org_id):
        org = Organization.objects.prefetch_related(
            "projects", "projects__hospitals", "projects__hospitals__screening_records"
        ).get(id=org_id)

        outdated_hospitals = []

        for project in org.projects.all():
            for hospital in project.hospitals.filter(is_active=True):
                aggregate_data = hospital.screening_records.aggregate(Max("updated_at"))

                if aggregate_data["updated_at__max"]:
                    if (
                        utils.get_today() - aggregate_data["updated_at__max"].date()
                    ).days > 3:
                        outdated_hospitals.append(hospital.name)
                else:
                    outdated_hospitals.append(hospital.name)

        if outdated_hospitals:
            utils.send_whatsapp_group_message(
                org,
                settings.ASOS_ADMIN_GROUP_ID,
                "Hospitals with outdated screening records:\n{}".format(
                    "\n".join(outdated_hospitals)
                ),
            )


screening_record_check = ScreeningRecordCheck()
