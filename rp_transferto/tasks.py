import json

import pkg_resources
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from json2html import json2html

from config.celery import app
from sidekick.models import Organization
from sidekick.utils import clean_msisdn, get_flow_url, start_flow

from .models import MsisdnInformation, TopupAttempt

log = get_task_logger(__name__)


def take_action(
    org, user_uuid, values_to_update=None, call_result=None, flow_start=None
):
    """
    Update rapidpro contact and/or start a user on a flow

    :parma obj org: Organization object
    :param str user_uuid: contact UUID in RapidPro
    :param dict values_to_update: key-value mapping which represents variable_on_rapidpro_to_update:variable_from_response
    :param dict call_result: response from transferto call
    :param str flow_start: flow UUID in RapidPro
    """
    rapidpro_client = org.get_rapidpro_client()

    if values_to_update and call_result:
        fields = {}
        for rapidpro_field, transferto_field in values_to_update.items():
            fields[rapidpro_field] = call_result[transferto_field]

        rapidpro_client.update_contact(user_uuid, fields=fields)

    if flow_start:
        rapidpro_client.create_flow_start(
            flow_start, contacts=[user_uuid], restart_participants=True
        )


def update_values(org, user_uuid, values_to_update, transferto_response):
    """
    Update rapidpro contact and/or start a user on a flow

    :parma obj org: Organization object
    :param str user_uuid: contact UUID in RapidPro
    :param dict values_to_update: key-value mapping which represents variable_on_rapidpro_to_update:variable_from_response
    :param dict transferto_response: response from transferto call
    """
    rapidpro_client = org.get_rapidpro_client()

    fields = {}
    for rapidpro_field, transferto_field in values_to_update.items():
        fields[rapidpro_field] = transferto_response.get(transferto_field, "NONE")

    rapidpro_client.update_contact(user_uuid, fields=fields)


@app.task()
def topup_data(org_id, msisdn, user_uuid, recharge_value, *args, **kwargs):
    org = Organization.objects.get(id=org_id)
    transferto_client = org.transferto_account.first().get_transferto_client()
    # get msisdn number info
    try:
        msisdn_object = MsisdnInformation.objects.filter(
            msisdn=clean_msisdn(msisdn)
        ).latest()
        # use dict to make a copy of the info
        operator_id_info = dict(msisdn_object.data)
    except ObjectDoesNotExist:
        operator_id_info = transferto_client.get_misisdn_info(msisdn)

    log.info(json.dumps(operator_id_info, indent=2))

    # extract the user's operator ID
    operator_id = int(operator_id_info["operatorid"])

    # check the product available and id
    available_products = transferto_client.get_operator_products(operator_id)
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

    topup_result = transferto_client.topup_data(msisdn, product_id, simulate=False)

    log.info(json.dumps(topup_result, indent=2))

    product_id = product["product_id"]

    # update RapidPro with those values

    rapidpro_client = org.get_rapidpro_client()

    fields = {
        "mcl_uag_data_topup_status": topup_result["status"],
        "mcl_uag_data_topup_status_message": topup_result["status_message"],
        "mcl_uag_data_topup_product_desc": topup_result["product_desc"],
        "mcl_uag_data_topup_simulation": topup_result["simulation"],
    }
    rp_contact = rapidpro_client.get_contacts(uuid=user_uuid).first()
    rapidpro_client.update_contact(rp_contact, fields=fields)


@app.task()
def buy_product_take_action(
    org_id, msisdn, product_id, user_uuid=None, values_to_update={}, flow_start=None
):
    """
    Note: operates under the assumption that org_id is valid and has transferto account
    """
    name = "rp_transferto.tasks.buy_product_take_action"
    log.info(
        json.dumps(
            dict(
                sidekick_version=pkg_resources.get_distribution("rp-sidekick").version,
                name=name,
                org_id=org_id,
                msisdn=msisdn,
                product_id=product_id,
                user_uuid=user_uuid,
                values_to_update=values_to_update,
                flow_start=flow_start,
            ),
            indent=2,
        )
    )
    org = Organization.objects.get(id=org_id)
    transferto_client = org.transferto_account.first().get_transferto_client()

    purchase_result = transferto_client.topup_data(msisdn, product_id, simulate=False)

    log.info(json.dumps(purchase_result, indent=2))

    if purchase_result["status"] != "0":
        # HANDLE USE CASE FOR 100MB in ZAR
        if purchase_result["status"] == "1000204" and product_id in [1194, 1601, 1630]:
            log.info("{} failed, attempting fallback".format(product_id))
            remaining_options = [1194, 1601, 1630]
            remaining_options.remove(product_id)

            for option in remaining_options:
                log.info(
                    json.dumps(
                        dict(
                            name=name,
                            msisdn=msisdn,
                            product_id=option,
                            user_uuid=user_uuid,
                            values_to_update=values_to_update,
                            flow_start=flow_start,
                        ),
                        indent=2,
                    )
                )
                retry_purchase_result = transferto_client.topup_data(
                    msisdn, option, simulate=False
                )
                log.info(json.dumps(retry_purchase_result, indent=2))
                if retry_purchase_result["status"] == "0":
                    if user_uuid:
                        take_action(
                            org,
                            user_uuid,
                            values_to_update=values_to_update,
                            call_result=retry_purchase_result,
                            flow_start=flow_start,
                        )
                    return None
            subject = "FAILURE WITH RETRIES: {} {}".format(name, timezone.now())
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
            email = EmailMessage(subject, message, from_string, [org.point_of_contact])
            email.send()
            return None

        subject = "FAILURE: {}".format(name)
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
        email = EmailMessage(subject, message, from_string, [org.point_of_contact])
        email.send()

    else:
        if user_uuid:
            take_action(
                org,
                user_uuid,
                values_to_update=values_to_update,
                call_result=purchase_result,
                flow_start=flow_start,
            )


