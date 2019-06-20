import uuid

from django.db import models

# Create your models here.
from sidekick.models import Organization


class Recruitment(models.Model):
    name = models.CharField(max_length=200, blank=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    term_and_conditions = models.TextField()
    org = models.ForeignKey(
        Organization, related_name="campaigns", null=False, on_delete=models.CASCADE
    )
    rapidpro_flow_uuid = models.UUIDField()
    rapidpro_pin_key_name = models.CharField(max_length=30)
    rapidpro_group_name = models.CharField(max_length=30)

    def __str__(self):
        return self.name
