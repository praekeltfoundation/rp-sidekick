import random
from urllib.parse import urlencode

from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.generic import View
from requests.exceptions import RequestException
from rest_framework import status

from sidekick.utils import get_whatsapp_contact_id

from .forms import SignupForm
from .models import Recruitment

WA_CHECK_FORM_ERROR = (
    "We apologise, something has gone wrong on our side, please try again"
)
RAPIDPRO_CREATE_OR_START_FAILURE = (
    "Apologies, an error has occured, please try again later"
)
MISSING_DATA_ERROR = "Your info appears to be missing"


class SignupView(View):
    def get(self, request, recruitment_uuid, *args, **kwargs):
        get_object_or_404(Recruitment, uuid=recruitment_uuid)
        return render(request, "recruit/signup.html", {"form": SignupForm()})

    def post(self, request, recruitment_uuid, *args, **kwargs):
        recruitment = get_object_or_404(Recruitment, uuid=recruitment_uuid)
        form = SignupForm(request.POST)

        if form.is_valid():
            clean_msisdn = form.cleaned_data["msisdn"].as_e164
            # is this a valid WA number?
            try:
                wa_id = get_whatsapp_contact_id(recruitment.org, clean_msisdn)
            except RequestException:
                form.add_error(None, WA_CHECK_FORM_ERROR)
                return render(
                    request,
                    "recruit/signup.html",
                    {"form": form},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            if wa_id is None:
                form.add_error(
                    "msisdn",
                    f"{form.data['msisdn']} is not a valid WhatsApp contact number",
                )
                return render(
                    request,
                    "recruit/signup.html",
                    {"form": form},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            client = recruitment.org.get_rapidpro_client()
            existing_contact = client.get_contacts(urn=f"whatsapp:{wa_id}").first()

            if existing_contact:
                form.add_error(
                    "msisdn",
                    # we don't want to leak info about who is already on the system
                    # thus we keep this error vague
                    f"{form.data['msisdn']} is not a valid contact number",
                )
                return render(
                    request,
                    "recruit/signup.html",
                    {"form": form},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                pin = random.randint(1000, 10000)  # random 4 digit number
                client.create_contact(
                    name=form.cleaned_data["name"],
                    urns=[f"whatsapp:{wa_id}"],
                    groups=[recruitment.rapidpro_group_name],
                    fields={recruitment.rapidpro_pin_key_name: pin},
                )
                client.create_flow_start(
                    flow=str(recruitment.rapidpro_flow_uuid),
                    urns=[f"whatsapp:{wa_id}"],
                    restart_participants=False,
                )
                query_params = {"name": form.cleaned_data["name"], "pin": pin}
                return redirect(
                    f"{reverse('recruit_success')}?{urlencode(query_params)}"
                )
            except Exception:
                pass

                form.add_error(None, RAPIDPRO_CREATE_OR_START_FAILURE)
                return render(
                    request,
                    "recruit/signup.html",
                    {"form": form},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return render(request, "recruit/signup.html", {"form": form})


class SignupSuccessView(View):
    def get(self, request, *args, **kwargs):
        name = request.GET.get("name", False)
        pin = request.GET.get("pin", False)
        if (not name) or (not pin):
            return render(
                request,
                "recruit/signup_success.html",
                {"missing_info": True, "error_message": MISSING_DATA_ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return render(
            request, "recruit/signup_success.html", {"pin": pin, "name": name}
        )
