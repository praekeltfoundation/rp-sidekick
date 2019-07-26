from django.urls import path

from rp_gpconnect.views import ContactImportView

urlpatterns = [path("", ContactImportView.as_view(), name="contact_import")]
