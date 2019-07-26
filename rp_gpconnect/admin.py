from django.contrib import admin

from rp_gpconnect.models import ContactImport, Flow


@admin.register(ContactImport)
class ContactImportAdmin(admin.ModelAdmin):
    list_display = ("created_at", "file", "org", "created_by")
    readonly_fields = ("created_at", "file", "org", "created_by")


@admin.register(Flow)
class FlowAdmin(admin.ModelAdmin):
    list_display = ("type", "org", "rapidpro_flow")
