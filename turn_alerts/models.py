from django.db import models


class TurnAlerts(models.Model):
    whatsappid = models.CharField(max_length=25, default="00000")
    assigned_to = models.UUIDField(null=True, blank=True)
    author_id = models.UUIDField(null=True, blank=True)
    chat_id = models.UUIDField(null=True, blank=True)
    conversation_id = models.TextField(null=True, blank=True)
    message_status = models.TextField(null=True, blank=True)
    message_direction = models.TextField(null=True, blank=True)
    message_body = models.TextField(null=True, blank=True)
    error_code = models.CharField(max_length=15, null=True, blank=True)
    error_data = models.TextField(null=True, blank=True)
    fallback_channel = models.TextField(null=True, blank=True)
    message_type = models.TextField(null=True, blank=True)
    labels = models.CharField(max_length=25, null=True, blank=True)
    state = models.CharField(max_length=25, null=True, blank=True)
    state_reason = models.CharField(max_length=255, null=True, blank=True)
    permalink = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"WhatsApp ID: {self.whatsappid} - "
            f"Message Type: {self.message_type} - "
            f"Status: {self.message_status} - "
            f"Created at: {self.created_at}"
        )
