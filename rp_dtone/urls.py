from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:org_id>/buy/airtime/<int:airtime_value>/<str:msisdn>/",
        views.SendFixedValueAirtimeView.as_view(),
        name="send_fixed_amount_airtime",
    ),
]
