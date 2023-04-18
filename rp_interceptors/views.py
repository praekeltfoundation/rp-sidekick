import hmac
import json
from urllib.parse import urljoin

from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import GenericViewSet

from rp_interceptors.models import Interceptor
from rp_interceptors.tasks import http_request
from rp_interceptors.utils import generate_hmac_signature


def validate_hmac_signature(secret, signature, body):
    if not secret:
        return
    if not hmac.compare_digest(
        generate_hmac_signature(body.decode(), secret), signature or ""
    ):
        raise AuthenticationFailed("Invalid HMAC signature")


class InterceptorUser(AnonymousUser):
    def __init__(self, interceptor):
        self.interceptor = interceptor

    @property
    def is_authenticated(self):
        return True


class HmacAuthentication(BaseAuthentication):
    def authenticate(self, request):
        try:
            interceptor_pk = request.parser_context["kwargs"]["pk"]
            interceptor = Interceptor.objects.get(pk=interceptor_pk)
        except KeyError:
            raise AuthenticationFailed("No Interceptor found")
        except Interceptor.DoesNotExist:
            raise AuthenticationFailed("No Interceptor found")

        signature = request.META.get("HTTP_X_TURN_HOOK_SIGNATURE")
        if not signature:
            raise AuthenticationFailed("HTTP_X_TURN_HOOK_SIGNATURE missing")

        validate_hmac_signature(
            interceptor.hmac_secret,
            signature,
            request.body,
        )

        request.interceptor = interceptor
        return (InterceptorUser(interceptor), None)


class InterceptorViewSet(GenericViewSet):
    queryset = Interceptor.objects.all()
    serializer_class = Serializer
    authentication_classes = [HmacAuthentication]

    @action(detail=True, methods=["POST"])
    def status(self, request, pk=None):
        interceptor = self.get_object()

        if "statuses" in request.data:
            statuses = []
            for status in request.data.get("statuses", []):
                if "recipient_id" not in status and "message" in status:
                    status["recipient_id"] = status["message"].get("recipient_id", "")

                if status != {}:
                    statuses.append(status)

            request.data["statuses"] = statuses

        if request.data.get("statuses") == [] and request.data.get("messages") == []:
            return Response()

        body = json.dumps(request.data, separators=(",", ":"))
        path = f"/c/wa/{interceptor.channel_uuid}/receive"
        http_request.delay(
            method="POST",
            url=urljoin(interceptor.org.url, path),
            headers={
                "X-Turn-Hook-Signature": generate_hmac_signature(
                    body, interceptor.hmac_secret
                ),
                "Content-Type": "application/json",
            },
            body=body,
        )
        return Response()
