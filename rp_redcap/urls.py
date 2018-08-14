from django.conf.urls import url

from .views import StartProjectCheckView

urlpatterns = [
    url(
        r"^start-project-check/(?P<project_id>[^/]+)$",
        StartProjectCheckView.as_view(),
        name="rp_redcap.start_project_check",
    )
]
