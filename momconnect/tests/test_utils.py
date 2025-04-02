from django.test import TestCase

from momconnect.utils import clean_clinic_code, validate_clinic_code


class TestUtils(TestCase):
    def test_clean_clinic_code(self):
        """
        Test that the clean_clinic_code function removes spaces
        from the input string.
        """
        self.assertEqual(clean_clinic_code("123 456"), "123456")
        self.assertEqual(clean_clinic_code("  789 "), "789")
        self.assertEqual(clean_clinic_code("abc def"), "")
        self.assertEqual(clean_clinic_code(""), "")
        self.assertEqual(clean_clinic_code("123-456"), "123456")
        self.assertEqual(clean_clinic_code('"123456"'), "123456")
        self.assertEqual(clean_clinic_code("123456 clinic"), "123456")

    def test_validate_clinic_code(self):
        """
        Test that the validate_clinic_code function checks if the clinic code
         is valid.
        A valid clinic code must be exactly 6 digits long and contain only
         numbers.
        """
        self.assertTrue(validate_clinic_code("123456"))
        self.assertFalse(validate_clinic_code("12345"))
        self.assertFalse(validate_clinic_code("1234567"))
        self.assertFalse(validate_clinic_code("12345a"))
        self.assertFalse(validate_clinic_code(""))
        self.assertFalse(validate_clinic_code(" "))
