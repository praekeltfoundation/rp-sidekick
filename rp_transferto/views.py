from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView

from .utils import TransferToClient


class Ping(APIView):
    def get(self, request):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.ping())


class MsisdnInfo(APIView):
    def get(self, request, msisdn):
        # TODO: check msisdn
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.get_misisdn_info(msisdn))


class GetCountries(APIView):
    def get(self, request):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.get_countries())


class GetOperators(APIView):
    def get(self, request, country_id):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.get_operators(country_id))


class GetProducts(APIView):
    def get(self, request, operator_id):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.get_operator_products(operator_id))
