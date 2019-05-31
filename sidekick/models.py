from uuid import UUID

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from hashids import Hashids
from rest_framework.authtoken.models import Token
from temba_client.v2 import TembaClient

hashids = Hashids(salt=settings.SECRET_KEY)


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

    class Meta:
        permissions = [
            ("label_turn_conversation", "Can label a Turn Conversation"),
            ("archive_turn_conversation", "Can archive a Turn Conversation"),
        ]


@receiver(post_save, sender=User)
def user_token_creation(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Consent(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    label = models.CharField(
        max_length=200,
        blank=True,
        help_text="Human readable label describing this consent",
    )
    flow_id = models.UUIDField(
        blank=True,
        null=True,
        help_text="The flow to trigger when the user visits the URL",
    )
    redirect_url = models.URLField(
        blank=True, help_text="The URL to redirect to when the user visits the URL"
    )
    preview_title = models.CharField(
        max_length=35,
        blank=True,
        help_text="The title displayed on the WhatsApp preview and page",
    )
    preview_url = models.URLField(
        blank=True, help_text="The URL to display on the WhatsApp preview"
    )
    preview_description = models.CharField(
        max_length=65,
        blank=True,
        help_text="The description to display in the WhatsApp preview",
    )
    preview_image_url = models.URLField(
        blank=True, help_text="The URL of the imgae to display on the WhatsApp preview"
    )
    body_text = models.CharField(
        max_length=200,
        blank=True,
        help_text="The text to display to the user while they're redirecting",
    )

    def generate_code(self, contact_uuid):
        return hashids.encode(self.id, contact_uuid.int)

    def generate_url(self, request, contact_uuid):
        """
        Returns the full URL for the user to consent
        """
        code = self.generate_code(contact_uuid)
        path = reverse("redirect-consent", args=[code])
        return request.build_absolute_uri(path)

    @classmethod
    def from_code(cls, code):
        """
        Returns (consent, contact_uuid) for the given code, where consent is a Consent
        model instance, and contact_uuid is the UUID of the RapidPro contact.
        """
        id, contact_uuid = hashids.decode(code)
        consent = Consent.objects.get(id=id)
        contact_uuid = UUID(int=contact_uuid)
        return consent, contact_uuid

    def __str__(self):
        return self.label
