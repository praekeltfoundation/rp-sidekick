from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rp_interceptors.views import InterceptorViewSet

router = DefaultRouter()
router.register("", InterceptorViewSet, basename="interceptor")

urlpatterns = [path("", include(router.urls))]
