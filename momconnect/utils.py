def clean_clinic_code(clinic_code):
    return str(clinic_code).replace(" ", "")


def validate_clinic_code(clinic_code):
    clinic_code = clean_clinic_code(clinic_code)
    return clinic_code.isdigit() and len(clinic_code) == 6
