from django.conf import settings
from django.urls import reverse

import google.oauth2.credentials
import google_auth_oauthlib.flow

from .models import GoogleCredentials


def get_credentials(user):
    """
    Retrieve a user's google.oauth2.credentials.Credentials from the database.
    """
    try:
        _credentials = GoogleCredentials.objects.get(user=user)
    except GoogleCredentials.DoesNotExist:
        return

    return google.oauth2.credentials.Credentials(**_credentials.to_dict())


def save_credentials(user, credentials):
    """
    Store a user's google.oauth2.credentials.Credentials in the database.
    """
    gc, _ = GoogleCredentials.objects.get_or_create(user=user)
    gc.update_from_credentials(credentials)


def get_flow(request, scopes, **kwargs):
    # Use the application credentials (originally from client_secret.json file)
    # to identify the application requesting authorization.
    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=settings.GOOGLE_CLIENT_CONFIG, scopes=scopes, **kwargs
    )

    # Set where API server will redirect the user after the user completes
    # the authorization flow.
    # Make sure this is listed in the Google API console
    flow.redirect_uri = request.build_absolute_uri(
        reverse("sidekick:oauth2callback")
    )
    return flow


def get_authorization_url(request, scopes):
    flow = get_flow(request, scopes=scopes)

    # Generate URL for request to Google's OAuth 2.0 server
    return flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission.
        access_type="offline",
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes="true",
    )
