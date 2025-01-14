from __future__ import absolute_import, division

import base64
import hmac
from hashlib import sha256

from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


def validate_signature(request):
    secret = settings.TURN_HMAC_SECRET
    try:
        signature = request.META["HTTP_X_TURN_HOOK_SIGNATURE"]
    except KeyError:
        raise AuthenticationFailed("X-Turn-Hook-Signature header required")

    raw_data = request.body

    h = hmac.new(secret.encode(), raw_data, sha256)
    generated_signature = base64.b64encode(h.digest()).decode()

    if not hmac.compare_digest(generated_signature, signature):
        raise AuthenticationFailed("Invalid hook signature")
