from django.urls import path

from .views import StartPatientDataCheckView

urlpatterns = [
    path(
        "start-patient-check/<int:project_id>/",
        StartPatientDataCheckView.as_view(),
        name="rp_asos.start_patient_check",
    )
]
