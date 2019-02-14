from django import forms
from django.contrib.postgres.forms import SimpleArrayField

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit

from sidekick.models import Organization


class CheckFlowsForm(forms.Form):
    org = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        to_field_name="name",
        empty_label=None,
    )
    uuids = SimpleArrayField(forms.CharField(required=False))

    def clean(self):
        cleaned_data = super().clean()
        org_name = cleaned_data.get("org")
        uuids = cleaned_data.get("uuids")

        # check that the flows exist
        org = Organization.objects.get(name=org_name)
        client = org.get_rapidpro_client()

        for uuid in uuids:
            if not client.get_flows(uuid=uuid).first():
                self.add_error(
                    "uuids", "{} is not a valid flow UUID".format(uuid)
                )
        return cleaned_data

    helper = FormHelper()
    helper.form_class = "form-horizontal"
    helper.label_class = "col-lg-2"
    helper.field_class = "col-lg-8"
    helper.layout = Layout(
        "org", "uuids", Submit("submit", "Submit", css_class="btn-primary")
    )
