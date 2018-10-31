from django.urls import path

from .views import StartProjectCheckView

urlpatterns = [
    path(
        "start-project-check/<int:project_id>/",
        StartProjectCheckView.as_view(),
        name="rp_redcap.start_project_check",
    )
]
