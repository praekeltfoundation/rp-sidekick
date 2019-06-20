from django.contrib import admin

from .models import Recruitment


@admin.register(Recruitment)
class RecruitmentAdmin(admin.ModelAdmin):
    list_display = ("name", "uuid")
    readonly_fields = ("uuid",)
