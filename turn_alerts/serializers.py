from rest_framework import serializers

"""
Serializer for delivery failure status payload
"""


class WhatsAppEventSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    recipient_id = serializers.CharField(required=False)
    status = serializers.CharField()
    code = serializers.IntegerField(required=False)


class WhatsAppInboundMessageSerializer(serializers.Serializer):
    id = serializers.CharField(required=True)
    type = serializers.CharField()


class WhatsAppWebhookSerializer(serializers.Serializer):
    messages = serializers.ListField(
        child=WhatsAppInboundMessageSerializer(), allow_empty=True, required=False
    )
    statuses = serializers.ListField(
        child=WhatsAppEventSerializer(), allow_empty=True, required=False
    )


class TurnOutboundV1Serializer(serializers.Serializer):
    direction = serializers.CharField()
    on_fallback_channel = serializers.BooleanField()
    rendered_content = serializers.CharField(allow_null=True)


class TurnOutboundVndSerializer(serializers.Serializer):
    v1 = TurnOutboundV1Serializer()


class TurnOutboundSerializer(serializers.Serializer):
    to = serializers.CharField()
    _vnd = TurnOutboundVndSerializer()
    type = serializers.CharField()
