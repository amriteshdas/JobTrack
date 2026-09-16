import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seeker(db):
    return User.objects.create_user(
        email="seeker@example.com",
        password="StrongPass123!",
        first_name="Sam",
        last_name="Seeker",
        role=User.Role.JOB_SEEKER,
    )


@pytest.fixture
def employer(db):
    return User.objects.create_user(
        email="employer@example.com",
        password="StrongPass123!",
        first_name="Erin",
        last_name="Employer",
        role=User.Role.EMPLOYER,
    )


@pytest.fixture
def auth_client(api_client):
    """
    Returns a factory that authenticates the client as a given user by
    performing a real login and attaching the resulting access token.

    Deliberately NOT using force_authenticate(): that bypasses the JWT layer
    entirely, so the tests would pass even if token issuing or parsing were
    broken. Going through the real login path means these tests exercise
    the whole authentication stack.
    """

    def _auth(user, password="StrongPass123!"):
        response = api_client.post(
            "/api/auth/login/",
            {"email": user.email, "password": password},
            format="json",
        )
        assert response.status_code == 200, response.data
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        return api_client

    return _auth
