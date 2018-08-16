from django.urls import path

from . import views

urlpatterns = [
    path("get_products", views.GetProducts.as_view(), name="get_products")
]
