from django.db import models

from sidekick.models import Organization


class Interceptor(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    channel_uuid = models.CharField(
        max_length=255,
        null=False,
        help_text="The uuid of the WhatsApp channel in RapidPro that should receive messages",
    )
    hmac_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="The secret for the webhook in Turn that calls this",
    )
