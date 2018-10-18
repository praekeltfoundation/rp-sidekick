import datetime

from celery.task import Task
from celery.utils.log import get_task_logger
from collections import defaultdict
from django.conf import settings
from sidekick import utils

from .models import Contact, Project, SurveyAnswer, PatientRecord, PatientValue


class ProjectCheck(Task):
    """Task to look for incomplete surveys in a Project."""

    name = "rp_redcap.tasks.project_check"
    log = get_task_logger(__name__)

    def get_metadata(self, survey_name, redcap_client):
        return redcap_client.export_metadata(forms=[survey_name])

    def get_required_fields(self, metadata):

        required_fields = {}

        for field in metadata:
            if field.get("required_field") == "y":
                condition = "True"
                if field["branching_logic"]:
                    condition = field["branching_logic"].replace("]", '"]')
                    condition = condition.replace(
                        "[", 'data[row["record_id"]]["'
                    )
                    condition = condition.replace(" = ", " == ")
                    condition = condition.replace("(", "___").replace(")", "")

                required_fields[field["field_name"]] = {
                    "condition": condition,
                    "label": field["field_label"],
                }

        return required_fields

    def get_records(self, survey_name, redcap_client):
        return redcap_client.export_records(
            forms=[survey_name],
            export_survey_fields=True,
            export_data_access_groups=False,
        )

    def get_choices(self, metadata, field_name):
        choices = {}
        for field in metadata:
            if field["field_name"] == field_name:
                choices.update(
                    dict(
                        item.split(", ", 1)
                        for item in field[
                            "select_choices_or_calculations"
                        ].split(" | ")
                    )
                )
        return choices

    def save_answers(self, row, survey, contact):
        for field, value in row.items():
            if (
                field
                not in [
                    "record_id",
                    "{}_complete".format(survey.name),
                    "{}_timestamp".format(survey.name),
                ]
                and value != ""
            ):
                obj, created = SurveyAnswer.objects.get_or_create(
                    survey=survey,
                    contact=contact,
                    name=field,
                    defaults={"value": value},
                )

                if not created and obj.value != value:
                    obj.value = value
                    obj.save()

    def start_flows(self, rapidpro_client, flow, project_name, reminders, org):
        for contact_id, missing_fields in reminders.items():
            contact = Contact.objects.get(id=contact_id)

            if contact.urn:
                utils.update_rapidpro_whatsapp_urn(
                    org, contact.urn.replace("tel:", "")
                )

                missing_fields_count = []
                for survey, count in missing_fields.items():
                    missing_fields_count.append(
                        "{}: {} missing field{}".format(
                            survey, count, "" if count == 1 else "s"
                        )
                    )

                extra_info = {
                    "project_name": project_name,
                    "role": contact.role or "",
                    "name": contact.name or "",
                    "surname": contact.surname or "",
                    "title": contact.title or "",
                    "week": utils.get_current_week_number(),
                    "missing_fields_count": "\n".join(missing_fields_count),
                    "missing_fields": "\n".join(missing_fields.keys()),
                }

                rapidpro_client.create_flow_start(
                    flow,
                    [contact.urn],
                    restart_participants=True,
                    extra=extra_info,
                )

    def run(self, project_id, **kwargs):

        project = Project.objects.prefetch_related("surveys").get(id=project_id)

        redcap_client = project.get_redcap_client()
        rapidpro_client = project.org.get_rapidpro_client()

        data = defaultdict(dict)

        reminders = defaultdict(dict)

        for survey in project.surveys.all().order_by("sequence"):

            records = self.get_records(survey.name, redcap_client)
            metadata = self.get_metadata(survey.name, redcap_client)

            required_fields = self.get_required_fields(metadata)
            ignore_fields = survey.get_ignore_fields()
            roles = self.get_choices(metadata, "role")
            titles = self.get_choices(metadata, "title")

            for row in records:
                data[row["record_id"]].update(row)

                contact, created = Contact.objects.get_or_create(
                    record_id=row["record_id"], project=project
                )

                contact_update = {}

                if survey.urn_field in row and row[survey.urn_field]:
                    contact_update["urn"] = "tel:{}".format(
                        row[survey.urn_field]
                    )

                if roles:
                    for role_id, role in roles.items():
                        if row.get("role___{}".format(role_id)) == "1":
                            contact_update["role"] = role

                if row.get("name"):
                    contact_update["name"] = row.get("name")

                if row.get("surname"):
                    contact_update["surname"] = row.get("surname")

                if row.get("title"):
                    contact_update["title"] = titles.get(row["title"])

                if contact_update:
                    Contact.objects.filter(id=contact.id).update(
                        **contact_update
                    )

                self.save_answers(row, survey, contact)

                if row["{}_complete".format(survey.name)] == "0":
                    missing_fields = []

                    for field, value in row.items():
                        if (
                            value == ""
                            and field in required_fields
                            and field not in ignore_fields
                            and eval(required_fields[field]["condition"])
                        ):
                            missing_fields.append(field)

                    if missing_fields:
                        reminders[contact.id][survey.description] = len(
                            missing_fields
                        )

        self.start_flows(
            rapidpro_client,
            survey.rapidpro_flow,
            project.name,
            reminders,
            project.org,
        )


