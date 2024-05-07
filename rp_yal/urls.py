from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:org_id>/get_ordered_contentset/",
        views.GetOrderedContentSet.as_view(),
        name="get_ordered_contentset",
    ),
]
