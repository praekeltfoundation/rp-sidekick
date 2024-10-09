import importlib.metadata
import json

from django.db import models
from django.db.models import JSONField
from django.utils import timezone

from sidekick.models import Organization
from sidekick.utils import clean_msisdn

from .utils import TransferToClient


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


class TransferToAccount(models.Model):
    login = models.CharField(max_length=200, null=False, blank=False)
    token = models.CharField(max_length=200, null=False, blank=False)
    apikey = models.CharField(max_length=200, null=False, blank=False)
    apisecret = models.CharField(max_length=200, null=False, blank=False)
    org = models.ForeignKey(
        Organization,
        related_name="transferto_account",
        null=False,
        on_delete=models.CASCADE,
    )

    def get_transferto_client(self):
        return TransferToClient(self.login, self.token, self.apikey, self.apisecret)

    def __str__(self):
        return self.login


class TopupAttempt(models.Model):
    sidekick_version = models.CharField(max_length=50, null=False, blank=False)
    msisdn = models.CharField(max_length=30, null=False, blank=False)
    from_string = models.CharField(max_length=200, null=False)
    amount = models.IntegerField(null=False, blank=False)
    response = JSONField(null=True)
    rapidpro_user_uuid = models.CharField(max_length=200, null=True)
    CREATED = "C"
    WAITING = "W"
    SUCEEDED = "S"
    FAILED = "F"
    STATUSES = (
        (CREATED, "CREATED"),
        (WAITING, "WAITING"),
        (SUCEEDED, "SUCEEDED"),
        (FAILED, "FAILED"),
    )
    status = models.CharField(max_length=1, choices=STATUSES, default=CREATED)
    org = models.ForeignKey(
        Organization,
        related_name="topup_attempts",
        null=False,
        on_delete=models.CASCADE,
    )
    timestamp = models.DateTimeField(default=timezone.now)

    def make_request(self):
        transferto_client = self.org.transferto_account.first().get_transferto_client()

        self.status = self.WAITING
        topup_result = transferto_client.make_topup(
            self.msisdn, self.amount, self.from_string
        )

        self.response = topup_result
        self.save()

    def save(self, *args, **kwargs):
        # throw an exception if there is no org or transferto account
        self.org.transferto_account.first().get_transferto_client()

        # update status based on response field
        if isinstance(self.response, dict):
            if "error_code" in self.response and self.response["error_code"] in [
                "0",
                0,
            ]:
                self.status = self.SUCEEDED
            else:
                self.status = self.FAILED

        self.sidekick_version = importlib.metadata.version("rp-sidekick")
        self.msisdn = clean_msisdn(self.msisdn)
        super().save(*args, **kwargs)

    def __str__(self):
        return json.dumps(
            {
                "id": self.id,
                "sidekick_version": self.sidekick_version,
                "msisdn": self.msisdn,
                "from_string": self.from_string,
                "amount": self.amount,
                "response": self.response,
                "rapidpro_user_uuid": self.rapidpro_user_uuid,
                "org": self.org.name,
                "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "status": self.status,
            },
            indent=2,
        )

    class Meta:
        get_latest_by = "timestamp"
