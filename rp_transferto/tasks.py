import json
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from celery.task import Task
from celery.utils.log import get_task_logger

from sidekick.utils import clean_msisdn

from .models import MsisdnInformation
from .utils import TransferToClient, TransferToClient2
from temba_client.v2 import TembaClient


log = get_task_logger(__name__)


class TopupData(Task):
    name = "rp_transferto.tasks.topup_data"

    def run(self, msisdn, user_uuid, recharge_value, *args, **kwargs):
        default_client = TransferToClient(
            settings.TRANSFERTO_LOGIN, settings.TRANSFERTO_TOKEN
        )
        new_client = TransferToClient2(
            settings.TRANSFERTO_APIKEY, settings.TRANSFERTO_APISECRET
        )
        # get msisdn number info
        try:
            msisdn_object = MsisdnInformation.objects.filter(
                msisdn=clean_msisdn(msisdn)
            ).latest()
            # use dict to make a copy of the info
            operator_id_info = dict(msisdn_object.data)
        except ObjectDoesNotExist:
            operator_id_info = default_client.get_misisdn_info(msisdn)

        log.info(json.dumps(operator_id_info, indent=2))

        # extract the user's operator ID
        operator_id = int(operator_id_info["operatorid"])

        # check the product available and id
        available_products = new_client.get_operator_products(operator_id)
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

        topup_result = new_client.topup_data(msisdn, product_id, simulate=False)

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


topup_data = TopupData()
