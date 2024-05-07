from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from sidekick.models import Organization

from .serializers import GetOrderedContentSetSerializer
from .utils import get_contentset, get_ordered_content_set


class GetOrderedContentSet(APIView):

    def post(self, request, org_id):
        serializer = GetOrderedContentSetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return JsonResponse(
                {"error": "Organization not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(
                data={
                    "error": "Authenticated user does not belong to specified Organization"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ordered_set_id = get_ordered_content_set(
            org, serializer.validated_data["fields"]
        )

        return JsonResponse(
            {"ordered_set_id": ordered_set_id}, status=status.HTTP_200_OK
        )


class GetContentSet(APIView):

    def get(self, request, org_id, contentset_id, msisdn):
        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return JsonResponse(
                {"error": "Organization not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(
                data={
                    "error": "Authenticated user does not belong to specified Organization"
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = get_contentset(org, contentset_id, msisdn)
        return JsonResponse(data, status=status.HTTP_200_OK)
