from unittest.mock import MagicMock, patch

from django.test import TestCase

from sidekick.models import GroupMonitor
from sidekick.tasks import (
    add_label_to_turn_conversation,
    archive_turn_conversation,
    check_rapidpro_group_membership_count,
)
from sidekick.tests.utils import create_org


class AddLabelToTurnConversationTests(TestCase):
    def setUp(self):
        self.org = create_org()

    @patch("sidekick.tasks.label_whatsapp_message")
    @patch("sidekick.tasks.get_whatsapp_contact_messages")
    def test_inbound_filtering_and_sorting(self, get_messages, label_message):
        """
        It should only look at inbound messages, and pick the latest one
        """
        get_messages.return_value = {
            "messages": [
                {
                    "_vnd": {"v1": {"direction": "outbound"}},
                    "id": "ignore-outbound",
                    "timestamp": "1",
                },
                {
                    "_vnd": {"v1": {"direction": "inbound"}},
                    "id": "first-inbound",
                    "timestamp": "2",
                },
                {
                    "_vnd": {"v1": {"direction": "inbound"}},
                    "id": "second-inbound",
                    "timestamp": "3",
                },
            ]
        }
        label_message.return_value = {}

        add_label_to_turn_conversation(self.org.id, "27820001001", ["label1", "label2"])

        get_messages.assert_called_once_with(self.org, "27820001001")
        label_message.assert_called_once_with(
            self.org, "second-inbound", ["label1", "label2"]
        )


class ArchiveTurnConversationTests(TestCase):
    def setUp(self):
        self.org = create_org()

    @patch("sidekick.tasks.archive_whatsapp_conversation")
    @patch("sidekick.tasks.get_whatsapp_contact_messages")
    def test_get_last_message(self, get_messages, archive):
        """
        It should archive the conversation to the message with the greatest timestamp
        """
        get_messages.return_value = {
            "messages": [
                {
                    "_vnd": {"v1": {"direction": "outbound"}},
                    "id": "ignore-outbound",
                    "timestamp": "1",
                },
                {
                    "_vnd": {"v1": {"direction": "inbound"}},
                    "id": "first-inbound",
                    "timestamp": "2",
                },
                {
                    "_vnd": {"v1": {"direction": "inbound"}},
                    "id": "second-inbound",
                    "timestamp": "3",
                },
                {
                    "_vnd": {"v1": {"direction": "outbound"}},
                    "id": "ignore-outbound-2",
                    "timestamp": "4",
                },
            ]
        }
        archive.return_value = {}

        archive_turn_conversation(self.org.id, "27820001001", "Test reason")

        get_messages.assert_called_once_with(self.org, "27820001001")
        archive.assert_called_once_with(
            self.org, "27820001001", "second-inbound", "Test reason"
        )


class CheckRapidproGroupMembershipCountTests(TestCase):
    def setUp(self):
        self.org = create_org()

    def create_group_monitor(self, minimum=0, triggered=False):
        return GroupMonitor.objects.create(
            org_id=self.org.id,
            group_name="Test participants",
            minimum_count=minimum,
            triggered=triggered,
        )

    def create_rapidpro_group_mock(self, group_membership_count):
        fake_group_object = MagicMock()
        fake_group_object.count = group_membership_count

        fake_query_obj = MagicMock()
        fake_query_obj.first.return_value = fake_group_object
        return fake_query_obj

    @patch("sidekick.tasks.raise_group_membership_error")
    @patch("temba_client.v2.TembaClient.get_groups", autospec=True)
    def test_group_monitor_dont_trigger(self, mock_get_groups, mock_raise_group_error):
        """
        If the group has more members than the minimum count don't trigger
        """
        mock_get_groups.return_value = self.create_rapidpro_group_mock(10)

        monitor = self.create_group_monitor()

        check_rapidpro_group_membership_count()

        self.assertFalse(monitor.triggered)
        mock_raise_group_error.delay.assert_not_called()

    @patch("sidekick.tasks.raise_group_membership_error")
    @patch("temba_client.v2.TembaClient.get_groups", autospec=True)
    def test_group_monitor_trigger(self, mock_get_groups, mock_raise_group_error):
        """
        If the group has less members than the minimum count then trigger
        """
        mock_get_groups.return_value = self.create_rapidpro_group_mock(0)

        monitor = self.create_group_monitor()

        check_rapidpro_group_membership_count()

        monitor.refresh_from_db()
        self.assertTrue(monitor.triggered)

        mock_raise_group_error.delay.assert_called_with(
            "Org: Test Organization - Test participants group is empty"
        )

    @patch("sidekick.tasks.raise_group_membership_error")
    @patch("temba_client.v2.TembaClient.get_groups", autospec=True)
    def test_group_monitor_already_triggered(
        self, mock_get_groups, mock_raise_group_error
    ):
        """
        If the monitor is already triggered on't triggered again
        """
        mock_get_groups.return_value = self.create_rapidpro_group_mock(0)

        monitor = self.create_group_monitor(triggered=True)

        check_rapidpro_group_membership_count()

        monitor.refresh_from_db()
        self.assertTrue(monitor.triggered)

        mock_raise_group_error.delay.assert_not_called()

    @patch("sidekick.tasks.raise_group_membership_error")
    @patch("temba_client.v2.TembaClient.get_groups", autospec=True)
    def test_group_monitor_reset_triggered(
        self, mock_get_groups, mock_raise_group_error
    ):
        """
        If the monitor is triggered and the membership count is more than the minimum,
        reset the triggered flag
        """
        mock_get_groups.return_value = self.create_rapidpro_group_mock(10)

        monitor = self.create_group_monitor(triggered=True)

        check_rapidpro_group_membership_count()

        monitor.refresh_from_db()
        self.assertFalse(monitor.triggered)

        mock_raise_group_error.delay.assert_not_called()
