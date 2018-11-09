from django.conf import settings
from django.http import JsonResponse
from rest_framework.views import APIView

from sidekick.utils import clean_msisdn

from .models import MsisdnInformation
from .utils import TransferToClient, TransferToClient2
from .tasks import topup_data


class Ping(APIView):
    def get(self, request, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.ping())


class MsisdnInfo(APIView):
    def get(self, request, msisdn, *args, **kwargs):
        # TODO: check msisdn
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        cleaned_msisdn = clean_msisdn(msisdn)
        info = client.get_misisdn_info(cleaned_msisdn)
        MsisdnInformation.objects.create(data=info, msisdn=cleaned_msisdn)
        return JsonResponse(info)


class ReserveId(APIView):
    def get(self, request, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.reserve_id())


class GetCountries(APIView):
    def get(self, request, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.get_countries())


class GetOperators(APIView):
    def get(self, request, country_id, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.get_operators(country_id))


class GetOperatorAirtimeProducts(APIView):
    def get(self, request, operator_id, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        return JsonResponse(client.get_operator_airtime_products(operator_id))


class GetOperatorProducts(APIView):
    def get(self, request, operator_id, *args, **kwargs):
        client = TransferToClient2(
            settings.TRANSFERTO_APIKEY, settings.TRANSFERTO_APISECRET
        )
        resp = client.get_operator_products(operator_id)
        return JsonResponse(resp)


class GetCountryServices(APIView):
    def get(self, request, country_id, *args, **kwargs):
        client = TransferToClient2(
            settings.TRANSFERTO_APIKEY, settings.TRANSFERTO_APISECRET
        )
        resp = client.get_country_services(country_id)
        return JsonResponse(resp)


class TopUpData(APIView):
    def get(self, request, *args, **kwargs):
        data = request.GET.dict()
        msisdn = data["msisdn"]
        user_uuid = data["user_uuid"]
        data_amount = data["data_amount"]

        # msisdn, user_uuid, amount
        # e.g. "+27827620000", "4a1b8cc8-905c-4c44-8bd2-dee3c4a3e2d1", "100MB"
        topup_data.delay(msisdn, user_uuid, data_amount)

        return JsonResponse({"info_txt": "top_up_data"})
