from django.db import models
from django.contrib.auth.models import User

from temba_client.v2 import TembaClient


class Organization(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False)
    url = models.CharField(max_length=200, null=False, blank=False)
    token = models.CharField(max_length=200, null=False, blank=False)
    users = models.ManyToManyField(User, related_name="org_users")
    engage_url = models.URLField(max_length=200, null=True)
    engage_token = models.CharField(max_length=1000, null=True)
    point_of_contact = models.EmailField(null=True)

    def __str__(self):
        return self.name

    def get_rapidpro_client(self):
        return TembaClient(self.url, self.token)
