from django import forms

from rp_gpconnect.models import ContactImport


class ContactImportForm(forms.ModelForm):
    class Meta:
        model = ContactImport
        fields = ["file", "org"]
