from django.urls import path

from . import views

urlpatterns = [
    path("<int:org_id>/ping/", views.Ping.as_view(), name="ping"),
    path(
        "<int:org_id>/msisdn_info/<str:msisdn>/",
        views.MsisdnInfo.as_view(),
        name="msisdn_info",
    ),
    path(
        "<int:org_id>/reserve_id/", views.ReserveId.as_view(), name="reserve_id"
    ),
    path(
        "<int:org_id>/get_countries/",
        views.GetCountries.as_view(),
        name="get_countries",
    ),
    path(
        "<int:org_id>/get_operators/<int:country_id>/",
        views.GetOperators.as_view(),
        name="get_operators",
    ),
    path(
        # failing
        "<int:org_id>/get_products/<int:operator_id>/",
        views.GetOperatorProducts.as_view(),
        name="get_operator_products",
    ),
    path(
        "<int:org_id>/get_products/airtime/<int:operator_id>/",
        views.GetOperatorAirtimeProducts.as_view(),
        name="get_operator_airtime_products",
    ),
    path(
        # failing
        "<int:org_id>/get_country_services/<int:country_id>/",
        views.GetCountryServices.as_view(),
        name="get_country_services",
    ),
    path("top_up_data/", views.TopUpData.as_view(), name="top_up_data"),
    path(
        "buy/<int:product_id>/<str:msisdn>/",
        views.BuyProductTakeAction.as_view(),
        name="buy_product_take_action",
    ),
    path(
        "buy/airtime/<int:airtime_amount>/<str:msisdn>/from/<str:from_string>/",
        views.BuyAirtimeTakeAction.as_view(),
        name="buy_airtime_take_action",
    ),
]
