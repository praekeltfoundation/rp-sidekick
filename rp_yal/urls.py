from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:org_id>/get_ordered_contentset/",
        views.GetOrderedContentSet.as_view(),
        name="get_ordered_contentset",
    ),
    path(
        "<int:org_id>/orderedcontent/<int:contentset_id>/<str:msisdn>",
        views.GetContentSet.as_view(),
        name="get_contentset",
    ),
]
