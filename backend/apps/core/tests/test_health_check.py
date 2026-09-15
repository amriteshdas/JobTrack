import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_returns_ok():
    """
    Deliberately trivial: this test exists only to prove the test
    infrastructure itself works end-to-end (pytest -> pytest-django ->
    a real, migrated test database -> DRF's test client -> a response).
    Every later phase's tests build on this same pattern.
    """
    client = APIClient()
    response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.data["status"] == "ok"
