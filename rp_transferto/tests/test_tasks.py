from mock import patch
from unittest.mock import MagicMock
from django.test import TestCase, override_settings

from rp_transferto.tasks import topup_data
from rp_transferto.models import MsisdnInformation

from .constants import (
    MSISDN_INFO_RESPONSE_DICT,
    GET_PRODUCTS_RESPONSE_DICT,
    POST_TOPUP_DATA_RESPONSE,
)


@patch("temba_client.v2.TembaClient.update_contact")
@patch("temba_client.v2.TembaClient.get_contacts")
@patch("rp_transferto.utils.TransferToClient2.topup_data")
@patch("rp_transferto.utils.TransferToClient2.get_operator_products")
@patch("rp_transferto.utils.TransferToClient.get_misisdn_info")
@override_settings(
    TRANSFERTO_LOGIN="fake_transferto_login",
    TRANSFERTO_TOKEN="fake_transferto_token",
    TRANSFERTO_APIKEY="fake_transferto_apikey",
    TRANSFERTO_APISECRET="fake_transferto_apisecret",
)
class TestTopupDataTask(TestCase):
    def test_successsful_run(
        self,
        fake_get_misisdn_info,
        fake_get_operator_products,
        fake_topup_data,
        fake_get_contacts,
        fake_update_contact,
    ):
        fake_get_misisdn_info.return_value = MSISDN_INFO_RESPONSE_DICT
        fake_get_operator_products.return_value = GET_PRODUCTS_RESPONSE_DICT
        fake_topup_data.return_value = POST_TOPUP_DATA_RESPONSE

        fake_query_obj = MagicMock()
        fake_query_obj.first.return_value = "fake_contact_object"

        fake_get_contacts.return_value = fake_query_obj

        # check nothing has been called
        self.assertFalse(fake_get_misisdn_info.called)
        self.assertFalse(fake_get_operator_products.called)
        self.assertFalse(fake_topup_data.called)
        self.assertFalse(fake_get_contacts.called)
        self.assertFalse(fake_update_contact.called)

        # create test variables
        msisdn = "+27820000000"
        user_uuid = "1234-abc"
        recharge_value = "1GB"

        # run the task
        topup_data(msisdn, user_uuid, recharge_value)

        # check that functions were called
        self.assertTrue(fake_get_misisdn_info.called)
        self.assertTrue(fake_get_operator_products.called)
        self.assertTrue(fake_topup_data.called)
        self.assertTrue(fake_get_contacts.called)
        self.assertTrue(fake_update_contact.called)

    def test_successsful_run_with_cached_msisdn(
        self,
        fake_get_misisdn_info,
        fake_get_operator_products,
        fake_topup_data,
        fake_get_contacts,
        fake_update_contact,
    ):
        fake_get_misisdn_info.return_value = MSISDN_INFO_RESPONSE_DICT
        fake_get_operator_products.return_value = GET_PRODUCTS_RESPONSE_DICT
        fake_topup_data.return_value = POST_TOPUP_DATA_RESPONSE

        fake_query_obj = MagicMock()
        fake_query_obj.first.return_value = "fake_contact_object"

        fake_get_contacts.return_value = fake_query_obj

        # check nothing has been called
        self.assertFalse(fake_get_misisdn_info.called)
        self.assertFalse(fake_get_operator_products.called)
        self.assertFalse(fake_topup_data.called)
        self.assertFalse(fake_get_contacts.called)
        self.assertFalse(fake_update_contact.called)

        # create test variables
        msisdn = "+27820000000"
        user_uuid = "1234-abc"
        recharge_value = "1GB"

        MsisdnInformation.objects.create(
            msisdn=msisdn, data=MSISDN_INFO_RESPONSE_DICT
        )

        # run the task
        topup_data(msisdn, user_uuid, recharge_value)

        # check that external call was NOT made
        self.assertFalse(fake_get_misisdn_info.called)
        # check that functions were called
        self.assertTrue(fake_get_operator_products.called)
        self.assertTrue(fake_topup_data.called)
        self.assertTrue(fake_get_contacts.called)
        self.assertTrue(fake_update_contact.called)
