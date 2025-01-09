from django.db import models

from sidekick.models import Organization


class TurnAlerts(models.Model):
    org = models.ForeignKey(Organization, default=100, on_delete=models.CASCADE)
    hmac_secret = models.CharField(
        max_length=255, blank=True, help_text="The secret for the Turn Journey"
    )
    journey_id = models.CharField(
        max_length=255,
        null=False,
        default="00000",
        help_text="The id of the Turn journey",
    )
