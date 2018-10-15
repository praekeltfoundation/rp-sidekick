from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .tasks import project_check, patient_data_check
from .models import Project


def _validate_project(project_id, request):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return False, status.HTTP_400_BAD_REQUEST

    if not project.org.users.filter(id=request.user.id).exists():
        return False, status.HTTP_401_UNAUTHORIZED

    return project, status.HTTP_202_ACCEPTED


class StartProjectCheckView(APIView):
    def post(self, request, project_id, *args, **kwargs):
        project, return_status = _validate_project(project_id, request)

        if project:
            project_check.delay(project.id)

        return HttpResponse(status=return_status)


class StartPatientDataCheckView(APIView):
    def post(self, request, project_id, *args, **kwargs):
        project, return_status = _validate_project(project_id, request)

        if project:
            patient_data_check.delay(project.id)

        return HttpResponse(status=return_status)
