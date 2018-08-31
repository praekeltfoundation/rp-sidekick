from django.test import TestCase
from django.utils import timezone

from sidekick import utils


class UtilsTests(TestCase):
    def test_get_today(self):

        self.assertEqual(utils.get_today(), timezone.now().date())
