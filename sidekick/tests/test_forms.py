from django.contrib.auth import get_user_model
from django.test import TestCase

from ..forms import OrgForm  # , WhatsAppTemplateForm
from ..models import Organization
from .utils import create_org


class TestOrgFrom(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "username", "testuser@example.com", "password"
        )
        self.org = create_org()

    def test_org_form_without_user(self):
        form = OrgForm()
        self.assertEqual(len(form.fields["org"].queryset), Organization.objects.count())

    def test_org_form_with_user_without_org(self):
        form = OrgForm(user=self.user)
        self.assertTrue(self.org not in form.fields["org"].queryset)

    def test_org_form_with_user(self):
        self.org.users.add(self.user)
        form = OrgForm(user=self.user)
        self.assertTrue(self.org in form.fields["org"].queryset)


# class TestWhatsAppTemplateForm(TestCase):
#     def test_name(self):
#         pass
# form = WhatsAppTemplateForm({"name": "something"})
# self.assertFieldOutput(EmailField, {'a@a.com': 'a@a.com'}, {'aaa': ['Enter a valid email address.']})
