from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .tasks import survey_check


class StartSurveyCheckView(APIView):
    def post(self, request, survey_name, *args, **kwargs):
        survey_check.delay(survey_name)
        return HttpResponse(status=status.HTTP_202_ACCEPTED)
