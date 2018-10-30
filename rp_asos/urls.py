from django.conf.urls import url

from .views import StartPatientDataCheckView

urlpatterns = [
    url(
        r"^start-patient-check/(?P<project_id>[^/]+)$",
        StartPatientDataCheckView.as_view(),
        name="rp_asos.start_patient_check",
    )
]
