from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework import status

from sidekick.utils import clean_msisdn
from sidekick.models import Organization

from .models import MsisdnInformation, TopupAttempt
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
            response = getattr(client, self.client_method_name)(
                **kwargs_for_client
            )
        else:
            response = getattr(client, self.client_method_name)()
        if "error_code" in response:
            return process_status_code(response)
        return JsonResponse(response)


class Ping(TransferToView):
    client_method_name = "ping"


class MsisdnInfo(APIView):
    def get(self, request, *args, **kwargs):
        org_id = kwargs["org_id"]
        msisdn = kwargs["msisdn"]

        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(data={}, status=status.HTTP_401_UNAUTHORIZED)

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
            try:
                client = org.transferto_account.first().get_transferto_client()
            except AttributeError:
                return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

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


class ReserveId(TransferToView):
    client_method_name = "reserve_id"


class GetCountries(TransferToView):
    client_method_name = "get_countries"


class GetOperators(TransferToView):
    client_method_name = "get_operators"
    args_for_client_method = ["country_id"]


class GetOperatorAirtimeProducts(TransferToView):
    client_method_name = "get_operator_airtime_products"
    args_for_client_method = ["operator_id"]


class GetOperatorProducts(TransferToView):
    client_method_name = "get_operator_products"
    args_for_client_method = ["operator_id"]


class GetCountryServices(TransferToView):
    client_method_name = "get_country_services"
    args_for_client_method = ["country_id"]


class TopUpData(APIView):
    def get(self, request, *args, **kwargs):
        org_id = kwargs["org_id"]

        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(data={}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # check that there is a valid  TransferTo Account attached
            org.transferto_account.first().get_transferto_client()
        except AttributeError:
            return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

        data = request.GET.dict()
        msisdn = data["msisdn"]
        user_uuid = data["user_uuid"]
        data_amount = data["data_amount"]

        # org_id, msisdn, user_uuid, amount
        # e.g. 1, "+27827620000", "4a1b8cc8-905c-4c44-8bd2-dee3c4a3e2d1", "100MB"
        topup_data.delay(org_id, msisdn, user_uuid, data_amount)

        return JsonResponse({"info_txt": "top_up_data"})


class BuyProductTakeAction(APIView):
    def get(self, request, *args, **kwargs):
        org_id = kwargs["org_id"]
        product_id = kwargs["product_id"]
        msisdn = kwargs["msisdn"]

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
            org_id,
            clean_msisdn(msisdn),
            product_id,
            user_uuid=user_uuid,
            values_to_update=data,
            flow_start=flow_start,
        )
        return JsonResponse({"info_txt": "buy_product_take_action"})


class BuyAirtimeTakeAction(APIView):
    def get(self, request, *args, **kwargs):
        org_id = kwargs["org_id"]
        airtime_amount = kwargs["airtime_amount"]
        msisdn = kwargs["msisdn"]
        from_string = kwargs["from_string"]

        try:
            org = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

        if not org.users.filter(id=request.user.id).exists():
            return JsonResponse(data={}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            # check that there is a valid  TransferTo Account attached
            org.transferto_account.first().get_transferto_client()
        except AttributeError:
            return JsonResponse(data={}, status=status.HTTP_400_BAD_REQUEST)

        flow_uuid_key = "flow_uuid"
        user_uuid_key = "user_uuid"
        fail_flow_uuid_key = "fail_flow_start"
        data = dict(request.GET.dict())

        flow_start = request.GET.get(flow_uuid_key, False)
        if flow_start:
            del data[flow_uuid_key]
        user_uuid = request.GET.get(user_uuid_key, False)
        if user_uuid:
            del data[user_uuid_key]
        fail_flow_start = request.GET.get(fail_flow_uuid_key, False)
        if fail_flow_start:
            del data[fail_flow_uuid_key]
        # remaining variables will be coerced from key:value mapping
        # which represents variable on rapidpro to update: variable from response

        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=org,
            rapidpro_user_uuid=user_uuid,
        )

        buy_airtime_take_action.delay(
            topup_attempt_id=topup_attempt.id,
            values_to_update=data,
            flow_start=flow_start,
            fail_flow_start=fail_flow_start,
        )
        return JsonResponse({"info_txt": "buy_airtime_take_action"})
