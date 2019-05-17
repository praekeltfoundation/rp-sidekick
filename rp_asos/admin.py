from django.contrib import admin

from .models import Hospital, PatientRecord

admin.site.register(Hospital)
admin.site.register(PatientRecord)
