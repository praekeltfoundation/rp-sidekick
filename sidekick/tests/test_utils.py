from django.test import TestCase
from django.utils import timezone

from sidekick import utils


class UtilsTests(TestCase):
    def test_get_today(self):

        self.assertEqual(utils.get_today(), timezone.now().date())

    def test_clean_message(self):

        self.assertEqual(
            utils.clean_message(
                "No new lines\nNo tabs\t              No huge spaces"
            ),
            "No new lines No tabs No huge spaces",
        )
