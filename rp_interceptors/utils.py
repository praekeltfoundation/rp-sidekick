import base64
import hmac
from hashlib import sha256


def generate_hmac_signature(body: str, secret: str) -> str:
    if not body or not secret:
        return ""
    h = hmac.new(secret.encode(), body.encode(), sha256)
    return base64.b64encode(h.digest()).decode()
