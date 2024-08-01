from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from sidekick.models import Organization

from .utils import send_airtime


class SendFixedValueAirtimeView(APIView):
    def get(self, request, *args, **kwargs):
        org_id = kwargs["org_id"]
        airtime_value = kwargs["airtime_value"]
        msisdn = kwargs["msisdn"]

        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return JsonResponse(
                data={"error": "organisation not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(
                data={"error": "user not in org"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # check that there is a valid  DTOne Account attached
            client = org.dtone_account.first().get_dtone_client()
        except AttributeError:
            return JsonResponse(
                data={"error": "no dtone account configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        success, transaction_uuid = send_airtime(org_id, client, msisdn, airtime_value)
        return_status = status.HTTP_200_OK
        if not success:
            return_status = status.HTTP_400_BAD_REQUEST

        return JsonResponse(data={"uuid": transaction_uuid}, status=return_status)
