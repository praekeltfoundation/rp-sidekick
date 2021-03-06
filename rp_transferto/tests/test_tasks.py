from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.test.utils import override_settings
from pytest import raises

from rp_transferto.models import MsisdnInformation, TopupAttempt
from rp_transferto.tasks import (
    buy_airtime_take_action,
    buy_product_take_action,
    start_flow,
    take_action,
    topup_data,
    update_values,
)
from sidekick.tests.utils import create_org
from sidekick.utils import clean_msisdn

from .constants import (
    GET_PRODUCTS_RESPONSE_DICT,
    MSISDN_INFO_RESPONSE_DICT,
    POST_TOPUP_DATA_RESPONSE,
    TOPUP_ERROR_RESPONSE_DICT,
    TOPUP_RESPONSE_DICT,
)
from .utils import create_transferto_account


class TestFunctions(TestCase):
    def setUp(self):
        self.org = create_org()

    @patch("temba_client.v2.TembaClient.update_contact")
    def test_take_action_update_fields(self, fake_update_contact):
        user_uuid = "3333-abc"
        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }
        call_result = POST_TOPUP_DATA_RESPONSE
        take_action(self.org, user_uuid, values_to_update, call_result, flow_start=None)
        fake_update_contact.assert_called_with(
            user_uuid,
            fields={
                "rp_0001_01_transferto_status": POST_TOPUP_DATA_RESPONSE["status"],
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

        take_action(self.org, user_uuid, flow_start=flow_uuid)

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
            self.org, user_uuid, values_to_update, call_result, flow_start=flow_uuid
        )
        fake_update_contact.assert_called_with(
            user_uuid,
            fields={
                "rp_0001_01_transferto_status": POST_TOPUP_DATA_RESPONSE["status"],
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
    def test_update_values_success(self, fake_update_contact):
        user_uuid = "3333-abc"
        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }
        call_result = POST_TOPUP_DATA_RESPONSE
        update_values(self.org, user_uuid, values_to_update, call_result)
        fake_update_contact.assert_called_with(
            user_uuid,
            fields={
                "rp_0001_01_transferto_status": POST_TOPUP_DATA_RESPONSE["status"],
                "rp_0001_01_transferto_status_message": POST_TOPUP_DATA_RESPONSE[
                    "status_message"
                ],
                "rp_0001_01_transferto_product_desc": POST_TOPUP_DATA_RESPONSE[
                    "product_desc"
                ],
            },
        )

    @patch("temba_client.v2.TembaClient.update_contact")
    def test_update_values_missing_values(self, fake_update_contact):
        user_uuid = "3333-abc"
        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }
        call_result = dict(POST_TOPUP_DATA_RESPONSE)
        del call_result["status_message"]
        update_values(self.org, user_uuid, values_to_update, call_result)
        fake_update_contact.assert_called_with(
            user_uuid,
            fields={
                "rp_0001_01_transferto_status": POST_TOPUP_DATA_RESPONSE["status"],
                "rp_0001_01_transferto_status_message": "NONE",
                "rp_0001_01_transferto_product_desc": POST_TOPUP_DATA_RESPONSE[
                    "product_desc"
                ],
            },
        )

    @patch("temba_client.v2.TembaClient.create_flow_start")
    def test_start_flow(self, fake_create_flow_start):
        user_uuid = "3333-abc"
        flow_uuid = "123412341234"

        start_flow(self.org, user_uuid, flow_uuid)

        fake_create_flow_start.assert_called_with(
            flow_uuid, contacts=[user_uuid], restart_participants=True
        )


@patch("temba_client.v2.TembaClient.update_contact")
@patch("temba_client.v2.TembaClient.get_contacts")
@patch("rp_transferto.utils.TransferToClient.topup_data")
@patch("rp_transferto.utils.TransferToClient.get_operator_products")
@patch("rp_transferto.utils.TransferToClient.get_misisdn_info")
class TestTopupDataTask(TestCase):
    def setUp(self):
        self.org = create_org()
        self.transferto_account = create_transferto_account(org=self.org)

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
        org_id = self.org.id
        msisdn = "+27820000000"
        user_uuid = "1234-abc"
        recharge_value = "1GB"

        # run the task
        topup_data(org_id, msisdn, user_uuid, recharge_value)

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
        org_id = self.org.id
        msisdn = "+27820000000"
        user_uuid = "1234-abc"
        recharge_value = "1GB"

        MsisdnInformation.objects.create(msisdn=msisdn, data=MSISDN_INFO_RESPONSE_DICT)

        # run the task
        topup_data(org_id, msisdn, user_uuid, recharge_value)

        # check that external call was NOT made
        self.assertFalse(fake_get_misisdn_info.called)
        # check that functions were called
        self.assertTrue(fake_get_operator_products.called)
        self.assertTrue(fake_topup_data.called)
        self.assertTrue(fake_get_contacts.called)
        self.assertTrue(fake_update_contact.called)


class TestBuyProductTakeActionTask(TestCase):
    def setUp(self):
        self.org = create_org()
        self.transferto_account = create_transferto_account(org=self.org)

    @patch("rp_transferto.tasks.take_action")
    @patch("rp_transferto.utils.TransferToClient.topup_data")
    def test_successsful_run_simple(self, fake_topup_data, fake_take_action):
        fake_topup_data.return_value = POST_TOPUP_DATA_RESPONSE
        self.assertFalse(fake_topup_data.called)
        self.assertFalse(fake_take_action.called)

        msisdn = "+27820000001"
        product_id = 111
        buy_product_take_action(self.org.id, msisdn, product_id)

        self.assertTrue(fake_topup_data.called)
        fake_topup_data.assert_called_with(msisdn, product_id, simulate=False)
        self.assertFalse(fake_take_action.called)

    @patch("rp_transferto.tasks.take_action")
    @patch("rp_transferto.utils.TransferToClient.topup_data")
    def test_successsful_run_update_fields(self, fake_topup_data, fake_take_action):
        fake_topup_data.return_value = POST_TOPUP_DATA_RESPONSE
        self.assertFalse(fake_topup_data.called)
        self.assertFalse(fake_take_action.called)

        msisdn = "+27820000001"
        product_id = 333
        user_uuid = "3333-abc"
        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }

        buy_product_take_action(
            self.org.id,
            msisdn,
            product_id,
            user_uuid=user_uuid,
            values_to_update=values_to_update,
        )

        fake_topup_data.assert_called_with(msisdn, product_id, simulate=False)
        self.assertTrue(fake_take_action.called)
        fake_take_action.assert_called_with(
            self.org,
            user_uuid,
            values_to_update=values_to_update,
            call_result=POST_TOPUP_DATA_RESPONSE,
            flow_start=None,
        )

    @patch("rp_transferto.tasks.take_action")
    @patch("rp_transferto.utils.TransferToClient.topup_data")
    def test_successsful_run_start_flow(self, fake_topup_data, fake_take_action):
        fake_topup_data.return_value = POST_TOPUP_DATA_RESPONSE
        self.assertFalse(fake_topup_data.called)
        self.assertFalse(fake_take_action.called)

        msisdn = "+27820006000"
        product_id = 444
        user_uuid = "4444-abc"
        flow_uuid = "123412341234"

        buy_product_take_action(
            self.org.id, msisdn, product_id, user_uuid=user_uuid, flow_start=flow_uuid
        )

        fake_topup_data.assert_called_with(msisdn, product_id, simulate=False)
        self.assertTrue(fake_take_action.called)
        fake_take_action.assert_called_with(
            self.org,
            user_uuid,
            values_to_update={},
            call_result=POST_TOPUP_DATA_RESPONSE,
            flow_start=flow_uuid,
        )


