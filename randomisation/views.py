from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView

from randomisation.models import Strategy
from randomisation.utils import (
    get_random_stratification_arm,
    validate_stratification_data,
)

# TODO: add a endpoint to call the validate_stratification_data


class GetRandomArmView(APIView):
    def post(self, request, *args, **kwargs):
        strategy_id = kwargs["strategy_id"]
        strategy = Strategy.objects.get(id=strategy_id)

        # TODO: serializer for request.data?

        error = validate_stratification_data(strategy, request.data)
        if error:
            return JsonResponse(
                data={"error": error}, status=status.HTTP_400_BAD_REQUEST
            )

        arm = get_random_stratification_arm(strategy, request.data)

        return JsonResponse(data={"arm": arm}, status=status.HTTP_200_OK)

# TODO: add tests for views
