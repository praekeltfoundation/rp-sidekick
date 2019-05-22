from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework.authtoken.models import Token

from sidekick.models import Consent, Organization, hashids


class TestUserTokenSignal(TestCase):
    def test_user_token_creation(self):
        user = User.objects.create_user("username", "testuser@example.com", "password")
        self.assertTrue(Token.objects.get(user=user))

    def test_user_token_deletion(self):
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Token.objects.count(), 0)

        user = User.objects.create_user("username", "testuser@example.com", "password")

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Token.objects.count(), 1)

        user.delete()

        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Token.objects.count(), 0)

    def test_user_token_creation_no_duplicates(self):
        user = User.objects.create_user("username", "testuser@example.com", "password")
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Token.objects.count(), 1)

        user.username = "newusername"
        user.save()

        self.assertEqual(Token.objects.count(), 1)


class ConsentModelTests(TestCase):
    def test_url_generation(self):
        """
        Generates a URL that contains the code that reflects both the Consent and the
        contact UUID
        """
        org = Organization.objects.create()
        consent = Consent.objects.create(org=org)
        uuid = uuid4()
        expected_code = hashids.encode(consent.id, uuid.int)
        factory = RequestFactory()
        request = factory.get("/")

        url = consent.generate_url(request, uuid)

        self.assertIn(expected_code, url)

    def test_fetch_from_url(self):
        """
        Given the code, we should be able to retrieve both the Consent and the contact
        UUID
        """
        org = Organization.objects.create()
        consent = Consent.objects.create(org=org)
        uuid = uuid4()
        code = hashids.encode(consent.id, uuid.int)

        result_consent, result_uuid = Consent.from_code(code)

        self.assertEqual(result_consent, consent)
        self.assertEqual(result_uuid, uuid)
