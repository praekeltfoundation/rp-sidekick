import re

from rest_framework import serializers

URN_REGEX = re.compile(r"(?P<scheme>.+):(?P<address>.+)")


class RapidProFlowWebhookSerializer(serializers.Serializer):
    """
    A serializer for the parts of a RapidPro Flow Webhook that we need
    """

    class Contact(serializers.Serializer):
        uuid = serializers.UUIDField()
        urn = serializers.RegexField(URN_REGEX)

    contact = Contact()


class LabelTurnConversationSerializer(serializers.Serializer):
    """"
    Serializer for the query parameters of the LabelTurnConversationView
    """

    label = serializers.ListField(child=serializers.CharField())
