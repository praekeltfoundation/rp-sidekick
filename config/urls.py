from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("sidekick.urls"), name="sidekick"),
    path("admin/", admin.site.urls),
    path("redcap/", include("rp_redcap.urls"), name="rp_redcap"),
    path("transferto/", include("rp_transferto.urls"), name="rp_transferto"),
]
