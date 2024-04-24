from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from .utils import create_test_strategy


class TestStrataValidationView(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )
        token = Token.objects.get(user=self.user)
        self.token = token.key

        self.api_client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

        self.strategy = create_test_strategy()

    def test_validate_strata_data_unauthenticated(self):
        api_client = APIClient()
        response = api_client.post(
            reverse(
                "validate_strata_data",
                kwargs={
                    "strategy_id": self.strategy.id,
                },
            ),
            data={"age-group": "18-29", "province": "WC"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_validate_strata_data_valid(self):
        response = self.api_client.post(
            reverse(
                "validate_strata_data",
                kwargs={
                    "strategy_id": self.strategy.id,
                },
            ),
            data={"age-group": "18-29", "province": "WC"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_body = response.json()
        self.assertTrue(response_body["valid"])

    def test_validate_strata_data_invalid(self):
        response = self.api_client.post(
            reverse(
                "validate_strata_data",
                kwargs={
                    "strategy_id": self.strategy.id,
                },
            ),
            data={"age-group": "18-89", "province": "WC"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_body = response.json()
        self.assertFalse(response_body["valid"])
        self.assertEqual(
            response_body["error"], "'18-89' is not one of ['18-29', '29-39']"
        )


class TestGetRandomArmView(APITestCase):
    def setUp(self):
        self.api_client = APIClient()

        self.user = User.objects.create_user(
            "username", "testuser@example.com", "password"
        )
        token = Token.objects.get(user=self.user)
        self.token = token.key

        self.api_client.credentials(HTTP_AUTHORIZATION="Token " + self.token)

        self.strategy = create_test_strategy()

    def test_get_random_arm_unauthenticated(self):
        api_client = APIClient()
        response = api_client.post(
            reverse(
                "get_random_arm",
                kwargs={
                    "strategy_id": self.strategy.id,
                },
            ),
            data={"age-group": "18-29", "province": "WC"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_random_arm_success(self):
        response = self.api_client.post(
            reverse(
                "get_random_arm",
                kwargs={
                    "strategy_id": self.strategy.id,
                },
            ),
            data={"age-group": "18-29", "province": "WC"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_body = response.json()
        valid_arms = [arm.name for arm in self.strategy.arms.all()]
        self.assertTrue(response_body["arm"] in valid_arms)

    def test_get_random_arm_error(self):
        response = self.api_client.post(
            reverse(
                "get_random_arm",
                kwargs={
                    "strategy_id": self.strategy.id,
                },
            ),
            data={"age-group": "18-89", "province": "WC"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response_body = response.json()
        self.assertEqual(
            response_body["error"], "'18-89' is not one of ['18-29', '29-39']"
        )
