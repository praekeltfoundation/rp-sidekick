import json

from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.db import models

from sidekick.utils import clean_msisdn


class MsisdnInformation(models.Model):
    """
    Before we can allocate data to a number, we have to first determine
    the mobile network operator that the user has. This stores the
    response that we get from calling the TransferTo endpoint.

    Rather than try to anticipate any future changes in the document, we simply
    store the data in a JSONField.
    """

    # TODO: handle MSISDN vs WhatsApp
    msisdn = models.CharField(max_length=200)
    data = JSONField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "{}\n{}\n{}".format(
            self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            self.msisdn,
            json.dumps(self.data, indent=2),
        )

    def save(self, *args, **kwargs):
        self.msisdn = clean_msisdn(self.msisdn)
        super().save(*args, **kwargs)

    class Meta:
        get_latest_by = "timestamp"
