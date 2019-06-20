from django.urls import path

from . import views

urlpatterns = [
    path("<uuid:recruitment_uuid>/", views.SignupView.as_view(), name="recruit"),
    path("success/", views.SignupSuccessView.as_view(), name="recruit_success"),
]
