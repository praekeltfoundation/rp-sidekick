from django.urls import path

from . import views

urlpatterns = [
    path("ping/", views.Ping.as_view(), name="ping"),
    path(
        "msisdn_info/<str:msisdn>/",
        views.MsisdnInfo.as_view(),
        name="msisdn_info",
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
        views.GetOperatorProducts.as_view(),
        name="get_operator_products",
    ),
    path(
        "get_products/airtime/<int:operator_id>/",
        views.GetOperatorAirtimeProducts.as_view(),
        name="get_operator_airtime_products",
    ),
    path(
        "get_country_services/<int:country_id>/",
        views.GetCountryServices.as_view(),
        name="get_country_services",
    ),
    path("top_up_data/", views.TopUpData.as_view(), name="top_up_data"),
    path(
        "buy/<int:product_id>/<str:msisdn>/",
        views.BuyProductTakeAction.as_view(),
        name="buy_product_take_action",
    ),
]
