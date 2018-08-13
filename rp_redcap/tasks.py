import redcap

from celery.task import Task
from celery.utils.log import get_task_logger
from django.conf import settings
from temba_client.v2 import TembaClient

from .models import Survey, Contact


class SurveyCheck(Task):
    """Task to look for incomplete surveys."""

    name = "rp_sidekick.rp_redcap.tasks.survey_check"
    log = get_task_logger(__name__)

    def get_redcap_client(self):
        return redcap.Project(settings.REDCAP_API_URL,
                              settings.REDCAP_API_TOKEN)

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
                    condition = field['branching_logic'].replace('[', 'row[\'')
                    condition = condition.replace(']', '\']')
                    condition = condition.replace(' = ', ' == ')
                    condition = condition.replace('(', '___').replace(')', '')

                required_fields[field['field_name']] = condition

        return required_fields

    def start_flows(self, flow, contacts):
        rp_client = TembaClient(settings.RAPIDPRO_API_URL,
                                settings.RAPIDPRO_API_TOKEN)

        for urn, missing_fields in contacts.items():
            rp_client.create_flow_start(
                flow, [urn], restart_participants=True,
                extra={'missing_fields': missing_fields})

    def run(self, survey_name, **kwargs):

        survey = Survey.objects.get(name=survey_name)

        redcap_client = self.get_redcap_client()

        records = self.get_records(survey_name, redcap_client)
        required_fields = self.get_required_fields(survey_name, redcap_client)

        contacts = {}
        for row in records:
            contact, created = Contact.objects.get_or_create(
                record_id=row['record_id'])

            if survey.urn_field in row and row[survey.urn_field]:
                contact.urn = 'tel:{}'.format(row[survey.urn_field])
                contact.save()

            if(row['{}_complete'.format(survey_name)] == '2'):

                missing_fields = []
                if survey.check_fields:
                    for field, value in row.items():
                        if (value == '' and
                                field in required_fields and
                                eval(required_fields[field])):
                            missing_fields.append(field)

                if contact.urn:
                    contacts[contact.urn] = ', '.join(missing_fields)

        self.start_flows(survey.rapidpro_flow, contacts)


survey_check = SurveyCheck()
