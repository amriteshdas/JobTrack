import pytest
from django.utils import timezone

from apps.jobs.models import Job, Skill

JOBS = "/api/jobs/"
COMPANIES = "/api/companies/"


def make_job(company, employer, **overrides):
    defaults = dict(
        company=company,
        posted_by=employer.employer_profile,
        title="Backend Engineer",
        description="Build REST APIs with Django.",
        location="Kolkata",
        work_mode=Job.WorkMode.REMOTE,
        employment_type=Job.EmploymentType.FULL_TIME,
        experience_required=2,
        salary_min=600000,
        salary_max=1200000,
        status=Job.Status.PUBLISHED,
        published_at=timezone.now(),
    )
    defaults.update(overrides)
    return Job.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Free-text search
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_search_matches_title(api_client, company_a, employer_a):
    make_job(company_a, employer_a, title="Senior Django Developer")
    make_job(company_a, employer_a, title="Marketing Manager", description="Run campaigns.")

    r = api_client.get(JOBS, {"search": "django"})
    titles = [j["title"] for j in r.data["results"]]
    assert titles == ["Senior Django Developer"]


@pytest.mark.django_db
def test_search_matches_company_name(api_client, company_a, employer_a):
    make_job(company_a, employer_a, title="Backend Engineer")
    r = api_client.get(JOBS, {"search": company_a.name})
    assert r.data["count"] == 1


@pytest.mark.django_db
def test_search_is_case_insensitive(api_client, company_a, employer_a):
    make_job(company_a, employer_a, title="Python Developer")
    r = api_client.get(JOBS, {"search": "PYTHON"})
    assert r.data["count"] == 1


@pytest.mark.django_db
def test_search_excludes_non_matching_jobs(api_client, company_a, employer_a):
    make_job(company_a, employer_a, title="Backend Engineer")
    r = api_client.get(JOBS, {"search": "nonexistent-term-xyz"})
    assert r.data["count"] == 0


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_filter_by_location(api_client, company_a, employer_a):
    make_job(company_a, employer_a, location="Kolkata")
    make_job(company_a, employer_a, location="Bangalore")
    r = api_client.get(JOBS, {"location": "kolkata"})  # icontains, case-insensitive
    assert r.data["count"] == 1


@pytest.mark.django_db
def test_filter_by_work_mode(api_client, company_a, employer_a):
    make_job(company_a, employer_a, work_mode=Job.WorkMode.REMOTE)
    make_job(company_a, employer_a, work_mode=Job.WorkMode.ONSITE)
    r = api_client.get(JOBS, {"work_mode": "remote"})
    assert r.data["count"] == 1
    assert r.data["results"][0]["work_mode"] == "remote"


@pytest.mark.django_db
def test_invalid_work_mode_returns_400(api_client):
    """ChoiceFilter rejects an unknown value instead of silently matching nothing."""
    r = api_client.get(JOBS, {"work_mode": "banana"})
    assert r.status_code == 400


@pytest.mark.django_db
def test_filter_by_employment_type(api_client, company_a, employer_a):
    make_job(company_a, employer_a, employment_type=Job.EmploymentType.INTERNSHIP)
    make_job(company_a, employer_a, employment_type=Job.EmploymentType.FULL_TIME)
    r = api_client.get(JOBS, {"employment_type": "internship"})
    assert r.data["count"] == 1


@pytest.mark.django_db
def test_filter_by_experience_range(api_client, company_a, employer_a):
    make_job(company_a, employer_a, experience_required=0)
    make_job(company_a, employer_a, experience_required=5)
    r = api_client.get(JOBS, {"experience_min": 3})
    assert r.data["count"] == 1


@pytest.mark.django_db
def test_filter_by_salary_range_overlap(api_client, company_a, employer_a):
    """
    A job paying 40k-90k should match a search for 'at least 60k' because the
    ranges OVERLAP, even though the job's own minimum (40k) is below 60k.
    """
    make_job(company_a, employer_a, salary_min=40000, salary_max=90000)
    make_job(company_a, employer_a, salary_min=20000, salary_max=30000)  # no overlap
    r = api_client.get(JOBS, {"salary_min": 60000})
    assert r.data["count"] == 1


@pytest.mark.django_db
def test_filter_by_skill(api_client, company_a, employer_a):
    job1 = make_job(company_a, employer_a, title="Python Role")
    job1.skills.add(Skill.objects.create(name="Python"))
    job2 = make_job(company_a, employer_a, title="Java Role")
    job2.skills.add(Skill.objects.create(name="Java"))

    r = api_client.get(JOBS, {"skill": "Python"})
    assert r.data["count"] == 1
    assert r.data["results"][0]["title"] == "Python Role"


@pytest.mark.django_db
def test_filter_by_company_slug(api_client, company_a, company_b, employer_a, employer_b):
    make_job(company_a, employer_a)
    make_job(company_b, employer_b)
    r = api_client.get(JOBS, {"company": company_a.slug})
    assert r.data["count"] == 1


@pytest.mark.django_db
def test_filters_compose_together(api_client, company_a, employer_a):
    make_job(
        company_a, employer_a, title="Remote Django Role",
        work_mode=Job.WorkMode.REMOTE, location="Kolkata",
    )
    make_job(
        company_a, employer_a, title="Onsite Django Role",
        work_mode=Job.WorkMode.ONSITE, location="Kolkata",
    )
    r = api_client.get(JOBS, {"search": "django", "work_mode": "remote"})
    assert r.data["count"] == 1
    assert r.data["results"][0]["title"] == "Remote Django Role"


