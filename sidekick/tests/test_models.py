from django.test import TestCase
from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token


class TestUserTokenSignal(TestCase):
    def test_user_token_creation(self):
        user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )
        self.assertTrue(Token.objects.get(user=user))

    def test_user_token_deletion(self):
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Token.objects.count(), 0)

        user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Token.objects.count(), 1)

        user.delete()

        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Token.objects.count(), 0)

    def test_user_token_creation_no_duplicates(self):
        user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Token.objects.count(), 1)

        user.username = "newusername"
        user.save()

        self.assertEqual(Token.objects.count(), 1)
