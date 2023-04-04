from django.db import models

from sidekick.models import Organization


class Interceptor(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    hmac_secret = models.CharField(max_length=255, blank=True)
