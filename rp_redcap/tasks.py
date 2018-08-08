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

    def get_records(self, survey_name):
        project = redcap.Project(settings.REDCAP_API_URL,
                                 settings.REDCAP_API_TOKEN)

        return project.export_records(
            forms=[survey_name],
            export_survey_fields=True,
            export_data_access_groups=False
        )

    def start_flows(self, flow, urns):
        rp_client = TembaClient(settings.RAPIDPRO_API_URL,
                                settings.RAPIDPRO_API_TOKEN)

        if urns:
            rp_client.create_flow_start(flow, urns, restart_participants=True)

    def run(self, survey_name, **kwargs):

        survey = Survey.objects.get(name=survey_name)

        records = self.get_records(survey_name)

        urns = []
        for record in records:
            contact, created = Contact.objects.get_or_create(
                record_id=record['record_id'])

            if survey.urn_field in record and record[survey.urn_field]:
                contact.urn = 'tel:{}'.format(record[survey.urn_field])
                contact.save()

            if(record['{}_complete'.format(survey_name)] == '2'):
                # TODO: check which fields are outstanding
                if contact.urn:
                    urns.append(contact.urn)

        self.start_flows(survey.rapidpro_flow, urns)


survey_check = SurveyCheck()
