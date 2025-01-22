from django.db import models

from sidekick.models import Organization


class TurnActions(models.Model):
    org = models.ForeignKey(Organization, default=100, on_delete=models.CASCADE)
    journey_id = models.CharField(
        max_length=255,
        null=False,
        default="00000",
        help_text="The id of the Turn journey",
    )
    error_code = models.IntegerField(
        max_length=255,
        null=False,
        default="00000",
        help_text="The error code that starts an event",
    )


class TurnSecret(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    secret = models.CharField(max_length=255)
