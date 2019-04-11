from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth.models import User

from .constants import category_codes, language_codes
from .models import Organization


class OrgForm(forms.Form):
    """
    This form can serve as a parent class for any form that needs to use Orgs
    Additionally, it sets up a Crispy Form layout as a default, which can be
    overridden if necessary
    """

    org = forms.ModelChoiceField(
        queryset=Organization.objects.all(), empty_label="-------"
    )

    def __init__(self, *args, **kwargs):
        # restrict form to only show user the Orgs they belong to
        user = kwargs.pop("user", None)
        super(OrgForm, self).__init__(*args, **kwargs)
        if user and isinstance(user, User):
            self.fields["org"].queryset = user.org_users.all()

        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal"
        self.helper.label_class = "col-lg-2"
        self.helper.field_class = "col-lg-8"
        self.helper.add_input(Submit("submit", "Submit", css_class="btn-primary"))


class WhatsAppTemplateForm(OrgForm):
    name = forms.RegexField(
        regex=r"([a-z0-9_]+)", max_length=512, min_length=1, strip=True
    )
    language = forms.TypedChoiceField(
        # this puts English at the top of the list
        choices=[("en", language_codes["en"])]
        + [(key, value) for key, value in language_codes.items() if key != "en"]
    )
    category = forms.TypedChoiceField(
        choices=[(value, value) for value in category_codes]
    )
    content = forms.CharField(widget=forms.Textarea, max_length=1024)

    # def clean_content(self):
    #     pass
