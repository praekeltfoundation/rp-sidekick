import redcap

from celery.task import Task
from celery.utils.log import get_task_logger
from collections import defaultdict
from django.conf import settings
from temba_client.v2 import TembaClient

from .models import Contact, Project


class ProjectCheck(Task):
    """Task to look for incomplete surveys in a Project."""

    name = "rp_sidekick.rp_redcap.tasks.project_check"
    log = get_task_logger(__name__)

    def get_redcap_client(self, project):
        return redcap.Project(project.url, project.token)

    def get_records(self, survey_name, redcap_client):
        return redcap_client.export_records(
            forms=[survey_name],
            export_survey_fields=True,
            export_data_access_groups=False
        )

    def get_required_fields(self, survey_name, redcap_client):
        metadata = redcap_client.export_metadata(forms=[survey_name])

        required_fields = {}

        for field in metadata:
            if field.get('required_field') == 'y':
                condition = 'True'
                if field['branching_logic']:
                    condition = field['branching_logic'].replace(']', '"]')
                    condition = condition.replace(
                        '[', 'data[row["record_id"]]["')
                    condition = condition.replace(' = ', ' == ')
                    condition = condition.replace('(', '___').replace(')', '')

                required_fields[field['field_name']] = condition

        return required_fields

    def start_flows(self, flow, reminders):
        rp_client = TembaClient(settings.RAPIDPRO_API_URL,
                                settings.RAPIDPRO_API_TOKEN)

        for urn, extra_info in reminders.items():
            rp_client.create_flow_start(
                flow, [urn], restart_participants=True, extra=extra_info)

    def run(self, project_id, **kwargs):

        project = Project.objects.prefetch_related('surveys').get(
            id=project_id)

        redcap_client = self.get_redcap_client(project)

        data = defaultdict(dict)

        for survey in project.surveys.all().order_by('sequence'):

            records = self.get_records(survey.name, redcap_client)
            required_fields = self.get_required_fields(survey.name,
                                                       redcap_client)

            reminders = {}
            for row in records:
                data[row["record_id"]].update(row)

                contact, created = Contact.objects.get_or_create(
                    record_id=row['record_id'], project=project)

                if survey.urn_field in row and row[survey.urn_field]:
                    contact.urn = 'tel:{}'.format(row[survey.urn_field])
                    contact.save()

                if contact.urn:
                    if (row['{}_complete'.format(survey.name)] == '2'):

                        extra_info = {
                            'project_name': project.name,
                            'survey_name': survey.name
                        }

                        if survey.check_fields:
                            missing_fields = []
                            for field, value in row.items():
                                if (value == '' and
                                        field in required_fields and
                                        eval(required_fields[field])):
                                    missing_fields.append(field)

                            extra_info['missing_fields'] = ', '.join(
                                missing_fields)

                        reminders[contact.urn] = extra_info

            self.start_flows(survey.rapidpro_flow, reminders)


project_check = ProjectCheck()
