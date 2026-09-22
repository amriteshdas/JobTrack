import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.companies.models import Company, CompanyMembership

User = get_user_model()
PASSWORD = "StrongPass123!"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def employer(db):
    return User.objects.create_user(
        email="employer@acme.com", password=PASSWORD, role=User.Role.EMPLOYER
    )


@pytest.fixture
def company(employer):
    c = Company.objects.create(name="Acme Corp", location="Kolkata")
    CompanyMembership.objects.create(
        company=c,
        employer_profile=employer.employer_profile,
        membership_role=CompanyMembership.MembershipRole.OWNER,
    )
    return c
