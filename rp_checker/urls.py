from django.urls import path

from . import views

urlpatterns = [
    path("variables/", views.CheckVariables.as_view(), name="variables"),
    path("webhooks/", views.CheckWebhooks.as_view(), name="webhooks"),
    path("flowlinks/", views.CheckFlowLinks.as_view(), name="flowlinks"),
]
