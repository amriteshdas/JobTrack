import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

REGISTER_URL = "/api/auth/register/"
LOGIN_URL = "/api/auth/login/"
REFRESH_URL = "/api/auth/refresh/"
LOGOUT_URL = "/api/auth/logout/"
ME_URL = "/api/auth/me/"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_register_creates_user_and_returns_tokens(api_client):
    payload = {
        "email": "new@example.com",
        "password": "StrongPass123!",
        "password_confirm": "StrongPass123!",
        "first_name": "New",
        "last_name": "User",
        "role": "seeker",
    }
    response = api_client.post(REGISTER_URL, payload, format="json")

    assert response.status_code == 201
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["email"] == "new@example.com"
    assert response.data["user"]["role"] == "seeker"
    assert User.objects.filter(email="new@example.com").exists()


@pytest.mark.django_db
def test_register_never_returns_password(api_client):
    """A password (or its hash) leaking into a response is a real bug class."""
    response = api_client.post(
        REGISTER_URL,
        {
            "email": "leak@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "seeker",
        },
        format="json",
    )
    assert response.status_code == 201
    assert "password" not in response.data
    assert "password" not in response.data["user"]


@pytest.mark.django_db
def test_register_stores_password_hashed(api_client):
    api_client.post(
        REGISTER_URL,
        {
            "email": "hash@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "seeker",
        },
        format="json",
    )
    user = User.objects.get(email="hash@example.com")
    assert user.password != "StrongPass123!"
    assert user.check_password("StrongPass123!")


