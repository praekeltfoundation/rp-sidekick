from django.urls import include, path

from . import views

urlpatterns = [
    path("", include("django_prometheus.urls")),
    path("template/view/", views.TemplateView.as_view(), name="view_template"),
    path(
        "template/create/", views.TemplateCreationView.as_view(), name="create_template"
    ),
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
    path(
        "api/consent/<int:pk>",
        views.GetConsentURLView.as_view(),
        name="get-consent-url",
    ),
    path(
        "consent/<str:code>",
        views.ConsentRedirectView.as_view(),
        name="redirect-consent",
    ),
    path(
        "give_consent/<str:code>",
        views.ProvideConsentView.as_view(),
        name="provide-consent",
    ),
]
