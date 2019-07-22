from django.test import TestCase
from django.urls import reverse_lazy


class ContactImportViewTests(TestCase):

    def test_login_required(self):
        response = self.client.get(reverse_lazy('contact_import'))
        self.assertRedirects(response, '/admin/login/?next=/gpconnect/')
