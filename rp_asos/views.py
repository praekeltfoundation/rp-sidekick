from django.http import HttpResponse
from rest_framework import status
from rest_framework.views import APIView

from .tasks import (
    patient_data_check,
    create_hospital_groups,
    screening_record_check,
)
from rp_redcap.views import validate_project
from sidekick.models import Organization


def validate_organization(org_id, request):
    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return status.HTTP_400_BAD_REQUEST

    if not org.users.filter(id=request.user.id).exists():
        return status.HTTP_401_UNAUTHORIZED

    return status.HTTP_202_ACCEPTED


class StartPatientDataCheckView(APIView):
    def post(self, request, project_id, tz_code, *args, **kwargs):
        return_status = validate_project(project_id, request)

        if return_status == status.HTTP_202_ACCEPTED:
            chain = create_hospital_groups.s() | patient_data_check.s()
            chain.delay(project_id, tz_code)

        return HttpResponse(status=return_status)


class StartScreeningRecordCheckView(APIView):
    def post(self, request, org_id, *args, **kwargs):
        return_status = validate_organization(org_id, request)

        if return_status == status.HTTP_202_ACCEPTED:
            screening_record_check.delay(org_id)

        return HttpResponse(status=return_status)
