from django.contrib import admin

from .models import Consent, Organization

admin.site.register(Organization)
admin.site.register(Consent)
