import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.applications.models import Application
from apps.jobs.models import Job
from apps.profiles.models import Education, Experience


def apply_url(job_id):
    return f"/api/jobs/{job_id}/apply/"


def applicants_url(job_id):
    return f"/api/jobs/{job_id}/applicants/"


ME = "/api/profiles/seeker/me/"


def resume():
    return SimpleUploadedFile("resume.pdf", b"%PDF-1.4 fake resume", content_type="application/pdf")


# ---------------------------------------------------------------------------
# Expanded applicant profile visible to the employer
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_sees_full_applicant_profile(auth, seeker, employer, published_job):
    profile = seeker.jobseeker_profile
    profile.headline = "Backend Engineer, 3 YOE"
    profile.bio = "I like building APIs."
    profile.phone = "+91 90000 00000"
    profile.location = "Kolkata"
    profile.github_url = "https://github.com/sam"
    profile.linkedin_url = "https://linkedin.com/in/sam"
    profile.portfolio_url = "https://sam.dev"
    profile.expected_salary = 1200000
    profile.save()

    Education.objects.create(
        profile=profile, institution="IIT Kharagpur", degree="B.Tech",
        field_of_study="CS", start_date="2018-07-01", end_date="2022-05-01",
    )
    Experience.objects.create(
        profile=profile, company_name="Startup Inc", title="Backend Intern",
        start_date="2021-05-01", end_date="2021-08-01", description="Built things.",
    )

    seeker_client = auth(seeker)
    seeker_client.post(apply_url(published_job.id), {"resume": resume()}, format="multipart")

    client = auth(employer)
    r = client.get(applicants_url(published_job.id))
    applicant = r.data[0]["applicant"]

    assert applicant["headline"] == "Backend Engineer, 3 YOE"
    assert applicant["bio"] == "I like building APIs."
    assert applicant["phone"] == "+91 90000 00000"
    assert applicant["github_url"] == "https://github.com/sam"
    assert applicant["linkedin_url"] == "https://linkedin.com/in/sam"
    assert applicant["portfolio_url"] == "https://sam.dev"
    assert applicant["expected_salary"] == 1200000

    assert len(applicant["education"]) == 1
    assert applicant["education"][0]["institution"] == "IIT Kharagpur"

    assert len(applicant["experience"]) == 1
    assert applicant["experience"][0]["company_name"] == "Startup Inc"


@pytest.mark.django_db
def test_applicant_profile_still_excludes_sensitive_user_fields(
    auth, seeker, employer, published_job
):
    auth(seeker).post(apply_url(published_job.id), {"resume": resume()}, format="multipart")
    client = auth(employer)
    applicant = client.get(applicants_url(published_job.id)).data[0]["applicant"]

    assert "password" not in applicant
    assert "is_staff" not in applicant
    assert "is_superuser" not in applicant


@pytest.mark.django_db
def test_applicant_profile_photo_is_null_when_not_uploaded(auth, seeker, employer, published_job):
    auth(seeker).post(apply_url(published_job.id), {"resume": resume()}, format="multipart")
    client = auth(employer)
    applicant = client.get(applicants_url(published_job.id)).data[0]["applicant"]
    assert applicant["profile_photo"] is None


