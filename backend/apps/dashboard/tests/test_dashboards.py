import pytest

from apps.applications.models import Application, SavedJob
from apps.jobs.models import Skill

from .conftest import make_job

SEEKER_DASH = "/api/dashboard/seeker/"
EMPLOYER_DASH = "/api/dashboard/employer/"


def apply(client, job_id, resume_factory):
    return client.post(f"/api/jobs/{job_id}/apply/", {"resume": resume_factory()}, format="multipart")


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_seeker_dashboard_requires_seeker_role(auth, employer):
    client = auth(employer)
    assert client.get(SEEKER_DASH).status_code == 403


@pytest.mark.django_db
def test_employer_dashboard_requires_employer_role(auth, seeker):
    client = auth(seeker)
    assert client.get(EMPLOYER_DASH).status_code == 403


@pytest.mark.django_db
def test_dashboards_require_authentication(api_client):
    assert api_client.get(SEEKER_DASH).status_code == 401
    assert api_client.get(EMPLOYER_DASH).status_code == 401


# ---------------------------------------------------------------------------
# Seeker dashboard
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_seeker_dashboard_empty_state(auth, seeker):
    client = auth(seeker)
    r = client.get(SEEKER_DASH)
    assert r.status_code == 200
    assert r.data["stats"]["total_applications"] == 0
    assert r.data["recent_applications"] == []
    assert r.data["upcoming_interviews"] == []


@pytest.mark.django_db
def test_seeker_dashboard_counts_applications_by_status(
    auth, seeker, employer, company, resume_file
):
    job1 = make_job(company, employer, title="Role A")
    job2 = make_job(company, employer, title="Role B")
    job3 = make_job(company, employer, title="Role C")

    client = auth(seeker)
    a1 = apply(client, job1.id, resume_file).data
    apply(client, job2.id, resume_file)
    apply(client, job3.id, resume_file)

    auth(employer).patch(
        f"/api/applications/{a1['id']}/status/", {"status": "shortlisted"}, format="json"
    )

    r = auth(seeker).get(SEEKER_DASH)
    assert r.data["stats"]["total_applications"] == 3
    assert r.data["stats"]["shortlisted"] == 1


@pytest.mark.django_db
def test_seeker_dashboard_counts_saved_jobs(auth, seeker, employer, company):
    job = make_job(company, employer)
    client = auth(seeker)
    client.post("/api/saved-jobs/", {"job": job.id}, format="json")

    r = client.get(SEEKER_DASH)
    assert r.data["stats"]["saved_jobs"] == 1


@pytest.mark.django_db
def test_seeker_dashboard_recent_applications_shape_is_flat(
    auth, seeker, employer, company, resume_file
):
    job = make_job(company, employer, title="Backend Engineer")
    client = auth(seeker)
    apply(client, job.id, resume_file)

    r = client.get(SEEKER_DASH)
    entry = r.data["recent_applications"][0]
    assert entry["job_title"] == "Backend Engineer"
    assert entry["company_name"] == company.name
    assert entry["status"] == "applied"
    # Deliberately flat -- not the full nested ApplicationSerializer shape.
    assert "job" not in entry
    assert "applicant" not in entry


@pytest.mark.django_db
def test_seeker_dashboard_isolated_per_user(auth, seeker, other_seeker, employer, company, resume_file):
    job = make_job(company, employer)
    apply(auth(other_seeker), job.id, resume_file)

    r = auth(seeker).get(SEEKER_DASH)
    assert r.data["stats"]["total_applications"] == 0


@pytest.mark.django_db
def test_recommended_jobs_matches_seeker_skills(auth, seeker, employer, company):
    python_job = make_job(company, employer, title="Python Role")
    python_job.skills.add(Skill.objects.create(name="Python"))

    java_job = make_job(company, employer, title="Java Role")
    java_job.skills.add(Skill.objects.create(name="Java"))

    client = auth(seeker)
    client.put("/api/profiles/seeker/me/skills/", {"skills": ["Python"]}, format="json")

    r = client.get(SEEKER_DASH)
    titles = [j["title"] for j in r.data["recommended_jobs"]]
    assert "Python Role" in titles
    assert "Java Role" not in titles


