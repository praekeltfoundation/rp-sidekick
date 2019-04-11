from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .tasks import patient_data_check, create_hospital_groups
from rp_redcap.views import validate_project


class StartPatientDataCheckView(APIView):
    def post(self, request, project_id, *args, **kwargs):
        return_status = validate_project(project_id, request)

        if return_status == status.HTTP_202_ACCEPTED:
            chain = create_hospital_groups.s() | patient_data_check.s()
            chain.delay(project_id)

        return HttpResponse(status=return_status)
