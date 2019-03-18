from django.urls import path

from . import views

urlpatterns = [
    path("health", views.health, name="health"),
    path("health_details", views.detailed_health, name="detailed-health"),
    path(
        "send_template",
        views.SendWhatsAppTemplateMessageView.as_view(),
        name="send_template",
    ),
    path(
        "check_contact/<int:org_id>/<str:msisdn>/",
        views.CheckContactView.as_view(),
        name="check_contact",
    ),
]
