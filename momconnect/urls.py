from django.urls import path

from .views import ClinicDetailsView

urlpatterns = [
    path("clinic-check", ClinicDetailsView.as_view(), name="clinic-check"),
]
