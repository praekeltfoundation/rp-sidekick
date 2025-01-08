from django.urls import path

from . import views

urlpatterns = [
    path(
        "api/v2/messages",
        views.TurnAlertsLayerView.as_view(),
        name="turn-messages",
    ),
]