class TestBuyAirtimeTakeAction(TestCase):
    def setUp(self):
        self.org = create_org()
        self.transferto_account = create_transferto_account(org=self.org)

    @patch("rp_transferto.tasks.update_values")
    @patch("rp_transferto.tasks.start_flow")
    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_successsful_run_simple(
        self, fake_make_topup, fake_start_flow, fake_update_values
    ):
        fake_make_topup.return_value = TOPUP_RESPONSE_DICT
        self.assertFalse(fake_make_topup.called)
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)

        msisdn = "+27820000001"
        airtime_amount = 111
        from_string = "bob"
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn, from_string=from_string, amount=airtime_amount, org=self.org
        )
        buy_airtime_take_action(topup_attempt.id)

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)

    @patch("rp_transferto.tasks.update_values")
    @patch("rp_transferto.tasks.start_flow")
    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_successsful_run_update_fields(
        self, fake_make_topup, fake_start_flow, fake_update_values
    ):
        fake_make_topup.return_value = TOPUP_RESPONSE_DICT
        self.assertFalse(fake_make_topup.called)
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)

        msisdn = "+27820000001"
        airtime_amount = 333
        from_string = "bob"
        user_uuid = "3333-abc"
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
            rapidpro_user_uuid=user_uuid,
        )

        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }

        buy_airtime_take_action(topup_attempt.id, values_to_update=values_to_update)

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )
        self.assertFalse(fake_start_flow.called)
        self.assertTrue(fake_update_values.called)
        fake_update_values.assert_called_with(
            org=self.org,
            user_uuid=user_uuid,
            values_to_update=values_to_update,
            transferto_response=TOPUP_RESPONSE_DICT,
        )

    @patch("rp_transferto.tasks.update_values")
    @patch("rp_transferto.tasks.start_flow")
    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_successsful_run_start_flow(
        self, fake_make_topup, fake_start_flow, fake_update_values
    ):
        fake_make_topup.return_value = TOPUP_RESPONSE_DICT
        self.assertFalse(fake_make_topup.called)
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)

        msisdn = "+27820006000"
        airtime_amount = 444
        from_string = "bob"
        user_uuid = "4444-abc"
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
            rapidpro_user_uuid=user_uuid,
        )

        flow_uuid = "123412341234"

        buy_airtime_take_action(topup_attempt.id, flow_start=flow_uuid)

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )
        self.assertFalse(fake_update_values.called)
        self.assertTrue(fake_start_flow.called)
        fake_start_flow.assert_called_with(
            org=self.org, user_uuid=user_uuid, flow_uuid=flow_uuid
        )

    @patch("rp_transferto.tasks.update_values")
    @patch("rp_transferto.tasks.start_flow")
    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_unsuccesssful_run_start_fail_flow(
        self, fake_make_topup, fake_start_flow, fake_update_values
    ):
        fake_make_topup.return_value = TOPUP_ERROR_RESPONSE_DICT
        self.assertFalse(fake_make_topup.called)
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)

        msisdn = "+27820006000"
        airtime_amount = 444
        from_string = "bob"
        user_uuid = "4444-abc"
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
            rapidpro_user_uuid=user_uuid,
        )

        flow_uuid = "123412341234"
        fail_flow_uuid = "098709870987"

        with raises(Exception) as exception:
            buy_airtime_take_action(
                topup_attempt.id, flow_start=flow_uuid, fail_flow_start=fail_flow_uuid
            )

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )
        self.assertFalse(fake_update_values.called)
        self.assertTrue(fake_start_flow.called)
        fake_start_flow.assert_called_with(
            org=self.org, user_uuid=user_uuid, flow_uuid=fail_flow_uuid
        )
        self.assertEqual(exception.value.__str__(), "Error From TransferTo")

    @override_settings(EMAIL_HOST_PASSWORD="EMAIL_HOST_PASSWORD")
    @override_settings(EMAIL_HOST_USER="EMAIL_HOST_USER")
    @patch("django.core.mail.EmailMessage.send")
    @patch("rp_transferto.tasks.update_values")
    @patch("rp_transferto.tasks.start_flow")
    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_unsuccesssful_run_email(
        self, fake_make_topup, fake_start_flow, fake_update_values, fake_send
    ):
        fake_make_topup.return_value = TOPUP_ERROR_RESPONSE_DICT
        self.org.point_of_contact = "test@example.org"
        self.org.save()

        self.assertFalse(fake_make_topup.called)
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)
        self.assertFalse(fake_send.called)

        msisdn = TOPUP_ERROR_RESPONSE_DICT["destination_msisdn"]
        airtime_amount = 333
        from_string = "bob"
        user_uuid = "3333-abc"
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
            rapidpro_user_uuid=user_uuid,
        )

        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }

        flow_uuid = "123412341234"

        buy_airtime_take_action(
            topup_attempt.id, values_to_update=values_to_update, flow_start=flow_uuid
        )

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )
        fake_update_values.assert_called_with(
            org=self.org,
            user_uuid=user_uuid,
            values_to_update=values_to_update,
            transferto_response=TOPUP_ERROR_RESPONSE_DICT,
        )
        self.assertFalse(fake_start_flow.called)
        self.assertTrue(fake_send.called)

    @override_settings(EMAIL_HOST_USER=None)
    @patch("django.core.mail.EmailMessage.send")
    @patch("rp_transferto.tasks.update_values")
    @patch("rp_transferto.tasks.start_flow")
    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_unsuccesssful_run_exception(
        self, fake_make_topup, fake_start_flow, fake_update_values, fake_send
    ):
        fake_make_topup.return_value = TOPUP_ERROR_RESPONSE_DICT

        self.assertFalse(fake_make_topup.called)
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)
        self.assertFalse(fake_send.called)

        msisdn = TOPUP_ERROR_RESPONSE_DICT["destination_msisdn"]
        airtime_amount = 333
        from_string = "bob"
        user_uuid = "3333-abc"
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
            rapidpro_user_uuid=user_uuid,
        )

        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }
        flow_uuid = "123412341234"
        fail_flow_uuid = "098709870987"

        with raises(Exception) as exception:
            buy_airtime_take_action(
                topup_attempt.id,
                values_to_update=values_to_update,
                flow_start=flow_uuid,
                fail_flow_start=fail_flow_uuid,
            )

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )
        self.assertFalse(fake_send.called)
        fake_start_flow.assert_called_with(
            org=self.org, user_uuid=user_uuid, flow_uuid=fail_flow_uuid
        )
        fake_update_values.assert_called_with(
            org=self.org,
            user_uuid=user_uuid,
            values_to_update=values_to_update,
            transferto_response=TOPUP_ERROR_RESPONSE_DICT,
        )
        self.assertEqual(exception.value.__str__(), "Error From TransferTo")

    @override_settings(EMAIL_HOST_PASSWORD="EMAIL_HOST_PASSWORD")
    @override_settings(EMAIL_HOST_USER="EMAIL_HOST_USER")
    @patch("django.core.mail.EmailMessage.send")
    @patch("rp_transferto.tasks.update_values")
    @patch("rp_transferto.tasks.start_flow")
    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_successsful_run_start_flow_throw_exception2(
        self, fake_make_topup, fake_start_flow, fake_update_values, fake_send
    ):
        self.org.point_of_contact = "test@example.org"
        self.org.save()

        fake_make_topup.return_value = TOPUP_RESPONSE_DICT
        fake_start_flow.side_effect = Exception("something is wrong")
        self.assertFalse(fake_make_topup.called)
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)

        msisdn = "+27820006000"
        airtime_amount = 444
        from_string = "bob"
        user_uuid = "4444-abc"
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
            rapidpro_user_uuid=user_uuid,
        )

        flow_uuid = "123412341234"

        buy_airtime_take_action(topup_attempt.id, flow_start=flow_uuid)

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )
        self.assertFalse(fake_update_values.called)
        self.assertTrue(fake_start_flow.called)
        fake_start_flow.assert_called_with(
            org=self.org, user_uuid=user_uuid, flow_uuid=flow_uuid
        )
        self.assertTrue(fake_send.called)

    @override_settings(EMAIL_HOST_PASSWORD="EMAIL_HOST_PASSWORD")
    @override_settings(EMAIL_HOST_USER="EMAIL_HOST_USER")
    @patch("django.core.mail.EmailMessage.send")
    @patch("rp_transferto.tasks.update_values")
    @patch("rp_transferto.tasks.start_flow")
    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_successsful_run_start_flow_throw_exception(
        self, fake_make_topup, fake_start_flow, fake_update_values, fake_send
    ):
        self.org.point_of_contact = "test@example.org"
        self.org.save()

        fake_make_topup.return_value = TOPUP_RESPONSE_DICT
        fake_start_flow.side_effect = Exception("something is wrong")
        self.assertFalse(fake_make_topup.called)
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)

        msisdn = "+27820006000"
        airtime_amount = 444
        from_string = "bob"
        user_uuid = "4444-abc"
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
            rapidpro_user_uuid=user_uuid,
        )

        flow_uuid = "123412341234"

        buy_airtime_take_action(topup_attempt.id, flow_start=flow_uuid)

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )
        self.assertFalse(fake_update_values.called)
        self.assertTrue(fake_start_flow.called)
        fake_start_flow.assert_called_with(
            org=self.org, user_uuid=user_uuid, flow_uuid=flow_uuid
        )
        self.assertTrue(fake_send.called)

    @override_settings(EMAIL_HOST_PASSWORD="EMAIL_HOST_PASSWORD")
    @override_settings(EMAIL_HOST_USER="EMAIL_HOST_USER")
    @patch("django.core.mail.EmailMessage.send")
    @patch("rp_transferto.tasks.update_values")
    @patch("rp_transferto.tasks.start_flow")
    @patch("rp_transferto.utils.TransferToClient.make_topup")
    def test_unsuccesssful_run_start_flow_throw_exception(
        self, fake_make_topup, fake_start_flow, fake_update_values, fake_send
    ):
        self.org.point_of_contact = "test@example.org"
        self.org.save()

        fake_make_topup.return_value = TOPUP_ERROR_RESPONSE_DICT
        fake_update_values.side_effect = Exception("something goes wrong")
        fake_start_flow.side_effect = Exception("something is wrong")
        self.assertFalse(fake_make_topup.called)
        self.assertFalse(fake_start_flow.called)
        self.assertFalse(fake_update_values.called)

        msisdn = "+27820006000"
        airtime_amount = 444
        from_string = "bob"
        user_uuid = "4444-abc"
        topup_attempt = TopupAttempt.objects.create(
            msisdn=msisdn,
            from_string=from_string,
            amount=airtime_amount,
            org=self.org,
            rapidpro_user_uuid=user_uuid,
        )

        values_to_update = {
            "rp_0001_01_transferto_status": "status",
            "rp_0001_01_transferto_status_message": "status_message",
            "rp_0001_01_transferto_product_desc": "product_desc",
        }

        flow_uuid = "123412341234"
        fail_flow_uuid = "098709870987"

        buy_airtime_take_action(
            topup_attempt.id,
            values_to_update=values_to_update,
            flow_start=flow_uuid,
            fail_flow_start=fail_flow_uuid,
        )

        fake_make_topup.assert_called_with(
            clean_msisdn(msisdn), airtime_amount, from_string
        )
        fake_update_values.assert_called_with(
            org=self.org,
            user_uuid=user_uuid,
            values_to_update=values_to_update,
            transferto_response=TOPUP_ERROR_RESPONSE_DICT,
        )
        self.assertTrue(fake_start_flow.called)
        fake_start_flow.assert_called_with(
            org=self.org, user_uuid=user_uuid, flow_uuid=fail_flow_uuid
        )
        self.assertTrue(fake_send.called)
