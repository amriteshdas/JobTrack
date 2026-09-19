import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
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
def seeker(db):
    return _make_user("seeker@example.com", User.Role.JOB_SEEKER)


@pytest.fixture
def other_seeker(db):
    return _make_user("other.seeker@example.com", User.Role.JOB_SEEKER)


@pytest.fixture
def employer(db):
    return _make_user("employer@acme.com", User.Role.EMPLOYER)


@pytest.fixture
def colleague(db):
    """A second recruiter at the SAME company -- interviews are company-scoped, not scheduler-scoped."""
    return _make_user("colleague@acme.com", User.Role.EMPLOYER)


@pytest.fixture
def other_employer(db):
    return _make_user("employer@globex.com", User.Role.EMPLOYER)


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
def company(employer, colleague):
    c = Company.objects.create(name="Acme Corp", location="Kolkata")
    CompanyMembership.objects.create(
        company=c, employer_profile=employer.employer_profile,
        membership_role=CompanyMembership.MembershipRole.OWNER,
    )
    CompanyMembership.objects.create(
        company=c, employer_profile=colleague.employer_profile,
        membership_role=CompanyMembership.MembershipRole.RECRUITER,
    )
    return c


@pytest.fixture
def other_company(other_employer):
    c = Company.objects.create(name="Globex", location="Mumbai")
    CompanyMembership.objects.create(
        company=c, employer_profile=other_employer.employer_profile,
        membership_role=CompanyMembership.MembershipRole.OWNER,
    )
    return c


@pytest.fixture
def published_job(company, employer):
    return Job.objects.create(
        company=company, posted_by=employer.employer_profile, title="Backend Engineer",
        description="Build APIs.", location="Kolkata", work_mode=Job.WorkMode.REMOTE,
        employment_type=Job.EmploymentType.FULL_TIME, status=Job.Status.PUBLISHED,
        published_at=timezone.now(),
    )


@pytest.fixture
def resume_file():
    def _make():
        return SimpleUploadedFile("resume.pdf", b"%PDF-1.4 fake resume", content_type="application/pdf")
    return _make


@pytest.fixture
def application(auth, seeker, published_job, resume_file):
    client = auth(seeker)
    r = client.post(
        f"/api/jobs/{published_job.id}/apply/", {"resume": resume_file()}, format="multipart"
    )
    assert r.status_code == 201, r.data
    from apps.applications.models import Application

    return Application.objects.get(id=r.data["id"])
