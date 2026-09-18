import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.companies.models import Company, CompanyMembership
from apps.jobs.models import Job

User = get_user_model()
PASSWORD = "StrongPass123!"


@pytest.fixture
def api_client():
    return APIClient()


def _make_user(email, role):
    return User.objects.create_user(
        email=email, password=PASSWORD, first_name="Test", last_name="User", role=role
    )


@pytest.fixture
def seeker_a(db):
    return _make_user("seeker.a@example.com", User.Role.JOB_SEEKER)


@pytest.fixture
def seeker_b(db):
    """A second, unrelated seeker -- for object-level isolation tests."""
    return _make_user("seeker.b@example.com", User.Role.JOB_SEEKER)


@pytest.fixture
def employer(db):
    return _make_user("employer@acme.com", User.Role.EMPLOYER)


@pytest.fixture
def auth(api_client):
    def _auth(user):
        r = api_client.post(
            "/api/auth/login/", {"email": user.email, "password": PASSWORD}, format="json"
        )
        assert r.status_code == 200, r.data
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        return api_client

    return _auth


@pytest.fixture
def company(employer):
    c = Company.objects.create(name="Acme Corp", location="Kolkata")
    CompanyMembership.objects.create(
        company=c,
        employer_profile=employer.employer_profile,
        membership_role=CompanyMembership.MembershipRole.OWNER,
    )
    return c


@pytest.fixture
def published_job(company, employer):
    from django.utils import timezone

    return Job.objects.create(
        company=company,
        posted_by=employer.employer_profile,
        title="Backend Engineer",
        description="Build APIs.",
        location="Kolkata",
        work_mode=Job.WorkMode.REMOTE,
        employment_type=Job.EmploymentType.FULL_TIME,
        status=Job.Status.PUBLISHED,
        published_at=timezone.now(),
    )


@pytest.fixture
def draft_job(company, employer):
    return Job.objects.create(
        company=company,
        posted_by=employer.employer_profile,
        title="Secret Role",
        description="Not public yet.",
        location="Kolkata",
        work_mode=Job.WorkMode.HYBRID,
        employment_type=Job.EmploymentType.FULL_TIME,
        status=Job.Status.DRAFT,
    )
