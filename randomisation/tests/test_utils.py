import random
from collections import defaultdict

from django.test import TestCase

from randomisation.utils import (
    get_random_stratification_arm,
    validate_stratification_data,
)

from .utils import create_test_strategy


# TODO: add docstrings to tests
class TestValidateStratificationData(TestCase):
    def setUp(self):
        self.strategy = create_test_strategy()

    def test_stratification_validation_valid_data(self):
        error = validate_stratification_data(
            self.strategy, {"age-group": "18-29", "province": "WC"}
        )
        self.assertIsNone(error)

    def test_stratification_validation_missing_key(self):
        error = validate_stratification_data(self.strategy, {"age-group": "18-29"})
        self.assertEqual(error, "'province' is a required property")

    def test_stratification_validation_extra_key(self):
        error = validate_stratification_data(
            self.strategy, {"age-group": "18-29", "province": "WC", "extra": "key"}
        )

        self.assertEqual(
            error, "Additional properties are not allowed ('extra' was unexpected)"
        )

    def test_stratification_validation_invalid_option(self):
        error = validate_stratification_data(
            self.strategy, {"age-group": "18-29", "province": "FS"}
        )
        self.assertEqual(error, "'FS' is not one of ['WC', 'GT']")


class TestGetRandomStratification(TestCase):

    # TODO: add more tests for randomisation

    def test_stratification_balancing(self):
        strategy = create_test_strategy()

        totals = defaultdict(int)
        stratas = defaultdict(lambda: defaultdict(int))
        for i in range(100):
            random_age = random.choice(["18-29", "29-39"])
            random_province = random.choice(["WC", "GT"])

            data = {"age-group": random_age, "province": random_province}

            random_arm = get_random_stratification_arm(strategy, data)
            stratas[f"{random_age}_{random_province}"][random_arm] += 1
            totals[random_arm] += 1

        def check_arms_balanced(arms, diff, description):
            values = [value for value in arms.values()]
            msg = f"Arms not balanced: {description} - {values}"
            assert max(values) - diff < values[0] < min(values) + diff, msg

        check_arms_balanced(totals, 3, "Totals")

        for key, arms in stratas.items():
            check_arms_balanced(arms, 3, key)