project_check = ProjectCheck()


class PatientDataCheck(Task):
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

    def refresh_historical_data(self, project, patient_client):
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
                project, patient_records
            )

            self.save_patient_records(project, patient_records)

    def check_patients_status(self, project, patients):

        pre_op_fields = project.pre_operation_fields.split(",")
        post_op_fields = project.post_operation_fields.split(",")

        for patient in patients:
            patient["pre_operation_status"] = PatientRecord.COMPLETE_STATUS
            patient["post_operation_status"] = PatientRecord.COMPLETE_STATUS
            for field, value in patient.items():
                if value == "" and field in pre_op_fields:
                    patient[
                        "pre_operation_status"
                    ] = PatientRecord.INCOMPLETE_STATUS
                if value == "" and field in post_op_fields:
                    patient[
                        "post_operation_status"
                    ] = PatientRecord.INCOMPLETE_STATUS

        return patients

    def get_reminders_for_date(
        self, date, project, screening_client, patient_client
    ):
        messages = defaultdict(lambda: defaultdict(list))

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

        patient_records = self.check_patients_status(project, patient_records)

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
                for status in ["pre", "post"]:
                    incomplete = [
                        patient.get("record_id")
                        for patient in hospital_patient_records
                        if patient.get("{}_operation_status".format(status))
                        != PatientRecord.COMPLETE_STATUS
                    ]

                    if incomplete:
                        messages[hospital][date].append(
                            "Incomplete {} operation patient data.({})".format(
                                status, ", ".join(incomplete)
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
                    reminders.append(date.strftime("%Y-%m-%d"))
                for msg in hosp_msgs:
                    reminders.append(msg)

            if reminders:
                urns = ["tel:{}".format(hospital.hospital_lead_urn)]
                utils.update_rapidpro_whatsapp_urn(
                    org, hospital.hospital_lead_urn
                )
                if hospital.nomination_urn:
                    urns.append("tel:{}".format(hospital.nomination_urn))
                    utils.update_rapidpro_whatsapp_urn(
                        org, hospital.nomination_urn
                    )

                extra_info = {
                    "hospital_name": hospital.name,
                    "week": utils.get_current_week_number(),
                    "reminder": "\n".join(reminders),
                }

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

        messages = defaultdict(lambda: defaultdict(list))

        for day in range(0, settings.REDCAP_HISTORICAL_DAYS):
            date = utils.get_today() - datetime.timedelta(days=day + 1)

            new_messages = self.get_reminders_for_date(
                date, project, screening_client, patient_client
            )

            for hospital, date_messages in new_messages.items():
                for date, hospital_messages in date_messages.items():
                    messages[hospital][date] += hospital_messages

        self.send_reminders(messages, rapidpro_client, project.org)

        self.refresh_historical_data(project, patient_client)


patient_data_check = PatientDataCheck()
