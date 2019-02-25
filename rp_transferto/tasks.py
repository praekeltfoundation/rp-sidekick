import json
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage

from celery.task import Task
from celery.utils.log import get_task_logger

from sidekick.utils import clean_msisdn

from .models import MsisdnInformation
from .utils import TransferToClient
from temba_client.v2 import TembaClient


log = get_task_logger(__name__)


def take_action(
    user_uuid, values_to_update=None, call_result=None, flow_start=None
):
    """
    Update rapidpro contact and/or start a user on a flow

    :param str user_uuid: contact UUID in RapidPro
    :param dict values_to_update: key-value mapping which represents variable_on_rapidpro_to_update:variable_from_response
    :param dict call_result: response from transferto call
    :param str flow_start: flow UUID in RapidPro
    """
    rapidpro_client = TembaClient(
        settings.RAPIDPRO_URL, settings.RAPIDPRO_TOKEN
    )

    if values_to_update and call_result:
        fields = {}
        for (rapidpro_field, transferto_field) in values_to_update.items():
            fields[rapidpro_field] = call_result[transferto_field]

        rapidpro_client.update_contact(user_uuid, fields=fields)

    if flow_start:
        rapidpro_client.create_flow_start(
            flow_start, contacts=[user_uuid], restart_participants=True
        )


class TopupData(Task):
    name = "rp_transferto.tasks.topup_data"

    def run(self, msisdn, user_uuid, recharge_value, *args, **kwargs):
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN,
            settings.TRANSFERTO_TOKEN,
            settings.TRANSFERTO_APIKEY,
            settings.TRANSFERTO_APISECRET,
        )
        # get msisdn number info
        try:
            msisdn_object = MsisdnInformation.objects.filter(
                msisdn=clean_msisdn(msisdn)
            ).latest()
            # use dict to make a copy of the info
            operator_id_info = dict(msisdn_object.data)
        except ObjectDoesNotExist:
            operator_id_info = client.get_misisdn_info(msisdn)

        log.info(json.dumps(operator_id_info, indent=2))

        # extract the user's operator ID
        operator_id = int(operator_id_info["operatorid"])

        # check the product available and id
        available_products = client.get_operator_products(operator_id)
        log.info(json.dumps(available_products, indent=2))

        # TODO: refactor
        product_description = None
        product_id = None
        for product in available_products["fixed_value_recharges"]:
            product_name = product["product_short_desc"]
            if recharge_value in product_name:
                product_id = product["product_id"]
                product_description = product["product_short_desc"]
                break

        log.info("product_id: {}".format(product_id))
        log.info("product_description: {}".format(product_description))

        topup_result = client.topup_data(msisdn, product_id, simulate=False)

        log.info(json.dumps(topup_result, indent=2))

        product_id = product["product_id"]

        # update RapidPro with those values

        rapidpro_client = TembaClient(
            settings.RAPIDPRO_URL, settings.RAPIDPRO_TOKEN
        )

        fields = {
            "mcl_uag_data_topup_status": topup_result["status"],
            "mcl_uag_data_topup_status_message": topup_result["status_message"],
            "mcl_uag_data_topup_product_desc": topup_result["product_desc"],
            "mcl_uag_data_topup_simulation": topup_result["simulation"],
        }
        rp_contact = rapidpro_client.get_contacts(uuid=user_uuid).first()
        rapidpro_client.update_contact(rp_contact, fields=fields)


