from django.urls import include, path

from . import views

urlpatterns = [
    path("", include("django_prometheus.urls")),
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
    path(
        "api/label_turn_conversation/<int:pk>",
        views.LabelTurnConversationView.as_view(),
        name="label-turn-conversation",
    ),
    path(
        "api/archive_turn_conversation/<int:pk>",
        views.ArchiveTurnConversationView.as_view(),
        name="archive-turn-conversation",
    ),
    path(
        "api/list_contacts/<int:pk>/",
        views.ListContactsView.as_view(),
        name="list_contacts",
    ),
    path(
        "<int:org_id>/api/v2/flows.json",
        views.RapidproFlowsView.as_view(),
        name="rapidpro-flows",
    ),
    path(
        "<int:org_id>/api/v2/contacts.json",
        views.RapidproContactView.as_view(),
        name="rapidpro-contact",
    ),
]
