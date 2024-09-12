import logging
from datetime import datetime
from math import floor

import phonenumbers
import pytz
from phonenumbers import timezone as ph_timezone
from rest_framework import authentication, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

LOGGER = logging.getLogger(__name__)


def get_middle_tz(zones):
    timezones = []
    for zone in zones:
        offset = pytz.timezone(zone).utcoffset(datetime.utcnow())
        offset_seconds = (offset.days * 86400) + offset.seconds
        timezones.append({"name": zone, "offset": offset_seconds / 3600})
    ordered_tzs = sorted(timezones, key=lambda k: k["offset"])

    approx_tz = ordered_tzs[floor(len(ordered_tzs) / 2)]["name"]

    LOGGER.info(
        "Available timezones: {}. Returned timezone: {}".format(ordered_tzs, approx_tz)
    )
    return approx_tz


class GetMsisdnTimezones(APIView):
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, *args, **kwargs):
        try:
            msisdn = request.data["whatsapp_id"]
        except KeyError:
            raise ValidationError({"whatsapp_id": ["This field is required."]})

        msisdn = msisdn if msisdn.startswith("+") else "+" + msisdn

        try:
            msisdn = phonenumbers.parse(msisdn)
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError(
                {
                    "whatsapp_id": [
                        "This value must be a phone number with a region prefix."
                    ]
                }
            )

        if not (
            phonenumbers.is_possible_number(msisdn)
            and phonenumbers.is_valid_number(msisdn)
        ):
            raise ValidationError(
                {
                    "whatsapp_id": [
                        "This value must be a phone number with a region prefix."
                    ]
                }
            )

        zones = list(ph_timezone.time_zones_for_number(msisdn))
        if (
            len(zones) > 1
            and request.query_params.get("return_one", "false").lower() == "true"
        ):
            zones = [get_middle_tz(zones)]

        return Response({"success": True, "timezones": zones}, status=200)