@pytest.mark.django_db
def test_applicant_list_query_count_does_not_scale_with_applicants(
    auth, employer, published_job
):
    """
    N+1 guard: education/experience/skills are all now nested per applicant,
    and JobSerializer nests company/skills too. Rather than assert an
    arbitrary ceiling, this proves the query count is roughly CONSTANT by
    comparing 3 applicants against 10 -- if any relation regresses to
    per-row fetching, this ratio stops being ~1 and the test fails,
    regardless of how many fixed-overhead queries (auth, permission
    checks) exist on top.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    def add_applicants(n):
        for i in range(n):
            u = User.objects.create_user(
                email=f"seeker{published_job.id}_{i}_{n}@example.com",
                password="StrongPass123!",
                role=User.Role.JOB_SEEKER,
            )
            Application.objects.create(
                job=published_job, applicant=u, resume=resume(), status=Application.Status.APPLIED,
            )

    client = auth(employer)

    add_applicants(3)
    with CaptureQueriesContext(connection) as ctx_small:
        r_small = client.get(applicants_url(published_job.id))
    assert len(r_small.data) == 3

    add_applicants(7)  # 10 total now
    with CaptureQueriesContext(connection) as ctx_large:
        r_large = client.get(applicants_url(published_job.id))
    assert len(r_large.data) == 10

    small_count = len(ctx_small.captured_queries)
    large_count = len(ctx_large.captured_queries)
    assert large_count <= small_count + 2, (
        f"Query count grew from {small_count} (3 applicants) to {large_count} "
        f"(10 applicants) -- looks like an N+1, not constant overhead."
    )


# ---------------------------------------------------------------------------
# Default resume on apply
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_apply_without_resume_uses_profile_resume(auth, seeker, published_job):
    profile = seeker.jobseeker_profile
    profile.resume.save("my_default_resume.pdf", resume(), save=True)

    client = auth(seeker)
    r = client.post(apply_url(published_job.id), {}, format="multipart")

    assert r.status_code == 201
    assert r.data["resume"] is not None
    assert "my_default_resume" in r.data["resume"]


@pytest.mark.django_db
def test_apply_without_resume_and_no_profile_resume_returns_400(auth, seeker, published_job):
    client = auth(seeker)
    r = client.post(apply_url(published_job.id), {}, format="multipart")
    assert r.status_code == 400
    assert "resume" in r.data


@pytest.mark.django_db
def test_apply_with_explicit_resume_overrides_profile_default(auth, seeker, published_job):
    profile = seeker.jobseeker_profile
    profile.resume.save("default_resume.pdf", resume(), save=True)

    client = auth(seeker)
    override = SimpleUploadedFile(
        "custom_for_this_job.pdf", b"%PDF-1.4 tailored resume", content_type="application/pdf"
    )
    r = client.post(apply_url(published_job.id), {"resume": override}, format="multipart")

    assert r.status_code == 201
    assert "custom_for_this_job" in r.data["resume"]
    assert "default_resume" not in r.data["resume"]


@pytest.mark.django_db
def test_default_resume_is_a_real_copy_not_a_live_reference(auth, seeker, published_job):
    """
    The whole point of snapshotting: replacing the profile resume AFTER
    applying must not change what the already-submitted application shows.
    """
    profile = seeker.jobseeker_profile
    profile.resume.save("original.pdf", resume(), save=True)

    client = auth(seeker)
    app_data = client.post(apply_url(published_job.id), {}, format="multipart").data

    # Now the seeker replaces their profile resume.
    profile.refresh_from_db()
    profile.resume.save("replacement.pdf", resume(), save=True)

    application = Application.objects.get(id=app_data["id"])
    assert "original" in application.resume.name
    assert application.resume.name != profile.resume.name


@pytest.mark.django_db
def test_two_applications_snapshot_independently(
    auth, seeker, employer, company, published_job
):
    """
    Applying to two different jobs with the "use my default" path must
    produce two independent files, not two Applications pointing at the
    same storage key (which would make deleting/replacing one profile
    resume corrupt a past application's file).
    """
    from django.utils import timezone

    profile = seeker.jobseeker_profile
    profile.resume.save("default.pdf", resume(), save=True)

    other_job = Job.objects.create(
        company=company, posted_by=employer.employer_profile, title="Second Role",
        description="d", location="K", work_mode=Job.WorkMode.REMOTE,
        employment_type=Job.EmploymentType.FULL_TIME, status=Job.Status.PUBLISHED,
        published_at=timezone.now(),
    )

    client = auth(seeker)
    a1 = client.post(apply_url(published_job.id), {}, format="multipart").data
    a2 = client.post(apply_url(other_job.id), {}, format="multipart").data

    app1 = Application.objects.get(id=a1["id"])
    app2 = Application.objects.get(id=a2["id"])
    assert app1.resume.name != app2.resume.name
