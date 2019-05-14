from django.urls import path

from .views import StartPatientDataCheckView, StartScreeningRecordCheckView

urlpatterns = [
    path(
        "start-patient-check/<int:project_id>/<slug:tz_code>",
        StartPatientDataCheckView.as_view(),
        name="rp_asos.start_patient_check",
    ),
    path(
        "start-screening-record-check/<int:org_id>",
        StartScreeningRecordCheckView.as_view(),
        name="rp_asos.start_screening_record_check",
    ),
]