@pytest.mark.django_db
def test_draft_jobs_never_appear_in_filtered_results(api_client, company_a, employer_a):
    make_job(company_a, employer_a, title="Hidden Role", status=Job.Status.DRAFT, published_at=None)
    r = api_client.get(JOBS, {"search": "hidden"})
    assert r.data["count"] == 0


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_default_ordering_is_newest_first(api_client, company_a, employer_a):
    import time

    make_job(company_a, employer_a, title="Older")
    time.sleep(0.01)
    make_job(company_a, employer_a, title="Newer")

    r = api_client.get(JOBS)
    assert [j["title"] for j in r.data["results"]] == ["Newer", "Older"]


@pytest.mark.django_db
def test_ordering_by_salary_ascending(api_client, company_a, employer_a):
    make_job(company_a, employer_a, title="High", salary_min=200000)
    make_job(company_a, employer_a, title="Low", salary_min=50000)
    r = api_client.get(JOBS, {"ordering": "salary_min"})
    assert [j["title"] for j in r.data["results"]] == ["Low", "High"]


@pytest.mark.django_db
def test_ordering_by_salary_descending(api_client, company_a, employer_a):
    make_job(company_a, employer_a, title="High", salary_min=200000)
    make_job(company_a, employer_a, title="Low", salary_min=50000)
    r = api_client.get(JOBS, {"ordering": "-salary_min"})
    assert [j["title"] for j in r.data["results"]] == ["High", "Low"]


@pytest.mark.django_db
def test_ordering_on_non_whitelisted_field_is_ignored_not_500(api_client, company_a, employer_a):
    """
    OrderingFilter silently falls back to the default ordering for a field
    not in `ordering_fields`, rather than erroring OR executing an
    unexpected sort. This test pins that behaviour so it cannot regress into
    letting a client sort on, say, an unindexed related field.
    """
    make_job(company_a, employer_a)
    r = api_client.get(JOBS, {"ordering": "posted_by__user__password"})
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_list_is_paginated(api_client, company_a, employer_a):
    for i in range(25):
        make_job(company_a, employer_a, title=f"Job {i}")

    r = api_client.get(JOBS)
    assert r.data["count"] == 25
    assert len(r.data["results"]) == 20  # PAGE_SIZE
    assert r.data["next"] is not None


@pytest.mark.django_db
def test_second_page_returns_remainder(api_client, company_a, employer_a):
    for i in range(25):
        make_job(company_a, employer_a, title=f"Job {i}")

    r = api_client.get(JOBS, {"page": 2})
    assert len(r.data["results"]) == 5
    assert r.data["next"] is None


@pytest.mark.django_db
def test_pagination_and_filtering_compose(api_client, company_a, employer_a):
    for i in range(25):
        make_job(company_a, employer_a, title=f"Django Job {i}", work_mode=Job.WorkMode.REMOTE)
    for i in range(5):
        make_job(company_a, employer_a, title=f"Java Job {i}", work_mode=Job.WorkMode.ONSITE)

    r = api_client.get(JOBS, {"work_mode": "remote", "page": 2})
    assert r.data["count"] == 25
    assert len(r.data["results"]) == 5


# ---------------------------------------------------------------------------
# Company marketplace surface
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_company_jobs_endpoint_returns_only_published(api_client, company_a, employer_a):
    make_job(company_a, employer_a, title="Live Role", status=Job.Status.PUBLISHED)
    make_job(company_a, employer_a, title="Draft Role", status=Job.Status.DRAFT, published_at=None)

    r = api_client.get(f"{COMPANIES}{company_a.slug}/jobs/")
    titles = [j["title"] for j in r.data["results"]]
    assert titles == ["Live Role"]


@pytest.mark.django_db
def test_company_jobs_endpoint_excludes_other_companies(
    api_client, company_a, company_b, employer_a, employer_b
):
    make_job(company_a, employer_a, title="A's job")
    make_job(company_b, employer_b, title="B's job")

    r = api_client.get(f"{COMPANIES}{company_a.slug}/jobs/")
    titles = [j["title"] for j in r.data["results"]]
    assert titles == ["A's job"]


@pytest.mark.django_db
def test_company_search_by_name(api_client, company_a, company_b):
    r = api_client.get(COMPANIES, {"search": "Acme"})
    names = [c["name"] for c in r.data["results"]]
    assert names == [company_a.name]


@pytest.mark.django_db
def test_company_detail_includes_open_jobs_count(api_client, company_a, employer_a):
    make_job(company_a, employer_a, status=Job.Status.PUBLISHED)
    make_job(company_a, employer_a, status=Job.Status.DRAFT, published_at=None)

    r = api_client.get(f"{COMPANIES}{company_a.slug}/")
    assert r.data["open_jobs_count"] == 1


@pytest.mark.django_db
def test_job_detail_includes_company_and_skills(api_client, company_a, employer_a):
    job = make_job(company_a, employer_a)
    job.skills.add(Skill.objects.create(name="Django"))

    r = api_client.get(f"{JOBS}{job.id}/")
    assert r.data["company_name"] == company_a.name
    assert r.data["skills"][0]["name"] == "Django"
    assert r.data["is_open"] is True
