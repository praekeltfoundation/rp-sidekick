from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .tasks import project_check


class StartProjectCheckView(APIView):
    def post(self, request, project_id, *args, **kwargs):
        project_check.delay(project_id)
        return HttpResponse(status=status.HTTP_202_ACCEPTED)
