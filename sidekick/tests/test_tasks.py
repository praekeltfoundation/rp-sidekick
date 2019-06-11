from unittest.mock import patch

from django.test import TestCase

from sidekick.tasks import add_label_to_turn_conversation, archive_turn_conversation
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
