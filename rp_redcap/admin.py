from django.contrib import admin
from .models import Survey, Project, Contact, Hospital, PatientRecord

admin.site.register(Project)
admin.site.register(Survey)
admin.site.register(Contact)
admin.site.register(Hospital)
admin.site.register(PatientRecord)
