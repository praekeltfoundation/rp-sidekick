from django.urls import path

from . import views

urlpatterns = [
    path(
        "turn-messages/<int:org_id>/<int:turn_secret_id>/",
        views.TurnAlertsLayerView.as_view(),
        name="turn-messages",
    ),
]
