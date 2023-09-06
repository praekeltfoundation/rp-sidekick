from django.db import models

from sidekick.models import Organization


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

    def __str__(self):
        return self.name
