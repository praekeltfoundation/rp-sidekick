from django import forms


class GoogleSheetForm(forms.Form):
    google_sheet_URL = forms.URLField(
        help_text="Enter the URL of the Google Sheet you wish to access"
    )

    def clean_renewal_date(self):
        data = self.cleaned_data["google_sheet_URL"]
        print("DATA")
        print(data)
        return data
