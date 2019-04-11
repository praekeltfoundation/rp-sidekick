from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .tasks import project_check
from .models import Project


def validate_project(project_id, request):
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return status.HTTP_400_BAD_REQUEST

    if not project.org.users.filter(id=request.user.id).exists():
        return status.HTTP_401_UNAUTHORIZED

    return status.HTTP_202_ACCEPTED


class StartProjectCheckView(APIView):
    def post(self, request, project_id, *args, **kwargs):
        return_status = validate_project(project_id, request)

        if return_status == status.HTTP_202_ACCEPTED:
            project_check.delay(project_id)

        return HttpResponse(status=return_status)
