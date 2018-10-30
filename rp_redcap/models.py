import redcap

from django.db import models
from sidekick.models import Organization


class Project(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False)
    url = models.CharField(max_length=200, null=False, blank=False)
    token = models.CharField(max_length=200, null=False, blank=False)
    crf_token = models.CharField(max_length=200, null=True)
    org = models.ForeignKey(
        Organization,
        related_name="projects",
        null=False,
        on_delete=models.CASCADE,
    )
    pre_operation_fields = models.TextField(null=True)
    post_operation_fields = models.TextField(null=True)

    def __str__(self):
        return self.name

    def get_redcap_client(self):
        return redcap.Project(self.url, self.token)  # pragma: no cover

    def get_redcap_crf_client(self):
        return redcap.Project(self.url, self.crf_token)  # pragma: no cover


class Survey(models.Model):
    sequence = models.IntegerField(default=1, null=False)
    name = models.CharField(max_length=200, blank=False)
    description = models.CharField(max_length=200, blank=False)
    project = models.ForeignKey(
        Project, related_name="surveys", null=False, on_delete=models.CASCADE
    )
    rapidpro_flow = models.CharField(max_length=200)
    urn_field = models.CharField(max_length=200)
    ignore_fields = models.TextField(null=True, blank=True)

    unique_together = (("name", "project_id"),)

    def __str__(self):
        return "{} - {}".format(self.project.name, self.description)

    def get_ignore_fields(self):
        if self.ignore_fields:
            return [x.strip() for x in self.ignore_fields.split(",")]
        return []


class Contact(models.Model):
    project = models.ForeignKey(
        Project, related_name="contacts", null=False, on_delete=models.CASCADE
    )
    record_id = models.IntegerField()
    urn = models.CharField(max_length=200)
    role = models.CharField(max_length=200, null=True)
    name = models.CharField(max_length=200, null=True)
    surname = models.CharField(max_length=200, null=True)
    title = models.CharField(max_length=200, null=True)

    unique_together = (("record_id", "project_id"),)

    def __str__(self):
        return "{}: {}".format(self.record_id, self.urn)


class SurveyAnswer(models.Model):
    survey = models.ForeignKey(
        Survey, related_name="answers", null=False, on_delete=models.CASCADE
    )
    contact = models.ForeignKey(
        Contact, related_name="answers", null=False, on_delete=models.CASCADE
    )
    name = models.CharField(max_length=200, blank=False)
    value = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    unique_together = (("survey", "contact", "name"),)
