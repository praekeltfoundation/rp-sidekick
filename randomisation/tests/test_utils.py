import random
from collections import defaultdict

from django.test import TestCase

from randomisation.models import StrataMatrix
from randomisation.utils import (
    get_random_stratification_arm,
    validate_stratification_data,
)

from .utils import create_test_strategy


class TestValidateStratificationData(TestCase):
    def setUp(self):
        self.strategy = create_test_strategy()

    def test_stratification_validation_valid_data(self):
        """
        Test with valid data
        """
        error = validate_stratification_data(
            self.strategy, {"age-group": "18-29", "province": "WC"}
        )
        self.assertIsNone(error)

    def test_stratification_validation_missing_key(self):
        """
        Test with a missing strata key
        """
        error = validate_stratification_data(self.strategy, {"age-group": "18-29"})
        self.assertEqual(error, "'province' is a required property")

    def test_stratification_validation_extra_key(self):
        """
        Test with strata key that is not configured
        """
        error = validate_stratification_data(
            self.strategy, {"age-group": "18-29", "province": "WC", "extra": "key"}
        )

        self.assertEqual(
            error, "Additional properties are not allowed ('extra' was unexpected)"
        )

    def test_stratification_validation_invalid_option(self):
        """
        Test with invalid strata value
        """
        error = validate_stratification_data(
            self.strategy, {"age-group": "18-29", "province": "FS"}
        )
        self.assertEqual(error, "'FS' is not one of ['WC', 'GT']")


class TestGetRandomStratification(TestCase):
    def test_random_arm(self):
        """
        Test that it returns a random arm that matches the first item in the matrix
        object it created and next index is set
        """
        strategy = create_test_strategy()

        data = {"age-group": "18-29", "province": "WC"}
        random_arm = get_random_stratification_arm(strategy, data)

        strata_arm = StrataMatrix.objects.first()

        self.assertEqual(random_arm, strata_arm.arm_order.split(",")[0])
        self.assertEqual(strata_arm.next_index, 1)

    def test_random_arm_with_matrix(self):
        """
        Check the next arm from the existing matrix record and the next_idnex is updated
        """
        strategy = create_test_strategy()

        data = {"age-group": "18-29", "province": "WC"}

        StrataMatrix.objects.create(
            strategy=strategy,
            strata_data=data,
            next_index=1,
            arm_order="Arm 1,Arm 2,Arm 3",
        )

        random_arm = get_random_stratification_arm(strategy, data)

        strata_arm = StrataMatrix.objects.first()

        self.assertEqual(random_arm, "Arm 2")
        self.assertEqual(strata_arm.next_index, 2)

    def test_random_arm_out_of_index(self):
        """
        Test for out of index to delete the order after maximum arm
        """

        strategy = create_test_strategy()

        data = {"age-group": "18-29", "province": "WC"}

        StrataMatrix.objects.create(
            strategy=strategy,
            strata_data=data,
            next_index=2,
            arm_order="Arm 1,Arm 2,Arm 3",
        )

        random_arm = get_random_stratification_arm(strategy, data)

        self.assertEqual(StrataMatrix.objects.count(), 0)
        self.assertEqual(random_arm, "Arm 3")

    def test_stratification_balancing(self):
        """
        Testing that after 100 iterations that the resuls are balanced accross the
        configured arms in total and per strata group
        """
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
