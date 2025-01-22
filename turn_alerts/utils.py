from __future__ import absolute_import, division

import base64
import hmac
from hashlib import sha256

from rest_framework.exceptions import AuthenticationFailed

from .models import Organization, TurnSecret


def validate_signature(request, org_id, turn_secret_id):
    try:
        organization = Organization.objects.get(id=org_id)
        turn_secret = TurnSecret.objects.get(id=turn_secret_id, org=organization)
        secret = turn_secret.secret
    except Organization.DoesNotExist:
        raise AuthenticationFailed("Organization not found")
    except TurnSecret.DoesNotExist:
        raise AuthenticationFailed("TurnSecret for organization not found")

    try:
        signature = request.META["HTTP_X_TURN_HOOK_SIGNATURE"]
    except KeyError:
        raise AuthenticationFailed("X-Turn-Hook-Signature header required")

    raw_data = request.body

    h = hmac.new(secret.encode(), raw_data, sha256)
    generated_signature = base64.b64encode(h.digest()).decode()

    if not hmac.compare_digest(generated_signature, signature):
        raise AuthenticationFailed("Invalid hook signature")