@app.task()
def buy_airtime_take_action(
    topup_attempt_id, values_to_update={}, flow_start=None, fail_flow_start=None
):
    """
    Note: operates under the assumption that TopupAttempt has been created
    but make_request has not been called
    """
    name = "rp_transferto.tasks.buy_airtime_take_action"
    topup_attempt = TopupAttempt.objects.get(id=topup_attempt_id)
    # log.info("{}\n{}".format(self.name, topup_attempt.__str__()))

    topup_attempt.make_request()

    topup_attempt.refresh_from_db()
    log.info(json.dumps(topup_attempt.response, indent=2))

    # take action
    topup_attempt_failed = topup_attempt.status == TopupAttempt.FAILED
    should_update_fields = (
        True if (values_to_update and topup_attempt.rapidpro_user_uuid) else False
    )
    should_start_success_flow = (
        True
        if (
            topup_attempt.status == TopupAttempt.SUCEEDED
            and flow_start
            and topup_attempt.rapidpro_user_uuid
        )
        else False
    )
    should_start_fail_flow = (
        True
        if (
            topup_attempt.status == TopupAttempt.FAILED
            and fail_flow_start
            and topup_attempt.rapidpro_user_uuid
        )
        else False
    )

    if should_update_fields:
        try:
            update_values(
                org=topup_attempt.org,
                user_uuid=topup_attempt.rapidpro_user_uuid,
                values_to_update=values_to_update,
                transferto_response=topup_attempt.response,
            )
            update_fields_successful = True
            update_fields_exception = None
        except Exception as e:
            update_fields_successful = False
            update_fields_exception = e

    if should_start_success_flow:
        try:
            start_flow(
                org=topup_attempt.org,
                user_uuid=topup_attempt.rapidpro_user_uuid,
                flow_uuid=flow_start,
            )
            success_flow_started = True
            success_flow_started_exception = None
        except Exception as e:
            success_flow_started = False
            success_flow_started_exception = e

    if should_start_fail_flow:
        try:
            start_flow(
                org=topup_attempt.org,
                user_uuid=topup_attempt.rapidpro_user_uuid,
                flow_uuid=fail_flow_start,
            )
            fail_flow_started = True
            fail_flow_started_exception = None
        except Exception as e:
            fail_flow_started = False
            fail_flow_started_exception = e

    # report errors
    if (
        topup_attempt_failed
        or (should_update_fields and not update_fields_successful)
        or (should_start_success_flow and not success_flow_started)
        or (should_start_fail_flow and not fail_flow_started)
    ):
        can_send_email = (
            hasattr(settings, "EMAIL_HOST_PASSWORD")
            and hasattr(settings, "EMAIL_HOST_USER")
            and settings.EMAIL_HOST_PASSWORD != ""
            and settings.EMAIL_HOST_USER != ""
            and topup_attempt.org.point_of_contact
        )
        if can_send_email:
            context = {
                "org_name": topup_attempt.org.name,
                "task_name": name,
                "topup_attempt_failed": topup_attempt_failed,
                "topup_attempt": json2html.convert(json.loads(topup_attempt.__str__())),
                "values_to_update": json2html.convert(values_to_update),
                "flow_start": (
                    get_flow_url(topup_attempt.org, flow_start) if flow_start else None
                ),
                "fail_flow_start": (
                    get_flow_url(topup_attempt.org, fail_flow_start)
                    if fail_flow_start
                    else None
                ),
                "should_update_fields": should_update_fields,
                "should_start_success_flow": should_start_success_flow,
                "should_start_fail_flow": should_start_fail_flow,
            }
            if should_update_fields:
                context.update(
                    {
                        "update_fields_successful": update_fields_successful,
                        "update_fields_exception": update_fields_exception,
                    }
                )

            if should_start_success_flow:
                context.update(
                    {
                        "success_flow_started": success_flow_started,
                        "success_flow_started_exception": success_flow_started_exception,
                    }
                )

            if should_start_fail_flow:
                context.update(
                    {
                        "fail_flow_started": fail_flow_started,
                        "fail_flow_started_exception": fail_flow_started_exception,
                    }
                )
            html_message = render_to_string(
                "rp_transferto/topup_airtime_take_action_email.html", context
            )
            send_mail(
                subject="FAILURE: {}".format(name),
                message=strip_tags(html_message),
                from_email="celery@rp-sidekick.prd.mhealthengagementlab.org",
                recipient_list=[topup_attempt.org.point_of_contact],
                html_message=html_message,
            )
        else:
            raise Exception("Error From TransferTo")
