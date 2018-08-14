from django.conf.urls import url

from .views import StartSurveyCheckView

urlpatterns = [
    url(
        r"^start-survey-check/(?P<survey_name>[a-z0-9\-_]+)$",
        StartSurveyCheckView.as_view(),
        name="rp_redcap.start_survey_check",
    )
]
