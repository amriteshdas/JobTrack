import pytest

from apps.companies.models import Company, CompanyMembership
from apps.jobs.models import Job, Skill

JOBS = "/api/jobs/"
COMPANIES = "/api/companies/"


def job_payload(company, **overrides):
    payload = {
        "company": company.id,
        "title": "Django Developer",
        "description": "Work on the API.",
        "location": "Kolkata",
        "work_mode": "remote",
        "employment_type": "full_time",
        "skills": ["Python", "Django"],
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Employer profile auto-creation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_gets_profile_on_registration(api_client):
    api_client.post(
        "/api/auth/register/",
        {
            "email": "new@corp.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "employer",
        },
        format="json",
    )
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.get(email="new@corp.com")
    assert hasattr(user, "employer_profile")


@pytest.mark.django_db
def test_seeker_does_not_get_employer_profile(seeker):
    assert not hasattr(seeker, "employer_profile")


@pytest.mark.django_db
def test_seeker_cannot_access_employer_profile_endpoint(auth, seeker):
    client = auth(seeker)
    assert client.get("/api/profiles/employer/me/").status_code == 403


# ---------------------------------------------------------------------------
# Company creation & ownership
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_can_create_company_and_becomes_owner(auth, employer_a):
    client = auth(employer_a)
    r = client.post(COMPANIES, {"name": "New Startup", "location": "Pune"}, format="json")
    assert r.status_code == 201

    company = Company.objects.get(name="New Startup")
    membership = company.memberships.get()
    assert membership.employer_profile == employer_a.employer_profile
    assert membership.membership_role == CompanyMembership.MembershipRole.OWNER


@pytest.mark.django_db
def test_seeker_cannot_create_company(auth, seeker):
    client = auth(seeker)
    r = client.post(COMPANIES, {"name": "Fake Co"}, format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_company_list_is_public(api_client, company_a):
    assert api_client.get(COMPANIES).status_code == 200


@pytest.mark.django_db
def test_employer_cannot_edit_another_companys_profile(auth, employer_b, company_a):
    """Employer B is a legitimate employer -- just not of Acme."""
    client = auth(employer_b)
    r = client.patch(f"{COMPANIES}{company_a.slug}/", {"name": "Hijacked"}, format="json")
    assert r.status_code == 403
    company_a.refresh_from_db()
    assert company_a.name == "Acme Corp"


@pytest.mark.django_db
def test_member_can_edit_own_company(auth, employer_a, company_a):
    client = auth(employer_a)
    r = client.patch(f"{COMPANIES}{company_a.slug}/", {"location": "Remote"}, format="json")
    assert r.status_code == 200


@pytest.mark.django_db
def test_slug_is_generated_and_unique(auth, employer_a):
    client = auth(employer_a)
    client.post(COMPANIES, {"name": "Duplicate Name"}, format="json")
    client.post(COMPANIES, {"name": "Duplicate Name"}, format="json")
    slugs = list(Company.objects.filter(name="Duplicate Name").values_list("slug", flat=True))
    assert len(set(slugs)) == 2


# ---------------------------------------------------------------------------
# Membership management
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_owner_can_add_member(auth, employer_a, employer_b, company_a):
    client = auth(employer_a)
    r = client.post(
        f"{COMPANIES}{company_a.slug}/members/add/",
        {"email": employer_b.email, "membership_role": "recruiter"},
        format="json",
    )
    assert r.status_code == 201
    assert company_a.memberships.count() == 2


@pytest.mark.django_db
def test_adding_same_member_twice_returns_409(auth, employer_a, employer_b, company_a):
    client = auth(employer_a)
    url = f"{COMPANIES}{company_a.slug}/members/add/"
    client.post(url, {"email": employer_b.email}, format="json")
    r = client.post(url, {"email": employer_b.email}, format="json")
    assert r.status_code == 409


@pytest.mark.django_db
def test_cannot_add_seeker_as_company_member(auth, employer_a, seeker, company_a):
    client = auth(employer_a)
    r = client.post(
        f"{COMPANIES}{company_a.slug}/members/add/", {"email": seeker.email}, format="json"
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_recruiter_cannot_add_members(auth, employer_a, employer_b, company_a):
    """Recruiters manage jobs; only owners manage who has access."""
    CompanyMembership.objects.create(
        company=company_a,
        employer_profile=employer_b.employer_profile,
        membership_role=CompanyMembership.MembershipRole.RECRUITER,
    )
    client = auth(employer_b)
    r = client.post(
        f"{COMPANIES}{company_a.slug}/members/add/", {"email": "x@y.com"}, format="json"
    )
    assert r.status_code == 403


@pytest.mark.django_db
def test_cannot_remove_only_owner(auth, employer_a, company_a):
    client = auth(employer_a)
    membership = company_a.memberships.get()
    r = client.delete(f"{COMPANIES}{company_a.slug}/members/{membership.id}/")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# Job creation
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_can_create_job_for_own_company(auth, employer_a, company_a):
    client = auth(employer_a)
    r = client.post(JOBS, job_payload(company_a), format="json")
    assert r.status_code == 201
    assert r.data["status"] == "draft"  # drafts by default, not live immediately
    assert {s["name"] for s in r.data["skills"]} == {"Python", "Django"}


@pytest.mark.django_db
def test_employer_cannot_create_job_for_another_company(auth, employer_b, company_a):
    """
    The payload names someone else's company id. Without validation on the
    FK, Employer B could post jobs under Acme's brand.
    """
    client = auth(employer_b)
    r = client.post(JOBS, job_payload(company_a), format="json")
    assert r.status_code == 400
    assert "company" in r.data
    assert not Job.objects.filter(company=company_a, title="Django Developer").exists()


@pytest.mark.django_db
def test_seeker_cannot_create_job(auth, seeker, company_a):
    client = auth(seeker)
    assert client.post(JOBS, job_payload(company_a), format="json").status_code == 403


@pytest.mark.django_db
def test_anonymous_cannot_create_job(api_client, company_a):
    assert api_client.post(JOBS, job_payload(company_a), format="json").status_code == 401


@pytest.mark.django_db
def test_posted_by_comes_from_token_not_payload(auth, employer_a, employer_b, company_a):
    client = auth(employer_a)
    r = client.post(
        JOBS,
        job_payload(company_a, posted_by=employer_b.employer_profile.id),
        format="json",
    )
    assert r.status_code == 201
    job = Job.objects.get(id=r.data["id"])
    assert job.posted_by == employer_a.employer_profile


@pytest.mark.django_db
def test_skills_are_deduplicated_case_insensitively(auth, employer_a, company_a):
    client = auth(employer_a)
    client.post(JOBS, job_payload(company_a, skills=["Python"]), format="json")
    client.post(JOBS, job_payload(company_a, skills=["python", "PYTHON"]), format="json")
    assert Skill.objects.filter(name__iexact="python").count() == 1


@pytest.mark.django_db
def test_salary_max_below_min_is_rejected(auth, employer_a, company_a):
    client = auth(employer_a)
    r = client.post(
        JOBS, job_payload(company_a, salary_min=100000, salary_max=50000), format="json"
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_past_deadline_is_rejected(auth, employer_a, company_a):
    client = auth(employer_a)
    r = client.post(
        JOBS, job_payload(company_a, application_deadline="2020-01-01"), format="json"
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Job editing & deletion -- object-level ownership
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_can_edit_own_job(auth, employer_a, published_job):
    client = auth(employer_a)
    r = client.patch(f"{JOBS}{published_job.id}/", {"title": "Senior Backend"}, format="json")
    assert r.status_code == 200
    published_job.refresh_from_db()
    assert published_job.title == "Senior Backend"


@pytest.mark.django_db
def test_employer_cannot_edit_another_employers_job(auth, employer_b, published_job):
    client = auth(employer_b)
    r = client.patch(f"{JOBS}{published_job.id}/", {"title": "Hijacked"}, format="json")
    assert r.status_code == 403
    published_job.refresh_from_db()
    assert published_job.title == "Backend Engineer"


@pytest.mark.django_db
def test_employer_cannot_delete_another_employers_job(auth, employer_b, published_job):
    client = auth(employer_b)
    assert client.delete(f"{JOBS}{published_job.id}/").status_code == 403
    assert Job.objects.filter(id=published_job.id).exists()


@pytest.mark.django_db
def test_employer_can_delete_own_job(auth, employer_a, published_job):
    client = auth(employer_a)
    assert client.delete(f"{JOBS}{published_job.id}/").status_code == 204


@pytest.mark.django_db
def test_forged_role_claim_cannot_bypass_ownership(api_client, seeker, published_job):
    """
    Phase 2 proved a forged JWT role claim cannot pass a ROLE check.
    This proves the same for an OBJECT-level check: authorization reads the
    database, never the token payload.
    """
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(seeker)
    token["role"] = "employer"  # a lie, correctly signed
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    r = api_client.patch(f"{JOBS}{published_job.id}/", {"title": "Owned"}, format="json")
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Draft/published visibility
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_public_list_excludes_drafts(api_client, published_job, draft_job):
    r = api_client.get(JOBS)
    titles = [j["title"] for j in r.data["results"]]
    assert "Backend Engineer" in titles
    assert "Secret Role" not in titles


@pytest.mark.django_db
def test_draft_returns_404_to_outsiders_not_403(api_client, draft_job):
    """404 not 403: confirming a hidden job exists at this id is itself a leak."""
    assert api_client.get(f"{JOBS}{draft_job.id}/").status_code == 404


@pytest.mark.django_db
def test_draft_is_visible_to_its_own_company(auth, employer_a, draft_job):
    client = auth(employer_a)
    assert client.get(f"{JOBS}{draft_job.id}/").status_code == 200


@pytest.mark.django_db
def test_draft_is_not_visible_to_other_employers(auth, employer_b, draft_job):
    client = auth(employer_b)
    assert client.get(f"{JOBS}{draft_job.id}/").status_code == 404


@pytest.mark.django_db
def test_published_job_is_public(api_client, published_job):
    assert api_client.get(f"{JOBS}{published_job.id}/").status_code == 200


@pytest.mark.django_db
def test_closed_job_remains_publicly_viewable(auth, employer_a, published_job):
    """
    Fixed during Phase 6: a CLOSED job was publicly known while it was
    published (someone may have bookmarked or applied to it), so unlike a
    DRAFT it stays visible -- `is_open` communicates "can't apply anymore",
    not a 404. Only DRAFT is private to the owning company.
    """
    client = auth(employer_a)
    client.post(f"{JOBS}{published_job.id}/close/")

    from rest_framework.test import APIClient
    outsider = APIClient()
    r = outsider.get(f"{JOBS}{published_job.id}/")
    assert r.status_code == 200
    assert r.data["status"] == "closed"
    assert r.data["is_open"] is False


# ---------------------------------------------------------------------------
# Publish / unpublish / close
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_publish_sets_status_and_published_at(auth, employer_a, draft_job):
    client = auth(employer_a)
    r = client.post(f"{JOBS}{draft_job.id}/publish/")
    assert r.status_code == 200
    draft_job.refresh_from_db()
    assert draft_job.status == Job.Status.PUBLISHED
    assert draft_job.published_at is not None


@pytest.mark.django_db
def test_republishing_preserves_original_published_at(auth, employer_a, draft_job):
    """Posted date must stay stable across unpublish/republish cycles."""
    client = auth(employer_a)
    client.post(f"{JOBS}{draft_job.id}/publish/")
    draft_job.refresh_from_db()
    first = draft_job.published_at

    client.post(f"{JOBS}{draft_job.id}/unpublish/")
    client.post(f"{JOBS}{draft_job.id}/publish/")
    draft_job.refresh_from_db()
    assert draft_job.published_at == first


@pytest.mark.django_db
def test_publishing_twice_returns_409(auth, employer_a, published_job):
    client = auth(employer_a)
    assert client.post(f"{JOBS}{published_job.id}/publish/").status_code == 409


@pytest.mark.django_db
def test_other_employer_cannot_publish_your_draft(auth, employer_b, draft_job):
    client = auth(employer_b)
    assert client.post(f"{JOBS}{draft_job.id}/publish/").status_code == 403


@pytest.mark.django_db
def test_closed_job_is_not_open_for_applications(auth, employer_a, published_job):
    client = auth(employer_a)
    client.post(f"{JOBS}{published_job.id}/close/")
    published_job.refresh_from_db()
    assert published_job.status == Job.Status.CLOSED
    assert published_job.is_open is False


# ---------------------------------------------------------------------------
# /jobs/mine/
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_mine_returns_all_own_jobs_including_drafts(auth, employer_a, published_job, draft_job):
    client = auth(employer_a)
    r = client.get(f"{JOBS}mine/")
    assert r.status_code == 200
    assert {j["title"] for j in r.data} == {"Backend Engineer", "Secret Role"}


@pytest.mark.django_db
def test_mine_excludes_other_companies_jobs(auth, employer_b, company_b, published_job):
    client = auth(employer_b)
    r = client.get(f"{JOBS}mine/")
    assert r.data == []


# ---------------------------------------------------------------------------
# JobWriteSerializer edge cases (Phase 9 coverage pass)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_creating_a_job_already_published_stamps_published_at(auth, employer_a, company_a):
    """
    Every other publish test goes through the dedicated /publish/ action.
    This covers the other path: status="published" set directly in the
    creation payload should still stamp published_at, not leave it null.
    """
    client = auth(employer_a)
    r = client.post(JOBS, job_payload(company_a, status="published"), format="json")
    assert r.status_code == 201
    assert r.data["status"] == "published"
    assert r.data["published_at"] is not None


@pytest.mark.django_db
def test_patching_status_to_published_stamps_published_at(auth, employer_a, draft_job):
    """Same as above, via PATCH rather than the /publish/ action."""
    client = auth(employer_a)
    r = client.patch(f"{JOBS}{draft_job.id}/", {"status": "published"}, format="json")
    assert r.status_code == 200
    assert r.data["published_at"] is not None


@pytest.mark.django_db
def test_updating_skills_via_patch_replaces_the_set(auth, employer_a, published_job):
    client = auth(employer_a)
    client.patch(f"{JOBS}{published_job.id}/", {"skills": ["Python"]}, format="json")
    r = client.patch(f"{JOBS}{published_job.id}/", {"skills": ["Go", "Rust"]}, format="json")
    assert {s["name"] for s in r.data["skills"]} == {"Go", "Rust"}


@pytest.mark.django_db
def test_sync_skills_skips_blank_entries_after_stripping(employer_a, company_a):
    """
    Not reachable through the public API at all: DRF's CharField has
    trim_whitespace=True by default, so it strips AND rejects a
    whitespace-only list entry with "This field may not be blank." before
    _sync_skills ever runs (confirmed directly against a live server --
    POSTing skills=["Python", "   "] returns 400 from the field itself,
    not a 201 with the whitespace entry silently dropped).

    _sync_skills' own strip+skip is kept anyway as defense-in-depth: it's
    a shared private helper, not exclusively reachable via this one
    DRF-validated path, so a future caller that builds a skills list by
    hand (a bulk-import script, an admin action) would still be protected.
    Since the public API can never exercise that branch, testing it means
    calling the private method directly -- the honest way to cover
    defense-in-depth code the "real" path can't reach, rather than
    contriving a fake API request that doesn't represent how it's used.
    """
    from apps.jobs.serializers import JobWriteSerializer

    job = Job.objects.create(
        company=company_a, posted_by=employer_a.employer_profile,
        title="Coverage Job", description="d", location="K",
        work_mode=Job.WorkMode.REMOTE, employment_type=Job.EmploymentType.FULL_TIME,
    )

    JobWriteSerializer()._sync_skills(job, ["Python", "   ", "Django"])

    assert {s.name for s in job.skills.all()} == {"Python", "Django"}
    assert not Skill.objects.filter(name="").exists()
