from django import forms

from rp_gpconnect.models import ContactImport
from rp_gpconnect.tasks import process_contact_import


class ContactImportForm(forms.ModelForm):
    class Meta:
        model = ContactImport
        fields = ["file", "org"]

    def save(self, commit=True):
        instance = super(ContactImportForm, self).save(commit=commit)
        process_contact_import.delay(instance.pk)
        return instance
