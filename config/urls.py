from django.contrib import admin
from django.urls import include, path


def trigger_error(request):
    division_by_zero = 1 / 0  # noqa: F841


urlpatterns = [
    path("", include("sidekick.urls"), name="sidekick"),
    path("admin/", admin.site.urls),
    path("transferto/", include("rp_transferto.urls"), name="rp_transferto"),
    path("recruit/", include("rp_recruit.urls"), name="rp_recruit"),
    path("sentry-debug/", trigger_error),
]
