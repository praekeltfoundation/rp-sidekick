from mock import patch
from unittest.mock import MagicMock
from django.test import TestCase, override_settings

from temba_client.v2 import TembaClient

from rp_transferto.tasks import topup_data
from rp_transferto.utils import TransferToClient, TransferToClient2

from .constants import (
    MSISDN_INFO_RESPONSE_DICT,
    GET_PRODUCTS_RESPONSE_DICT,
    POST_TOPUP_DATA_RESPONSE,
)

fake_get_misisdn_info = MagicMock(return_value=MSISDN_INFO_RESPONSE_DICT)
fake_get_operator_products = MagicMock(return_value=GET_PRODUCTS_RESPONSE_DICT)
fake_topup_data = MagicMock(return_value=POST_TOPUP_DATA_RESPONSE)
fake_get_contacts_query = MagicMock()
fake_get_contacts_query.first.return_value = {}
fake_update_contact = MagicMock(return_value={})


@patch.object(TransferToClient, "get_misisdn_info", fake_get_misisdn_info)
@patch.object(
    TransferToClient2, "get_operator_products", fake_get_operator_products
)
@patch.object(TransferToClient2, "topup_data", fake_topup_data)
@patch.object(TembaClient, "get_contacts", fake_get_contacts_query)
@patch.object(TembaClient, "update_contact", fake_update_contact)
@override_settings(
    TRANSFERTO_LOGIN="fake_transferto_login",
    TRANSFERTO_TOKEN="fake_transferto_token",
    TRANSFERTO_APIKEY="fake_transferto_apikey",
    TRANSFERTO_APISECRET="fake_transferto_apisecret",
)
class TestTopupDataTask(TestCase):
    def setUp(self):
        pass

    def test_successsful_run(self):
        # check nothing has been called
        self.assertFalse(fake_get_misisdn_info.called)
        self.assertFalse(fake_get_operator_products.called)
        self.assertFalse(fake_topup_data.called)
        self.assertFalse(fake_get_contacts_query.called)
        self.assertFalse(fake_update_contact.called)

        # run the task
        msisdn = "+27820000000"
        user_uuid = "1234-abc"
        recharge_value = "1GB"
        topup_data(msisdn, user_uuid, recharge_value)

        # check that functions were called
        self.assertTrue(fake_get_misisdn_info.called)
        self.assertTrue(fake_get_operator_products.called)
        self.assertTrue(fake_topup_data.called)
        self.assertTrue(fake_get_contacts_query.called)
        self.assertTrue(fake_update_contact.called)
