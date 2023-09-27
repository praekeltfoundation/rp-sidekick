from django.contrib import admin

from .models import Consent, GroupMonitor, Organization

admin.site.register(Organization)
admin.site.register(GroupMonitor)
admin.site.register(Consent)
