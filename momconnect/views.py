from rest_framework import generics, status
from rest_framework.response import Response

from .models import Clinic
from .utils import validate_clinic_code


class ClinicDetailsView(generics.RetrieveAPIView):
    def get(self, request):
        try:
            clinic_code = request.query_params["clinic_code"]
        except KeyError:
            return Response(
                {"error": "missing clinic code"}, status.HTTP_400_BAD_REQUEST
            )

        if not validate_clinic_code(clinic_code):
            return Response({"error": "invalid"}, status.HTTP_400_BAD_REQUEST)

        try:
            clinic = Clinic.objects.get(value=clinic_code)
        except Clinic.DoesNotExist:
            return Response({"error": "clinic not found"}, status.HTTP_404_NOT_FOUND)

        return Response({"code": clinic.value, "name": clinic.name})
