from django.urls import path

from .views import ContactImportView

urlpatterns = [
    path('', ContactImportView.as_view(), name='contact_import'),
]
