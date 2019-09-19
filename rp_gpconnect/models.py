from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models

from sidekick.models import Organization


class ContactImport(models.Model):
    file = models.FileField(
        upload_to="uploads/gpconnect/",
        validators=[FileExtensionValidator(allowed_extensions=["csv"])],
    )
    org = models.ForeignKey(
        Organization, on_delete=models.CASCADE, null=True, blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)


class Flow(models.Model):
    TYPE_CHOICES = (
        ("new_contact", "New Contacts"),
        ("contact_update", "Updating Contacts"),
    )
    type = models.CharField(
        max_length=200, null=False, blank=False, choices=TYPE_CHOICES
    )
    rapidpro_flow = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        help_text="RapidPro ID of the flow to trigger",
    )
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        null=True,
        blank=False,
        related_name="flows",
    )
