from rest_framework import serializers


class RapidProFlowWebhookSerializer(serializers.Serializer):
    """
    A serializer for the parts of a RapidPro Flow Webhook that we need
    """

    class Contact(serializers.Serializer):
        uuid = serializers.UUIDField()

    contact = Contact()
