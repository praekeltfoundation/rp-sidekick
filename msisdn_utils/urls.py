from django.urls import path

from . import views

urlpatterns = [
    path(
        "timezones/",
        views.GetMsisdnTimezones.as_view(),
        name="get-timezones",
    ),
]
