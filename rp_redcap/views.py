from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .tasks import project_check, patient_data_check
from .models import Project


def _validate_project_start_task(project_id, request, task):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return status.HTTP_400_BAD_REQUEST

    if not project.org.users.filter(id=request.user.id).exists():
        return status.HTTP_401_UNAUTHORIZED

    task.delay(project.id)

    return status.HTTP_202_ACCEPTED


class StartProjectCheckView(APIView):
    def post(self, request, project_id, *args, **kwargs):
        return_status = _validate_project_start_task(
            project_id, request, project_check
        )

        return HttpResponse(status=return_status)


class StartPatientDataCheckView(APIView):
    def post(self, request, project_id, *args, **kwargs):
        return_status = _validate_project_start_task(
            project_id, request, patient_data_check
        )

        return HttpResponse(status=return_status)
