# from django.conf import settings
# from django.contrib.auth.decorators import login_required
from django.views import View

# from django.views.generic.edit import FormView

# from django.views.generic.base import TemplateView

from django.http import HttpResponse, HttpResponseRedirect

from django.urls import reverse

# from django.shortcuts import redirect
from django.template import loader
from django.contrib.auth.mixins import LoginRequiredMixin

# from googleapiclient.discovery import build

from sidekick.auth_utils import get_credentials

# from sidekick.models import GoogleCredentials
from .forms import GoogleSheetForm

API_SERVICE_NAME = "calendar"
API_VERSION = "v3"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


class SheetView(LoginRequiredMixin, View):
    def get(self, request):
        template = loader.get_template("rp_lookup/index.html")

        has_google_auth = True if get_credentials(request.user) else False
        context = {"has_google_auth": has_google_auth}
        if has_google_auth:
            context.update({"form": GoogleSheetForm()})
        else:
            auth_redirect_url = "{}?next={}&scope={}".format(
                reverse("sidekick:authorize"),
                request.get_full_path(),
                "&scope=".join(SCOPES),
            )
            context.update({"auth_redirect_url": auth_redirect_url})

        return HttpResponse(template.render(context, request))

    def post(self, request):
        credentials = get_credentials(user=request.user)
        if not credentials:
            return HttpResponseRedirect(reverse("lookup"))

        form = self.get_form(request)
        if form.is_valid():
            pass
            # google_sheet_URL = form.cleaned_data["google_sheet_URL"]
            # template = loader.get_template("rp_lookup/index.html")


"""
for getting info from sheet
    def get(self, request):
        credentials = get_credentials(user=request.user)
        if not credentials:

        service = build('sheets', 'v4', credentials=credentials)
        RANGE_NAME="A:B"
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME
        ).execute()

        from pprint import pprint
        pprint(dir(result))

        values = result.get('values', [])
        resp_string = "<h1>THINGS</h1>{}".format(values)
        return HttpResponse(resp_string)
"""