@pytest.mark.django_db
def test_recommended_jobs_falls_back_to_recent_when_no_skill_match(
    auth, seeker, employer, company
):
    make_job(company, employer, title="Some Role")
    client = auth(seeker)
    r = client.get(SEEKER_DASH)
    # No skills set on the profile at all -- recommendations should not be
    # empty just because there's nothing to match against.
    assert len(r.data["recommended_jobs"]) == 1


@pytest.mark.django_db
def test_recommended_jobs_excludes_already_applied(auth, seeker, employer, company, resume_file):
    job = make_job(company, employer, title="Already Applied")
    apply(auth(seeker), job.id, resume_file)

    r = auth(seeker).get(SEEKER_DASH)
    titles = [j["title"] for j in r.data["recommended_jobs"]]
    assert "Already Applied" not in titles


# ---------------------------------------------------------------------------
# Employer dashboard
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_dashboard_empty_state(auth, employer):
    client = auth(employer)
    r = client.get(EMPLOYER_DASH)
    assert r.status_code == 200
    assert r.data["stats"]["total_jobs"] == 0
    assert r.data["charts"]["applications_per_job"] == []


@pytest.mark.django_db
def test_employer_dashboard_counts_jobs_by_status(auth, employer, company):
    make_job(company, employer, status="published")
    make_job(company, employer, status="published")
    make_job(company, employer, status="draft", published_at=None)

    r = auth(employer).get(EMPLOYER_DASH)
    assert r.data["stats"]["total_jobs"] == 3
    assert r.data["stats"]["active_jobs"] == 2


@pytest.mark.django_db
def test_employer_dashboard_isolated_by_company_membership(
    auth, employer, company, other_employer, other_company
):
    """
    Same attacker shape as every other object-level test since Phase 3:
    other_employer is a real employer, just not a member of THIS company.
    """
    make_job(company, employer)
    make_job(other_company, other_employer)

    r = auth(employer).get(EMPLOYER_DASH)
    assert r.data["stats"]["total_jobs"] == 1


@pytest.mark.django_db
def test_applications_per_job_chart_data(auth, employer, company, seeker, other_seeker, resume_file):
    job = make_job(company, employer, title="Popular Role")
    apply(auth(seeker), job.id, resume_file)
    apply(auth(other_seeker), job.id, resume_file)

    r = auth(employer).get(EMPLOYER_DASH)
    entry = next(e for e in r.data["charts"]["applications_per_job"] if e["job_id"] == job.id)
    assert entry["count"] == 2


@pytest.mark.django_db
def test_applications_per_job_excludes_withdrawn(auth, employer, company, seeker, resume_file):
    job = make_job(company, employer, title="Role")
    created = apply(auth(seeker), job.id, resume_file).data
    auth(seeker).post(f"/api/applications/{created['id']}/withdraw/")

    r = auth(employer).get(EMPLOYER_DASH)
    entry = next(e for e in r.data["charts"]["applications_per_job"] if e["job_id"] == job.id)
    assert entry["count"] == 0


@pytest.mark.django_db
def test_status_distribution_chart_data(auth, employer, company, seeker, resume_file):
    job = make_job(company, employer)
    created = apply(auth(seeker), job.id, resume_file).data
    auth(employer).patch(
        f"/api/applications/{created['id']}/status/", {"status": "shortlisted"}, format="json"
    )

    r = auth(employer).get(EMPLOYER_DASH)
    distribution = {e["status"]: e["count"] for e in r.data["charts"]["status_distribution"]}
    assert distribution["shortlisted"] == 1


@pytest.mark.django_db
def test_applications_over_time_chart_data(auth, employer, company, seeker, resume_file):
    job = make_job(company, employer)
    apply(auth(seeker), job.id, resume_file)

    r = auth(employer).get(EMPLOYER_DASH)
    series = r.data["charts"]["applications_over_time"]
    assert len(series) == 1
    assert series[0]["count"] == 1


@pytest.mark.django_db
def test_recently_posted_jobs_ordered_newest_first(auth, employer, company):
    import time

    make_job(company, employer, title="Older")
    time.sleep(0.01)
    make_job(company, employer, title="Newer")

    r = auth(employer).get(EMPLOYER_DASH)
    titles = [j["title"] for j in r.data["recently_posted_jobs"]]
    assert titles[0] == "Newer"
