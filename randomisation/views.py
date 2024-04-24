from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from randomisation.models import Strategy
from randomisation.utils import (
    get_random_stratification_arm,
    validate_stratification_data,
)


class ValidateStrataData(APIView):
    def post(self, request, *args, **kwargs):
        strategy_id = kwargs["strategy_id"]
        strategy = Strategy.objects.get(id=strategy_id)

        error = validate_stratification_data(strategy, request.data or {})
        if error:
            return JsonResponse(
                data={"valid": False, "error": error},
                status=status.HTTP_200_OK,
            )

        return JsonResponse(data={"valid": True}, status=status.HTTP_200_OK)


class GetRandomArmView(APIView):
    def post(self, request, *args, **kwargs):
        strategy_id = kwargs["strategy_id"]
        strategy = Strategy.objects.get(id=strategy_id)

        error = validate_stratification_data(strategy, request.data or {})
        if error:
            return JsonResponse(
                data={"error": error}, status=status.HTTP_400_BAD_REQUEST
            )

        arm = get_random_stratification_arm(strategy, request.data)

        return JsonResponse(data={"arm": arm}, status=status.HTTP_200_OK)
