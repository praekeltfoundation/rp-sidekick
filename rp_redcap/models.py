import redcap

from django.db import models
from sidekick.models import Organization


class Project(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False)
    url = models.CharField(max_length=200, null=False, blank=False)
    token = models.CharField(max_length=200, null=False, blank=False)
    org = models.ForeignKey(
        Organization,
        related_name="projects",
        null=False,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name

    def get_redcap_client(self):
        return redcap.Project(self.url, self.token)  # pragma: no cover


class Survey(models.Model):
    sequence = models.IntegerField(default=1, null=False)
    name = models.CharField(max_length=200, blank=False)
    project = models.ForeignKey(
        Project, related_name="surveys", null=False, on_delete=models.CASCADE
    )
    rapidpro_flow = models.CharField(max_length=200)
    urn_field = models.CharField(max_length=200)
    check_fields = models.BooleanField(default=False)

    unique_together = (("name", "project_id"),)

    def __str__(self):
        return self.name


class Contact(models.Model):
    project = models.ForeignKey(
        Project, related_name="contacts", null=False, on_delete=models.CASCADE
    )
    record_id = models.IntegerField()
    urn = models.CharField(max_length=200)
    role = models.CharField(max_length=200, null=True)
    name = models.CharField(max_length=200, null=True)
    title = models.CharField(max_length=200, null=True)

    unique_together = (("record_id", "project_id"),)

    def __str__(self):
        return "{}: {}".format(self.record_id, self.urn)
