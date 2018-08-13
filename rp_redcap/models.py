from django.db import models


class Survey(models.Model):
    name = models.CharField(max_length=200, unique=True, blank=False)
    rapidpro_flow = models.CharField(max_length=200)
    urn_field = models.CharField(max_length=200)
    check_fields = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Contact(models.Model):
    record_id = models.IntegerField(unique=True)
    urn = models.CharField(max_length=200)

    def __str__(self):
        return "{}: {}".format(self.record_id, self.urn)
