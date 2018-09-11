from django.urls import path

from . import views

app_name = "rp_lookup"

urlpatterns = [path("", views.SheetView.as_view(), name="sheet")]
