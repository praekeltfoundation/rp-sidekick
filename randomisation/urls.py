from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:strategy_id>/get_random_arm/",
        views.GetRandomArmView.as_view(),
        name="get_random_arm",
    ),
]
