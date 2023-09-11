import json
import uuid

from django.db import models
from django.utils import timezone

from sidekick.models import Organization

from .dtone_client import DtoneClient


class DtoneAccount(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False)
    apikey = models.CharField(max_length=200, null=False, blank=False)
    apisecret = models.CharField(max_length=200, null=False, blank=False)
    production = models.BooleanField(default=False)
    org = models.ForeignKey(
        Organization,
        related_name="dtone_account",
        null=False,
        on_delete=models.CASCADE,
    )

    def get_dtone_client(self):
        return DtoneClient(self.apikey, self.apisecret, self.production)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        OPERATOR_NOT_FOUND = "operator_not_found", "Operator not found"
        PRODUCT_NOT_FOUND = "product_not_found", "Product not found"
        ERROR = "error", "Error"
        SUCCESS = "success", "Success"

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    msisdn = models.CharField(max_length=30, null=False, blank=False)
    value = models.IntegerField(null=False, blank=False)
    operator_id = models.IntegerField(null=True)
    product_id = models.IntegerField(null=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED
    )
    response = models.JSONField(null=True)
    org = models.ForeignKey(
        Organization,
        related_name="transaction_attempts",
        null=False,
        on_delete=models.CASCADE,
    )
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return json.dumps(
            {
                "id": self.id,
                "uuid": self.uuid,
                "msisdn": self.msisdn,
                "value": self.value,
                "operator_id": self.operator_id,
                "product_id": self.product_id,
                "status": self.status,
                "response": self.response,
                "org": self.org.name,
                "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            },
            indent=2,
        )
