from django.contrib import admin
from django.urls import include, path

from rest_framework.documentation import include_docs_urls
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser

urlpatterns = [
    path("", include("sidekick.urls"), name="sidekick"),
    path("admin/", admin.site.urls),
    path("redcap/", include("rp_redcap.urls"), name="rp_redcap"),
    path("transferto/", include("rp_transferto.urls"), name="rp_transferto"),
    path(
        "docs/api/",
        include_docs_urls(
            title="REST API Documentation",
            authentication_classes=[SessionAuthentication],
            permission_classes=[IsAdminUser],
        ),
    ),
]
