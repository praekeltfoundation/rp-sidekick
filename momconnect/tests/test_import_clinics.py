from django.core.management import CommandError, call_command
from django.test import TestCase

from momconnect.models import Clinic


class ImportClinicsCommandTest(TestCase):
    def get_file_path(self, name):
        return f"./momconnect/tests/clinic-data/{name}.csv"

    def test_import_clinics_success(self):
        call_command("import_clinics", self.get_file_path("import_valid"))

        self.assertEqual(Clinic.objects.count(), 2)
        clinic1 = Clinic.objects.get(uid="123")
        self.assertEqual(clinic1.name, "Clinic One")
        self.assertEqual(clinic1.province, "GP")
        self.assertEqual(clinic1.value, "123456")
        self.assertEqual(clinic1.code, "123456")
        self.assertEqual(clinic1.location, "Location One")
        self.assertEqual(clinic1.area_type, "Urban")
        self.assertEqual(clinic1.unit_type, "Type A")
        self.assertEqual(clinic1.district, "District A")
        self.assertEqual(clinic1.municipality, "Municipality A")

        clinic2 = Clinic.objects.get(uid="456")
        self.assertEqual(clinic2.name, "Clinic Two")
        self.assertEqual(clinic2.province, "WC")
        self.assertEqual(clinic2.value, "123457")
        self.assertEqual(clinic2.code, "123457")
        self.assertEqual(clinic2.location, "Location Two")
        self.assertEqual(clinic2.area_type, "Rural")
        self.assertEqual(clinic2.unit_type, "Type B")
        self.assertEqual(clinic2.district, "District B")
        self.assertEqual(clinic2.municipality, "Municipality B")

    def test_import_clinics_update_existing(self):
        Clinic.objects.create(
            uid="123", value="123456", code="123456", name="Old Clinic"
        )
        call_command("import_clinics", self.get_file_path("import_valid"))

        clinic = Clinic.objects.get(uid="123")
        self.assertEqual(clinic.name, "Clinic One")
        self.assertEqual(clinic.province, "GP")
        self.assertEqual(clinic.value, "123456")
        self.assertEqual(clinic.code, "123456")
        self.assertEqual(clinic.location, "Location One")
        self.assertEqual(clinic.area_type, "Urban")
        self.assertEqual(clinic.unit_type, "Type A")
        self.assertEqual(clinic.district, "District A")
        self.assertEqual(clinic.municipality, "Municipality A")
        self.assertEqual(Clinic.objects.count(), 2)

    def test_import_clinics_missing_column(self):
        with self.assertRaises(CommandError) as context:
            call_command("import_clinics", self.get_file_path("import_invalid"))
        self.assertIn("Missing required column", str(context.exception))

    def test_import_clinics_file_not_found(self):
        with self.assertRaises(CommandError) as context:
            call_command("import_clinics", "nonexistent.csv")
        self.assertIn("does not exist", str(context.exception))
