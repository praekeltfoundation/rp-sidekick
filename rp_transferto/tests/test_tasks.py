from mock import patch
from unittest.mock import MagicMock
from django.test import TestCase

from rp_transferto.tasks import topup_data, buy_product_take_action, take_action
from rp_transferto.models import MsisdnInformation

from .constants import (
    MSISDN_INFO_RESPONSE_DICT,
    GET_PRODUCTS_RESPONSE_DICT,
    POST_TOPUP_DATA_RESPONSE,
)


class TestFunctions(TestCase):
    @patch("temba_client.v2.TembaClient.update_contact")
    def test_take_action_update_fields(self, fake_update_contact):
        user_uuid = "3333-abc"
        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }
        call_result = POST_TOPUP_DATA_RESPONSE
        take_action(user_uuid, values_to_update, call_result, flow_start=None)
        fake_update_contact.assert_called_with(
            user_uuid,
            fields={
                "rp_0001_01_transferto_status": POST_TOPUP_DATA_RESPONSE[
                    "status"
                ],
                "rp_0001_01_transferto_status_message": POST_TOPUP_DATA_RESPONSE[
                    "status_message"
                ],
                "rp_0001_01_transferto_product_desc": POST_TOPUP_DATA_RESPONSE[
                    "product_desc"
                ],
            },
        )

    @patch("temba_client.v2.TembaClient.create_flow_start")
    def test_take_action_start_flow(self, fake_create_flow_start):
        user_uuid = "3333-abc"
        flow_uuid = "123412341234"

        take_action(user_uuid, flow_start=flow_uuid)

        fake_create_flow_start.assert_called_with(
            flow_uuid, contacts=[user_uuid], restart_participants=True
        )

    @patch("temba_client.v2.TembaClient.create_flow_start")
    @patch("temba_client.v2.TembaClient.update_contact")
    def test_take_action_update_fields_start_flow(
        self, fake_update_contact, fake_create_flow_start
    ):
        user_uuid = "3333-abc"
        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }
        flow_uuid = "123412341234"
        call_result = POST_TOPUP_DATA_RESPONSE
        take_action(
            user_uuid, values_to_update, call_result, flow_start=flow_uuid
        )
        fake_update_contact.assert_called_with(
            user_uuid,
            fields={
                "rp_0001_01_transferto_status": POST_TOPUP_DATA_RESPONSE[
                    "status"
                ],
                "rp_0001_01_transferto_status_message": POST_TOPUP_DATA_RESPONSE[
                    "status_message"
                ],
                "rp_0001_01_transferto_product_desc": POST_TOPUP_DATA_RESPONSE[
                    "product_desc"
                ],
            },
        )
        fake_create_flow_start.assert_called_with(
            flow_uuid, contacts=[user_uuid], restart_participants=True
        )


@patch("temba_client.v2.TembaClient.update_contact")
@patch("temba_client.v2.TembaClient.get_contacts")
@patch("rp_transferto.utils.TransferToClient2.topup_data")
@patch("rp_transferto.utils.TransferToClient2.get_operator_products")
@patch("rp_transferto.utils.TransferToClient.get_misisdn_info")
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


class TestBuyProductTakeActionTask(TestCase):
    @patch("temba_client.v2.TembaClient.create_flow_start")
    @patch("temba_client.v2.TembaClient.update_contact")
    @patch("rp_transferto.utils.TransferToClient2.topup_data")
    def test_successsful_run_simple(
        self, fake_topup_data, fake_update_contact, fake_create_flow_start
    ):
        fake_topup_data.return_value = POST_TOPUP_DATA_RESPONSE
        fake_update_contact.return_value = {}
        fake_create_flow_start.return_value = {}

        self.assertFalse(fake_topup_data.called)
        self.assertFalse(fake_update_contact.called)
        self.assertFalse(fake_create_flow_start.called)

        msisdn = "+27820000001"
        product_id = 111
        buy_product_take_action(msisdn, product_id)

        self.assertTrue(fake_topup_data.called)
        fake_topup_data.assert_called_with(msisdn, product_id, simulate=False)
        self.assertFalse(fake_update_contact.called)
        self.assertFalse(fake_create_flow_start.called)

    @patch("temba_client.v2.TembaClient.create_flow_start")
    @patch("temba_client.v2.TembaClient.update_contact")
    @patch("rp_transferto.utils.TransferToClient2.topup_data")
    def test_successsful_run_update_fields(
        self, fake_topup_data, fake_update_contact, fake_create_flow_start
    ):
        fake_topup_data.return_value = POST_TOPUP_DATA_RESPONSE
        self.assertFalse(fake_topup_data.called)
        self.assertFalse(fake_update_contact.called)
        self.assertFalse(fake_create_flow_start.called)

        msisdn = "+27820000001"
        product_id = 333
        user_uuid = "3333-abc"
        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }

        buy_product_take_action(
            msisdn,
            product_id,
            user_uuid=user_uuid,
            values_to_update=values_to_update,
        )

        self.assertTrue(fake_topup_data.called)
        fake_topup_data.assert_called_with(msisdn, product_id, simulate=False)
        self.assertTrue(fake_update_contact.called)
        fake_update_contact.assert_called_with(
            user_uuid,
            fields={
                "rp_0001_01_transferto_status": POST_TOPUP_DATA_RESPONSE[
                    "status"
                ],
                "rp_0001_01_transferto_status_message": POST_TOPUP_DATA_RESPONSE[
                    "status_message"
                ],
                "rp_0001_01_transferto_product_desc": POST_TOPUP_DATA_RESPONSE[
                    "product_desc"
                ],
            },
        )
        self.assertFalse(fake_create_flow_start.called)

    @patch("temba_client.v2.TembaClient.create_flow_start")
    @patch("temba_client.v2.TembaClient.update_contact")
    @patch("rp_transferto.utils.TransferToClient2.topup_data")
    def test_successsful_run_start_flow(
        self, fake_topup_data, fake_update_contact, fake_create_flow_start
    ):
        fake_topup_data.return_value = POST_TOPUP_DATA_RESPONSE
        self.assertFalse(fake_topup_data.called)
        self.assertFalse(fake_update_contact.called)
        self.assertFalse(fake_create_flow_start.called)

        msisdn = "+27820006000"
        product_id = 444
        user_uuid = "4444-abc"
        flow_uuid = "123412341234"

        buy_product_take_action(
            msisdn, product_id, user_uuid=user_uuid, flow_start=flow_uuid
        )

        fake_topup_data.assert_called_with(msisdn, product_id, simulate=False)
        self.assertFalse(fake_update_contact.called)
        self.assertTrue(fake_create_flow_start.called)
        fake_create_flow_start.assert_called_with(
            flow_uuid, contacts=[user_uuid], restart_participants=True
        )
