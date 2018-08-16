from celery.task import Task
from celery.utils.log import get_task_logger
from collections import defaultdict

from .models import Contact, Project


class ProjectCheck(Task):
    """Task to look for incomplete surveys in a Project."""

    name = "rp_sidekick.rp_redcap.tasks.project_check"
    log = get_task_logger(__name__)

    def get_records(self, survey_name, redcap_client):
        return redcap_client.export_records(
            forms=[survey_name],
            export_survey_fields=True,
            export_data_access_groups=False,
        )

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

                required_fields[field["field_name"]] = condition

        return required_fields

    def get_choices(self, metadata, field_name):
        choices = {}
        for field in metadata:
            if field["field_name"] == field_name:
                choices.update(
                    dict(
                        item.split(", ")
                        for item in field[
                            "select_choices_or_calculations"
                        ].split(" | ")
                    )
                )
        return choices

    def start_flows(self, rapidpro_client, flow, reminders):
        for urn, extra_info in reminders.items():
            rapidpro_client.create_flow_start(
                flow, [urn], restart_participants=True, extra=extra_info
            )

    def run(self, project_id, **kwargs):

        project = Project.objects.prefetch_related("surveys").get(id=project_id)

        redcap_client = project.get_redcap_client(project)
        rapidpro_client = project.org.get_rapidpro_client()

        data = defaultdict(dict)

        for survey in project.surveys.all().order_by("sequence"):

            records = self.get_records(survey.name, redcap_client)
            metadata = self.get_metadata(survey.name, redcap_client)

            required_fields = self.get_required_fields(metadata)
            roles = self.get_choices(metadata, "role")
            titles = self.get_choices(metadata, "title")

            reminders = {}
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

                if row.get("title"):
                    contact_update["title"] = titles.get(row["title"])

                if contact_update:
                    Contact.objects.filter(id=contact.id).update(
                        **contact_update
                    )
                    contact.refresh_from_db()

                if contact.urn:
                    if row["{}_complete".format(survey.name)] == "2":

                        extra_info = {
                            "project_name": project.name,
                            "survey_name": survey.name,
                            "role": contact.role,
                            "name": contact.name,
                            "title": contact.title,
                        }

                        if survey.check_fields:
                            missing_fields = []
                            for field, value in row.items():
                                if (
                                    value == ""
                                    and field in required_fields
                                    and eval(required_fields[field])
                                ):
                                    missing_fields.append(field)

                            extra_info["missing_fields"] = ", ".join(
                                missing_fields
                            )

                        reminders[contact.urn] = extra_info

            self.start_flows(rapidpro_client, survey.rapidpro_flow, reminders)


project_check = ProjectCheck()
