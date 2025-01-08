from rest_framework import serializers

"""
Serializer for delivery failure status payload
"""


class ErrorSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    title = serializers.CharField()
    error_data = serializers.JSONField()


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

    def get_error_data(self):
        error_data = self.validated_data["statuses"][0]["errors"][0]["error_data"][
            "details"
        ]
        return error_data

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

    def get_message_type(self):
        message_type = self.validated_data["statuses"][0]["conversation"]["origin"][
            "type"
        ]
        return message_type

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


class ChatSerializer(serializers.Serializer):
    assigned_to = VendorAssignedToSerializer()
    contact_uuid = serializers.CharField()
    inserted_at = serializers.DateTimeField()
    owner = serializers.CharField()
    permalink = serializers.URLField()
    state = serializers.CharField()
    state_reason = serializers.CharField()
    unread_count = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
    uuid = serializers.CharField()


class V1Serializer(serializers.Serializer):
    author = VendorAuthorSerializer()
    card_uuid = serializers.CharField(allow_null=True)
    chat = ChatSerializer()
    direction = serializers.CharField()
    faq_uuid = serializers.CharField(allow_null=True)
    in_reply_to = serializers.CharField(allow_null=True)
    inserted_at = serializers.DateTimeField()
    labels = serializers.ListField(child=serializers.CharField(), required=False)
    last_status = serializers.CharField(allow_null=True)
    last_status_timestamp = serializers.DateTimeField(allow_null=True)
    on_fallback_channel = serializers.BooleanField()
    rendered_content = serializers.CharField(allow_null=True)
    uuid = serializers.CharField()


class VendorSerializer(serializers.Serializer):
    v1 = V1Serializer()


class VendorTextSerializer(serializers.Serializer):
    body = serializers.CharField()


class VendorPayloadSerializer(serializers.Serializer):
    _vnd = VendorSerializer()
    id = serializers.CharField()
    preview_url = serializers.BooleanField()
    recipient_type = serializers.CharField()
    text = VendorTextSerializer()
    timestamp = serializers.IntegerField()
    to = serializers.CharField()
    type = serializers.CharField()

    def get_recipient_id(self):
        recipient_id = self.validated_data["to"]
        return recipient_id

    def get_message_type(self):
        message_type = self.validated_data["type"]
        return message_type

    def get_message_body(self):
        message_body = self.validated_data["text"]["body"]
        return message_body

    def get_author_id(self):
        author_id = self.validated_data["_vnd"]["v1"]["author"]["id"]
        return author_id

    def get_chat_id(self):
        chat_id = self.validated_data["_vnd"]["v1"]["chat"]["contact_uuid"]
        return chat_id

    def get_permalink(self):
        permalink = self.validated_data["_vnd"]["v1"]["chat"]["permalink"]
        return permalink

    def get_state(self):
        state = self.validated_data["_vnd"]["v1"]["chat"]["state"]
        return state

    def get_state_reason(self):
        state_reason = self.validated_data["_vnd"]["v1"]["chat"]["state_reason"]
        return state_reason

    def get_direction(self):
        direction = self.validated_data["_vnd"]["v1"]["direction"]
        return direction

    def get_fallback_channel(self):
        fallback_channel = self.validated_data["_vnd"]["v1"]["on_fallback_channel"]
        return fallback_channel

    def get_labels(self):
        labels = self.validated_data["_vnd"]["v1"]["on_fallback_channel"]
        return labels

    def get_assigned_to(self):
        assigned_to = self.validated_data["_vnd"]["v1"]["chat"]["assigned_to"]["id"]
        return assigned_to


"""
Serializer for contacts payload
"""


class ProfileSerializer(serializers.Serializer):
    name = serializers.CharField()


class ContactSerializer(serializers.Serializer):
    profile = ProfileSerializer()
    wa_id = serializers.CharField()


class AuthorSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()


class AssignedToSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    type = serializers.CharField()


class ChatSerializer(serializers.Serializer):
    assigned_to = AssignedToSerializer()
    contact_uuid = serializers.CharField()
    inserted_at = serializers.DateTimeField()
    owner = serializers.CharField()
    permalink = serializers.URLField()
    state = serializers.CharField()
    state_reason = serializers.CharField()
    unread_count = serializers.IntegerField()
    updated_at = serializers.DateTimeField()
    uuid = serializers.CharField()


class ContactsTextSerializer(serializers.Serializer):
    body = serializers.CharField()


class V1Serializer(serializers.Serializer):
    author = AuthorSerializer()
    card_uuid = serializers.CharField(allow_null=True)
    chat = ChatSerializer()
    direction = serializers.CharField()
    faq_uuid = serializers.CharField(allow_null=True)
    in_reply_to = serializers.CharField(allow_null=True)
    inserted_at = serializers.DateTimeField()
    labels = serializers.ListField(child=serializers.CharField(), required=False)
    last_status = serializers.CharField(allow_null=True)
    last_status_timestamp = serializers.DateTimeField(allow_null=True)
    on_fallback_channel = serializers.BooleanField()
    rendered_content = serializers.CharField(allow_null=True)
    uuid = serializers.CharField()


class VndSerializer(serializers.Serializer):
    v1 = V1Serializer()


class MessageSerializer(serializers.Serializer):
    _vnd = VndSerializer()
    id = serializers.CharField()
    text = ContactsTextSerializer()
    timestamp = serializers.IntegerField()
    type = serializers.CharField()


class ContactsPayloadSerializer(serializers.Serializer):
    contacts = ContactSerializer(many=True)
    messages = MessageSerializer(many=True)

    def get_recipient_id(self):
        recipient_id = self.validated_data["contacts"][0]["wa_id"]
        return recipient_id

    def get_message_type(self):
        message_type = self.validated_data["messages"][0]["type"]
        return message_type

    def get_assigned_to(self):
        assigned_to = self.validated_data["messages"][0]["_vnd"]["v1"]["chat"][
            "assigned_to"
        ]["id"]
        return assigned_to

    def get_direction(self):
        direction = self.validated_data["messages"][0]["_vnd"]["v1"]["direction"]
        return direction

    def get_fallback_channel(self):
        fallback_channel = self.validated_data["messages"][0]["_vnd"]["v1"][
            "on_fallback_channel"
        ]
        return fallback_channel

    def get_labels(self):
        labels = self.validated_data["messages"][0]["_vnd"]["v1"]["labels"]
        return labels

    def get_chat_id(self):
        chat_id = self.validated_data["messages"][0]["_vnd"]["v1"]["chat"][
            "contact_uuid"
        ]
        return chat_id

    def get_permalink(self):
        permalink = self.validated_data["messages"][0]["_vnd"]["v1"]["chat"][
            "contact_uuid"
        ]
        return permalink

    def get_state(self):
        state = self.validated_data["messages"][0]["_vnd"]["v1"]["chat"]["state"]
        return state

    def get_state_reason(self):
        state_reason = self.validated_data["messages"][0]["_vnd"]["v1"]["chat"][
            "state_reason"
        ]
        return state_reason

    def get_message_body(self):
        message_body = self.validated_data["messages"][0]["text"]["body"]
        return message_body
