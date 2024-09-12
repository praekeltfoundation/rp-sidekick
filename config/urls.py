from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("sidekick.urls"), name="sidekick"),
    path("admin/", admin.site.urls),
    path("transferto/", include("rp_transferto.urls"), name="rp_transferto"),
    path("recruit/", include("rp_recruit.urls"), name="rp_recruit"),
    path("interceptor/", include("rp_interceptors.urls")),
    path("dtone/", include("rp_dtone.urls")),
    path("randomisation/", include("randomisation.urls")),
    path("yal/", include("rp_yal.urls"), name="rp_yal"),
    path("msisdn_utils/", include("msisdn_utils.urls")),
]
