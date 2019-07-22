from django import forms
from .models import ContactImport


class ContactImportForm(forms.ModelForm):
    class Meta:
        model = ContactImport
        fields = ["file", "org"]
