from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .tasks import project_check
from .models import Project


class StartProjectCheckView(APIView):
    def post(self, request, project_id, *args, **kwargs):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

        if not project.org.users.filter(id=request.user.id).exists():
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

        project_check.delay(project.id)
        return HttpResponse(status=status.HTTP_202_ACCEPTED)
