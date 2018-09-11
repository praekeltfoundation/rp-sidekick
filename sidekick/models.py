from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework.authtoken.models import Token

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


@receiver(post_save, sender=User)
def user_token_creation(sender, instance, created, **kwargs):
    if created:
        Token.objects.create(user=instance)


class GoogleCredentials(models.Model):
    """
    Model for saving Google credentials to a persistent database
    https://developers.google.com/api-client-library/python/auth/web-app
    """

    user = models.OneToOneField(
        User,
        primary_key=True,
        limit_choices_to={"is_staff": True},
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    token = models.CharField(max_length=255, null=True)
    refresh_token = models.CharField(max_length=255, null=True)
    token_uri = models.CharField(max_length=255, null=True)
    client_id = models.CharField(max_length=255, null=True)
    client_secret = models.CharField(max_length=255, null=True)
    scopes = models.TextField(
        null=True
    )  # string of list of objects seperated by "|" character

    def to_dict(self):
        """
        Return a dictionary of the fields required to construct
        a google.oauth2.credentials.Credentials object
        """
        return dict(
            token=self.token,
            refresh_token=self.refresh_token,
            token_uri=self.token_uri,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes.split("|"),
        )

    def update_from_credentials(self, credentials):
        self.token = credentials.token
        self.refresh_token = credentials.refresh_token
        self.token_uri = credentials.token_uri
        self.client_id = credentials.client_id
        self.client_secret = credentials.client_secret
        self.scopes = "|".join(credentials.scopes)
        self.save()
