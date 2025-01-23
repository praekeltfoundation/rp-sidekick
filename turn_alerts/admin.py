from django.contrib import admin

from .models import TurnActions, TurnSecret

admin.site.register(TurnActions)
admin.site.register(TurnSecret)
