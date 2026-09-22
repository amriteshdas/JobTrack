import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_unauthenticated_request_gets_detail_and_code():
    client = APIClient()
    r = client.get("/api/auth/me/")
    assert r.status_code == 401
    assert r.data["detail"]
    assert r.data["code"] == "not_authenticated"


@pytest.mark.django_db
def test_forbidden_request_gets_detail_and_code():
    from django.contrib.auth import get_user_model

    User = get_user_model()
    employer = User.objects.create_user(
        email="employer@x.com", password="StrongPass123!", role=User.Role.EMPLOYER
    )
    client = APIClient()
    login = client.post(
        "/api/auth/login/", {"email": employer.email, "password": "StrongPass123!"}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    r = client.get("/api/profiles/seeker/me/")
    assert r.status_code == 403
    assert r.data["code"] == "permission_denied"


@pytest.mark.django_db
def test_missing_object_via_drf_generic_view_gets_json_envelope():
    """
    DRF's generic views (EducationViewSet here is a plain ModelViewSet)
    raise Http404 automatically via get_object_or_404 when the requested
    id isn't in the queryset -- that's the actual Http404 branch this
    handler exists for. An unmatched URL is a DIFFERENT case: Django's URL
    resolver rejects it before any view or exception handler runs at all,
    so that path is not something a DRF exception handler can control.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    seeker = User.objects.create_user(
        email="seeker2@x.com", password="StrongPass123!", role=User.Role.JOB_SEEKER
    )
    client = APIClient()
    login = client.post(
        "/api/auth/login/", {"email": seeker.email, "password": "StrongPass123!"}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    r = client.get("/api/profiles/seeker/me/education/999999/")
    assert r.status_code == 404
    assert r["Content-Type"].startswith("application/json")
    assert r.data["detail"]


@pytest.mark.django_db
def test_validation_error_shape_is_unchanged():
    """
    The handler must NOT touch field-level validation errors -- every view
    in this project (and the whole frontend) relies on err.response.data
    being {"field_name": ["message"]}, not a wrapped {"detail": ..., "code": ...}.
    """
    client = APIClient()
    r = client.post(
        "/api/auth/register/",
        {"email": "not-an-email", "password": "x", "password_confirm": "y", "role": "seeker"},
        format="json",
    )
    assert r.status_code == 400
    assert "email" in r.data
    assert "code" not in r.data
