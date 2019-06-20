from django import forms
from django.forms import widgets
from phonenumber_field.formfields import PhoneNumberField


class SignupForm(forms.Form):
    name = forms.CharField(required=True)
    msisdn = PhoneNumberField(
        required=True, widget=widgets.TextInput(attrs={"class": "form-control"})
    )
