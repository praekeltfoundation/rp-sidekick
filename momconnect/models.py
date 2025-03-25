from django.db import models


class Clinic(models.Model):
    code = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    uid = models.CharField(max_length=255, primary_key=True)
    name = models.CharField(max_length=255)
    province = models.CharField(max_length=6, blank=True, null=True, default=None)
    location = models.CharField(max_length=255, blank=True, null=True, default=None)
    area_type = models.CharField(max_length=50, blank=True, null=True, default=None)
    unit_type = models.CharField(max_length=50, blank=True, null=True, default=None)
    district = models.CharField(max_length=50, blank=True, null=True, default=None)
    municipality = models.CharField(max_length=50, blank=True, null=True, default=None)

    class Meta:
        indexes = [models.Index(fields=["value"])]
