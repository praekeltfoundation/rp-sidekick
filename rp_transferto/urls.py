from django.urls import path

from . import views

urlpatterns = [
    path("ping/", views.Ping.as_view(), name="ping"),
    path(
        "msisdn_info/<str:msisdn>/",
        views.MsisdnInfo.as_view(),
        name="misisdn_info",
    ),
    path("reserve_id/", views.ReserveId.as_view(), name="reserve_id"),
    path("get_countries/", views.GetCountries.as_view(), name="get_countries"),
    path(
        "get_operators/<int:country_id>/",
        views.GetOperators.as_view(),
        name="get_operators",
    ),
    path(
        "get_products/<int:operator_id>/",
        views.GetProducts.as_view(),
        name="get_products",
    ),
]
