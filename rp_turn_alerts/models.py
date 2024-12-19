from django.db import models

from .validators import za_phone_number


class TurnAlerts(models.Model):
    message_id = models.UUIDField()
    msisdn = models.CharField(max_length=255, validators=[za_phone_number])
    message_status = models.TextField(null=True, blank=True)
    message_direction = models.TextField(null=True, blank=True)
    message_body = models.TextField(null=True, blank=True)
    fallback_channel = models.TextField(null=True, blank=True)
    message_type = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Recipient_ID: {self.message_id} "
            f"MSISDN: {self.msisdn} \n"
            f"Created_at: {self.created_at} \n"
            f"message_status: {self.message_status} \n"
        )
