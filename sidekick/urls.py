from django.urls import path

from . import views

urlpatterns = [
    path("health", views.health, name="health"),
    path("send_template", views.send_wa_template_message, name="send_template"),
    path(
        "check_contact/<int:org_id>/<str:msisdn>/",
        views.CheckContactView.as_view(),
        name="check_contact",
    ),
]