@pytest.mark.django_db
def test_register_rejects_mismatched_passwords(api_client):
    response = api_client.post(
        REGISTER_URL,
        {
            "email": "mismatch@example.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass123!",
            "role": "seeker",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "password_confirm" in response.data


@pytest.mark.django_db
def test_register_rejects_duplicate_email_case_insensitively(api_client, seeker):
    """"SEEKER@example.com" must not become a second account."""
    response = api_client.post(
        REGISTER_URL,
        {
            "email": "SEEKER@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "seeker",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_register_rejects_invalid_role(api_client):
    response = api_client.post(
        REGISTER_URL,
        {
            "email": "admin@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "admin",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "role" in response.data


@pytest.mark.django_db
def test_register_rejects_weak_password(api_client):
    response = api_client.post(
        REGISTER_URL,
        {
            "email": "weak@example.com",
            "password": "password",
            "password_confirm": "password",
            "role": "seeker",
        },
        format="json",
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_login_returns_tokens_and_user(api_client, seeker):
    response = api_client.post(
        LOGIN_URL,
        {"email": seeker.email, "password": "StrongPass123!"},
        format="json",
    )
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["user"]["role"] == "seeker"


@pytest.mark.django_db
def test_login_with_wrong_password_fails(api_client, seeker):
    response = api_client.post(
        LOGIN_URL,
        {"email": seeker.email, "password": "WrongPassword123!"},
        format="json",
    )
    assert response.status_code == 401


@pytest.mark.django_db
def test_login_fails_for_inactive_user(api_client, seeker):
    seeker.is_active = False
    seeker.save()
    response = api_client.post(
        LOGIN_URL,
        {"email": seeker.email, "password": "StrongPass123!"},
        format="json",
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Current user / protected endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_me_requires_authentication(api_client):
    response = api_client.get(ME_URL)
    assert response.status_code == 401


@pytest.mark.django_db
def test_me_returns_current_user(auth_client, seeker):
    client = auth_client(seeker)
    response = client.get(ME_URL)
    assert response.status_code == 200
    assert response.data["user"]["email"] == seeker.email


@pytest.mark.django_db
def test_garbage_token_is_rejected(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")
    response = api_client.get(ME_URL)
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Refresh & logout
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_refresh_returns_new_access_token(api_client, seeker):
    login = api_client.post(
        LOGIN_URL,
        {"email": seeker.email, "password": "StrongPass123!"},
        format="json",
    )
    response = api_client.post(
        REFRESH_URL, {"refresh": login.data["refresh"]}, format="json"
    )
    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_rotated_refresh_token_cannot_be_reused(api_client, seeker):
    """
    With ROTATE_REFRESH_TOKENS + BLACKLIST_AFTER_ROTATION, using a refresh
    token invalidates it. Replaying a stolen one must fail.
    """
    login = api_client.post(
        LOGIN_URL,
        {"email": seeker.email, "password": "StrongPass123!"},
        format="json",
    )
    original_refresh = login.data["refresh"]

    first = api_client.post(REFRESH_URL, {"refresh": original_refresh}, format="json")
    assert first.status_code == 200

    replay = api_client.post(REFRESH_URL, {"refresh": original_refresh}, format="json")
    assert replay.status_code == 401


@pytest.mark.django_db
def test_logout_blacklists_refresh_token(api_client, seeker):
    login = api_client.post(
        LOGIN_URL,
        {"email": seeker.email, "password": "StrongPass123!"},
        format="json",
    )
    refresh = login.data["refresh"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")

    logout = api_client.post(LOGOUT_URL, {"refresh": refresh}, format="json")
    assert logout.status_code == 205

    # The blacklisted refresh token must no longer buy a new access token.
    response = api_client.post(REFRESH_URL, {"refresh": refresh}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_logout_without_refresh_token_returns_400(auth_client, seeker):
    client = auth_client(seeker)
    response = client.post(LOGOUT_URL, {}, format="json")
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# Rate limiting on auth endpoints (Phase 9)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_login_is_rate_limited_after_repeated_attempts(api_client, seeker, settings):
    """
    Every other test in this suite runs with throttling neutralized (see
    the autouse fixture in backend/conftest.py) so repeated logins in
    other tests don't trip it. This test explicitly restores a real cache
    to prove the throttle actually engages when it should -- disabling it
    everywhere and never proving it works would leave a false sense of
    security.
    """
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

    responses = [
        api_client.post(
            LOGIN_URL, {"email": seeker.email, "password": "WrongPassword!"}, format="json"
        )
        for _ in range(11)  # one more than the "10/min" limit
    ]

    statuses = [r.status_code for r in responses]
    assert 429 in statuses, f"Expected a 429 after 10 requests, got statuses: {statuses}"

    throttled = next(r for r in responses if r.status_code == 429)
    assert throttled.data["code"] == "throttled"


@pytest.mark.django_db
def test_register_is_rate_limited_after_repeated_attempts(api_client, settings):
    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

    responses = [
        api_client.post(
            REGISTER_URL,
            {
                "email": f"flood{i}@example.com",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
                "role": "seeker",
            },
            format="json",
        )
        for i in range(11)
    ]
    assert any(r.status_code == 429 for r in responses)


# ---------------------------------------------------------------------------
# create_superuser (Phase 9 coverage pass)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_create_superuser_sets_staff_and_superuser_flags():
    user = User.objects.create_superuser(email="admin@jobtrack.local", password="StrongPass123!")
    assert user.is_staff is True
    assert user.is_superuser is True
    # Defaults to employer rather than leaving role unset -- an admin
    # account still needs to satisfy every IsEmployer/IsJobSeeker check
    # consistently if it's ever used to browse the app, not just /admin/.
    assert user.role == User.Role.EMPLOYER


@pytest.mark.django_db
def test_create_superuser_rejects_is_staff_false():
    with pytest.raises(ValueError, match="is_staff=True"):
        User.objects.create_superuser(
            email="admin2@jobtrack.local", password="StrongPass123!", is_staff=False
        )


@pytest.mark.django_db
def test_create_superuser_rejects_is_superuser_false():
    with pytest.raises(ValueError, match="is_superuser=True"):
        User.objects.create_superuser(
            email="admin3@jobtrack.local", password="StrongPass123!", is_superuser=False
        )


# ---------------------------------------------------------------------------
# Logout with a malformed/garbage refresh token (Phase 9 coverage pass)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_logout_with_garbage_refresh_token_returns_400_not_500(auth_client, seeker):
    client = auth_client(seeker)
    response = client.post(LOGOUT_URL, {"refresh": "this-is-not-a-real-token"}, format="json")
    assert response.status_code == 400