class BuyProductTakeAction(Task):
    name = "rp_transferto.tasks.buy_product_take_action"

    def run(
        self,
        msisdn,
        product_id,
        user_uuid=None,
        values_to_update={},
        flow_start=None,
    ):
        log.info(
            json.dumps(
                dict(
                    name=self.name,
                    msisdn=msisdn,
                    product_id=product_id,
                    user_uuid=user_uuid,
                    values_to_update=values_to_update,
                    flow_start=flow_start,
                ),
                indent=2,
            )
        )
        client = TransferToClient(
            settings.TRANSFERTO_LOGIN,
            settings.TRANSFERTO_TOKEN,
            settings.TRANSFERTO_APIKEY,
            settings.TRANSFERTO_APISECRET,
        )
        purchase_result = client.topup_data(msisdn, product_id, simulate=False)

        log.info(json.dumps(purchase_result, indent=2))

        if purchase_result["status"] != "0":
            # HANDLE USE CASE FOR 100MB in ZAR
            if purchase_result["status"] == "1000204" and product_id in [
                1194,
                1601,
                1630,
            ]:
                log.info("{} failed, attempting fallback".format(product_id))
                remaining_options = [1194, 1601, 1630]
                remaining_options.remove(product_id)

                for option in remaining_options:
                    log.info(
                        json.dumps(
                            dict(
                                name=self.name,
                                msisdn=msisdn,
                                product_id=option,
                                user_uuid=user_uuid,
                                values_to_update=values_to_update,
                                flow_start=flow_start,
                            ),
                            indent=2,
                        )
                    )
                    retry_purchase_result = client.topup_data(
                        msisdn, option, simulate=False
                    )
                    log.info(json.dumps(retry_purchase_result, indent=2))
                    if retry_purchase_result["status"] == "0":
                        if user_uuid:
                            take_action(
                                user_uuid,
                                values_to_update=values_to_update,
                                call_result=retry_purchase_result,
                                flow_start=flow_start,
                            )
                        return None
                subject = "FAILURE WITH RETRIES: {} {}".format(
                    self.name, timezone.now()
                )
                message = (
                    "{}\n"
                    "-------\n"
                    "user_uuid: {}\n"
                    "values_to_update:{}\n"
                    "flow_start: {}\n"
                    "also tried: {}"
                ).format(
                    json.dumps(purchase_result, indent=2),
                    user_uuid,
                    json.dumps(values_to_update, indent=2),
                    flow_start,
                    remaining_options,
                )
                from_string = "celery@rp-sidekick.prd.mhealthengagementlab.org"
                recipients = (
                    "nathan@praekelt.org"  # TODO: link to org user in future
                )
                email = EmailMessage(
                    subject, message, from_string, [recipients]
                )
                email.send()
                return None

            subject = "FAILURE: {}".format(self.name)
            message = (
                "{}\n"
                "-------\n"
                "user_uuid: {}\n"
                "values_to_update:{}\n"
                "flow_start: {}"
            ).format(
                json.dumps(purchase_result, indent=2),
                user_uuid,
                json.dumps(values_to_update, indent=2),
                flow_start,
            )
            from_string = "celery@rp-sidekick.prd.mhealthengagementlab.org"
            recipients = (
                "nathan@praekelt.org"  # TODO: link to org user in future
            )
            email = EmailMessage(subject, message, from_string, [recipients])
            email.send()

        else:
            if user_uuid:
                take_action(
                    user_uuid,
                    values_to_update=values_to_update,
                    call_result=purchase_result,
                    flow_start=flow_start,
                )


class BuyAirtimeTakeAction(Task):
    name = "rp_transferto.tasks.buy_airtime_take_action"

    def run(
        self,
        msisdn,
        airtime_amount,
        from_string,
        user_uuid=None,
        values_to_update={},
        flow_start=None,
    ):
        log.info(
            json.dumps(
                dict(
                    name=self.name,
                    msisdn=msisdn,
                    airtime_amount=airtime_amount,
                    user_uuid=user_uuid,
                    values_to_update=values_to_update,
                    flow_start=flow_start,
                ),
                indent=2,
            )
        )
        transferto_client = TransferToClient(
            settings.TRANSFERTO_LOGIN,
            settings.TRANSFERTO_TOKEN,
            settings.TRANSFERTO_APIKEY,
            settings.TRANSFERTO_APISECRET,
        )
        topup_result = transferto_client.make_topup(
            msisdn, airtime_amount, from_string
        )

        log.info(json.dumps(topup_result, indent=2))

        if user_uuid:
            take_action(
                user_uuid,
                values_to_update=values_to_update,
                call_result=topup_result,
                flow_start=flow_start,
            )


topup_data = TopupData()
buy_product_take_action = BuyProductTakeAction()
buy_airtime_take_action = BuyAirtimeTakeAction()
