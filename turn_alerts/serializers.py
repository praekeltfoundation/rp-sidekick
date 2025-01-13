from rest_framework import serializers

"""
Serializer for delivery failure status payload
"""


class ErrorSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    title = serializers.CharField()


class StatusErrorSerializer(serializers.Serializer):
    id = serializers.CharField()
    recipient_id = serializers.CharField()
    status = serializers.CharField()
    timestamp = serializers.IntegerField()
    errors = ErrorSerializer(many=True, required=False)


class Status_ErrorPayloadSerializer(serializers.Serializer):
    statuses = StatusErrorSerializer(many=True)

    def get_error_code(self):
        error_code = self.validated_data["statuses"][0]["errors"][0]["code"]
        return error_code

    def get_message_status(self):
        status = self.validated_data["statuses"][0]["status"]
        return status

    def get_recipient_id(self):
        recipient_id = self.validated_data["statuses"][0]["recipient_id"]
        return recipient_id


"""
Serializer for delivered messages status payload
"""


class OriginSerializer(serializers.Serializer):
    type = serializers.CharField()


class PricingSerializer(serializers.Serializer):
    billable = serializers.BooleanField()
    category = serializers.CharField()
    pricing_model = serializers.CharField()


class ConversationSerializer(serializers.Serializer):
    expiration_timestamp = serializers.IntegerField()
    id = serializers.CharField()
    origin = OriginSerializer()


class StatusSerializer(serializers.Serializer):
    conversation = ConversationSerializer()
    id = serializers.CharField()
    recipient_id = serializers.CharField()
    status = serializers.CharField()
    timestamp = serializers.IntegerField()


class StatusPayloadSerializer(serializers.Serializer):
    statuses = StatusSerializer(many=True)

    def get_recipient_id(self):
        recipient_id = self.validated_data["statuses"][0]["recipient_id"]
        return recipient_id

    def get_conversation_type(self):
        conversation_type = self.validated_data["statuses"][0]["conversation"][
            "origin"
        ]["type"]
        return conversation_type

    def get_conversation_id(self):
        conversation_id = self.validated_data["statuses"][0]["conversation"]["id"]
        return conversation_id

    def get_message_status(self):
        status = self.validated_data["statuses"][0]["status"]
        return status


"""
Serializer for vendor messages payload
"""


class VendorAuthorSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    request_id = serializers.CharField()
    type = serializers.CharField()


class VendorAssignedToSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()


class V1Serializer(serializers.Serializer):
    author = VendorAuthorSerializer()
    direction = serializers.CharField()
    on_fallback_channel = serializers.BooleanField()
    rendered_content = serializers.CharField(allow_null=True)


class VendorSerializer(serializers.Serializer):
    v1 = V1Serializer()


class VendorPayloadSerializer(serializers.Serializer):
    _vnd = VendorSerializer()
    type = serializers.CharField()

    def get_message_type(self):
        message_type = self.validated_data["type"]
        return message_type

    def get_direction(self):
        direction = self.validated_data["_vnd"]["v1"]["direction"]
        return direction

    def get_fallback_channel(self):
        fallback_channel = self.validated_data["_vnd"]["v1"]["on_fallback_channel"]
        return fallback_channel


"""
Serializer for contacts payload
"""


class ProfileSerializer(serializers.Serializer):
    name = serializers.CharField()


class AuthorSerializer(serializers.Serializer):
    type = serializers.CharField()


class AssignedToSerializer(serializers.Serializer):
    type = serializers.CharField()


class V1Serializer(serializers.Serializer):
    author = AuthorSerializer()
    direction = serializers.CharField()
    on_fallback_channel = serializers.BooleanField()


class VndSerializer(serializers.Serializer):
    v1 = V1Serializer()


class MessageSerializer(serializers.Serializer):
    _vnd = VndSerializer()

    type = serializers.CharField()


class ContactsPayloadSerializer(serializers.Serializer):
    messages = MessageSerializer(many=True)

    def get_message_type(self):
        message_type = self.validated_data["messages"][0]["type"]
        return message_type

    def get_direction(self):
        direction = self.validated_data["messages"][0]["_vnd"]["v1"]["direction"]
        return direction

    def get_fallback_channel(self):
        fallback_channel = self.validated_data["messages"][0]["_vnd"]["v1"][
            "on_fallback_channel"
        ]
        return fallback_channel
