from django.contrib import admin
from django.urls import include, path

from rest_framework.documentation import include_docs_urls
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAdminUser

urlpatterns = [
    path("", include("sidekick.urls", namespace="sidekick"), name="sidekick"),
    path("admin/", admin.site.urls),
    path("redcap/", include("rp_redcap.urls"), name="rp_redcap"),
    path("asos/", include("rp_asos.urls"), name="rp_asos"),
    path("transferto/", include("rp_transferto.urls"), name="rp_transferto"),
    path(
        "lookup/",
        include("rp_lookup.urls", namespace="rp_lookup"),
        name="rp_lookup",
    ),
    path(
        "docs/api/",
        include_docs_urls(
            title="REST API Documentation",
            authentication_classes=[SessionAuthentication],
            permission_classes=[IsAdminUser],
        ),
    ),
]
