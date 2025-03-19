import base64
import hmac
from hashlib import sha256

from rest_framework.exceptions import AuthenticationFailed

from .models import TurnSecret


def validate_signature(request, org_id, turn_secret_id):
    try:
        turn_secret = TurnSecret.objects.get(id=turn_secret_id, org_id=org_id)
        secret = turn_secret.secret
    except TurnSecret.DoesNotExist as e:
        raise AuthenticationFailed(
            "TurnSecret for the given organization not found"
        ) from e

    try:
        signature = request.META["HTTP_X_TURN_HOOK_SIGNATURE"]
    except KeyError as e:
        raise AuthenticationFailed("X-Turn-Hook-Signature header required") from e

    raw_data = request.body

    h = hmac.new(secret.encode(), raw_data, sha256)
    generated_signature = base64.b64encode(h.digest()).decode()

    if not hmac.compare_digest(generated_signature, signature):
        raise AuthenticationFailed("Invalid hook signature")
