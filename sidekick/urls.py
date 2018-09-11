from django.urls import path

from . import views


app_name = "sidekick"

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
    path("authorize/", views.GoogleAuthorizeView.as_view(), name="authorize"),
    path(
        "oauth2callback/", views.OAuth2Callback.as_view(), name="oauth2callback"
    ),
]
