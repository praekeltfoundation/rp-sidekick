from django.http import HttpResponse
from rest_framework.views import APIView

from .tasks import patient_data_check
from rp_redcap.views import validate_project_start_task


class StartPatientDataCheckView(APIView):
    def post(self, request, project_id, *args, **kwargs):
        return_status = validate_project_start_task(
            project_id, request, patient_data_check
        )

        return HttpResponse(status=return_status)
