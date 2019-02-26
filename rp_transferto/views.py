from django.conf import settings
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import BasePermission

from sidekick.utils import clean_msisdn
from sidekick.models import Organization

from .models import MsisdnInformation
from .utils import TransferToClient
from .tasks import topup_data, buy_product_take_action, buy_airtime_take_action


def process_status_code(info):
    """
    returns a JsonResponse object with status updated to reflect info

    For more detail on possible  TransferTo error codes, see
    section "9.0 Standard API Errors" in https://shop.transferto.com/shop/v3/doc/TransferTo_API.pdf

    @param info: dict containing key "error_code"
    @returns: JsonResponse object with status updated to reflect "error_code"
    @raises keyError: if "error_code" is not contained within info dict
    """
    error_code = info["error_code"]
    if error_code not in ["0", 0]:
        return JsonResponse(info, status=400)
    # default to 200 status code
    return JsonResponse(info)


class BelongsToOrg(BasePermission):
    pass


class TransferToView(APIView):
    client_method_name = None
    args_for_client_method = None

    def get(self, request, *args, **kwargs):
        # check that org exists
        # check that request belongs to org
        # check that org has TransferTo account
        org_id = kwargs["org_id"]

        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(data={}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            client = org.transferto_account.first().get_transferto_client()
        except AttributeError:
            return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

        if self.args_for_client_method:
            kwargs_for_client = {
                key: kwargs[key] for key in self.args_for_client_method
            }
            return process_status_code(
                getattr(client, self.client_method_name)(**kwargs_for_client)
            )
        return process_status_code(getattr(client, self.client_method_name)())


class Ping(TransferToView):
    client_method_name = "ping"


class MsisdnInfo(APIView):
    def get(self, request, msisdn, *args, **kwargs):
        use_cache = (
            request.GET.get("no_cache", False)
            and request.GET.get("no_cache").lower() == "true"
        )
        if (
            use_cache
            or not MsisdnInformation.objects.filter(
                msisdn=clean_msisdn(msisdn)
            ).exists()
        ):
            client = TransferToClient(
                settings.TRANSFERTO_LOGIN,
                settings.TRANSFERTO_TOKEN,
                settings.TRANSFERTO_APIKEY,
                settings.TRANSFERTO_APISECRET,
            )
            cleaned_msisdn = clean_msisdn(msisdn)
            info = client.get_misisdn_info(cleaned_msisdn)
            MsisdnInformation.objects.create(data=info, msisdn=cleaned_msisdn)
        # get cached result
        else:
            info = dict(
                MsisdnInformation.objects.filter(msisdn=clean_msisdn(msisdn))
                .latest()
                .data
            )
        return process_status_code(info)


class ReserveId(APIView):
    def get(self, request, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN,
            settings.TRANSFERTO_TOKEN,
            settings.TRANSFERTO_APIKEY,
            settings.TRANSFERTO_APISECRET,
        )
        return process_status_code(client.reserve_id())


class GetCountries(APIView):
    def get(self, request, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN,
            settings.TRANSFERTO_TOKEN,
            settings.TRANSFERTO_APIKEY,
            settings.TRANSFERTO_APISECRET,
        )
        return process_status_code(client.get_countries())


class GetOperators(TransferToView):
    client_method_name = "get_operators"
    args_for_client_method = ["country_id"]


class GetOperatorAirtimeProducts(APIView):
    def get(self, request, operator_id, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN,
            settings.TRANSFERTO_TOKEN,
            settings.TRANSFERTO_APIKEY,
            settings.TRANSFERTO_APISECRET,
        )
        return process_status_code(
            client.get_operator_airtime_products(operator_id)
        )


class GetOperatorProducts(APIView):
    def get(self, request, operator_id, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN,
            settings.TRANSFERTO_TOKEN,
            settings.TRANSFERTO_APIKEY,
            settings.TRANSFERTO_APISECRET,
        )
        resp = client.get_operator_products(operator_id)
        return JsonResponse(resp)


class GetCountryServices(APIView):
    def get(self, request, country_id, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN,
            settings.TRANSFERTO_TOKEN,
            settings.TRANSFERTO_APIKEY,
            settings.TRANSFERTO_APISECRET,
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


class BuyProductTakeAction(APIView):
    def get(self, request, product_id, msisdn, *args, **kwargs):
        flow_uuid_key = "flow_uuid"
        user_uuid_key = "user_uuid"
        data = dict(request.GET.dict())

        flow_start = request.GET.get(flow_uuid_key, False)
        if flow_start:
            del data[flow_uuid_key]
        user_uuid = request.GET.get(user_uuid_key, False)
        if user_uuid:
            del data[user_uuid_key]
        # remaining variables will be coerced from key:value mapping
        # which represents variable on rapidpro to update: variable from response

        buy_product_take_action.delay(
            clean_msisdn(msisdn),
            product_id,
            user_uuid=user_uuid,
            values_to_update=data,
            flow_start=flow_start,
        )
        return JsonResponse({"info_txt": "buy_product_take_action"})


class BuyAirtimeTakeAction(APIView):
    def get(
        self, request, airtime_amount, msisdn, from_string, *args, **kwargs
    ):
        flow_uuid_key = "flow_uuid"
        user_uuid_key = "user_uuid"
        data = dict(request.GET.dict())

        flow_start = request.GET.get(flow_uuid_key, False)
        if flow_start:
            del data[flow_uuid_key]
        user_uuid = request.GET.get(user_uuid_key, False)
        if user_uuid:
            del data[user_uuid_key]
        # remaining variables will be coerced from key:value mapping
        # which represents variable on rapidpro to update: variable from response

        buy_airtime_take_action.delay(
            clean_msisdn(msisdn),
            airtime_amount,
            from_string,
            user_uuid=user_uuid,
            values_to_update=data,
            flow_start=flow_start,
        )
        return JsonResponse({"info_txt": "buy_airtime_take_action"})
