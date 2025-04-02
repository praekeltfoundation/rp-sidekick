import re


def clean_clinic_code(clinic_code):
    # Remove non digit and return only digits from clinic code
    return re.sub("[^0-9]", "", clinic_code)


def validate_clinic_code(clinic_code):
    return clinic_code.isdigit() and len(clinic_code) == 6
