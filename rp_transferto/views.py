from django.http import JsonResponse
from rest_framework.views import APIView


class GetProducts(APIView):
    def get(self, request):
        return JsonResponse({"status": "okay"})
