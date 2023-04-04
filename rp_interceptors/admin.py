from django.contrib import admin
from django.urls import reverse

from rp_interceptors.models import Interceptor


@admin.register(Interceptor)
class InterceptorAdmin(admin.ModelAdmin):
    list_display = ("org", "hmac_secret")

    def view_on_site(self, obj):
        return reverse("interceptor-status", args=[obj.pk])
