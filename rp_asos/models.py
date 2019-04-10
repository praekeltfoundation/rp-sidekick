from django.db import models

from rp_redcap.models import Project


class Hospital(models.Model):
    name = models.CharField(max_length=200, blank=False)
    data_access_group = models.CharField(max_length=200, blank=False)
    project = models.ForeignKey(
        Project, related_name="hospitals", null=False, on_delete=models.CASCADE
    )
    rapidpro_flow = models.CharField(max_length=200)
    hospital_lead_name = models.CharField(max_length=200)
    hospital_lead_urn = models.CharField(max_length=200)
    nomination_name = models.CharField(max_length=200, null=True, blank=True)
    nomination_urn = models.CharField(max_length=200, null=True, blank=True)
    whatsapp_group_id = models.CharField(max_length=200, null=True, blank=True)

    unique_together = (("name", "project_id"),)

    def __str__(self):
        return "{} - {}".format(self.project.name, self.name)


class PatientRecord(models.Model):

    INCOMPLETE_STATUS = "0"
    UNVERIFIED_STATUS = "1"
    COMPLETE_STATUS = "2"

    STATUS_CHOICES = (
        (INCOMPLETE_STATUS, "Incomplete"),
        (UNVERIFIED_STATUS, "Unverified"),
        (COMPLETE_STATUS, "Complete"),
    )
    project = models.ForeignKey(
        Project, related_name="patients", null=False, on_delete=models.CASCADE
    )
    record_id = models.CharField(max_length=30, null=False, blank=False)
    date = models.DateField()
    pre_operation_status = models.CharField(
        max_length=1,
        null=False,
        blank=False,
        choices=STATUS_CHOICES,
        default=INCOMPLETE_STATUS,
    )
    post_operation_status = models.CharField(
        max_length=1,
        null=False,
        blank=False,
        choices=STATUS_CHOICES,
        default=INCOMPLETE_STATUS,
    )

    unique_together = (("project", "record_id"),)


class PatientValue(models.Model):
    patient = models.ForeignKey(
        PatientRecord,
        related_name="values",
        null=False,
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=200, blank=False)
    value = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    unique_together = (("patient", "name"),)
