from django.contrib import admin

from .models import Contact, Project, Survey

admin.site.register(Project)
admin.site.register(Survey)
admin.site.register(Contact)
