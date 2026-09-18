import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.profiles.models import Education, Experience, JobSeekerProfile

ME = "/api/profiles/seeker/me/"
SKILLS = "/api/profiles/seeker/me/skills/"
EDUCATION = "/api/profiles/seeker/me/education/"
EXPERIENCE = "/api/profiles/seeker/me/experience/"


# ---------------------------------------------------------------------------
# Auto-creation on registration
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_seeker_gets_profile_on_registration(api_client):
    api_client.post(
        "/api/auth/register/",
        {
            "email": "new@seeker.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "role": "seeker",
        },
        format="json",
    )
    from django.contrib.auth import get_user_model

    user = get_user_model().objects.get(email="new@seeker.com")
    assert hasattr(user, "jobseeker_profile")


@pytest.mark.django_db
def test_employer_does_not_get_seeker_profile(employer):
    assert not hasattr(employer, "jobseeker_profile")


@pytest.mark.django_db
def test_employer_cannot_access_seeker_profile_endpoint(auth, employer):
    client = auth(employer)
    assert client.get(ME).status_code == 403


@pytest.mark.django_db
def test_anonymous_cannot_access_seeker_profile(api_client):
    assert api_client.get(ME).status_code == 401


# ---------------------------------------------------------------------------
# Profile read/update
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_seeker_can_read_own_profile(auth, seeker_a):
    client = auth(seeker_a)
    r = client.get(ME)
    assert r.status_code == 200
    assert r.data["email"] == seeker_a.email
    assert r.data["skills"] == []
    assert r.data["education"] == []
    assert r.data["experience"] == []


@pytest.mark.django_db
def test_seeker_can_update_own_profile(auth, seeker_a):
    client = auth(seeker_a)
    r = client.patch(
        ME,
        {"headline": "Backend Engineer, 3 YOE", "location": "Kolkata", "years_of_experience": 3},
        format="json",
    )
    assert r.status_code == 200
    assert r.data["headline"] == "Backend Engineer, 3 YOE"

    profile = JobSeekerProfile.objects.get(user=seeker_a)
    assert profile.years_of_experience == 3


@pytest.mark.django_db
def test_profile_update_rejects_negative_salary(auth, seeker_a):
    client = auth(seeker_a)
    r = client.patch(ME, {"expected_salary": -5000}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_update_response_includes_nested_data(auth, seeker_a):
    """
    A write returns the full read shape (with nested skills/education),
    not just the fields that were patched -- so the frontend doesn't need a
    second request to resync.
    """
    client = auth(seeker_a)
    r = client.patch(ME, {"headline": "X"}, format="json")
    assert "skills" in r.data
    assert "education" in r.data
    assert "experience" in r.data


@pytest.mark.django_db
def test_resume_upload_accepts_pdf(auth, seeker_a):
    client = auth(seeker_a)
    resume = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 fake content", content_type="application/pdf")
    r = client.patch(ME, {"resume": resume}, format="multipart")
    assert r.status_code == 200
    assert r.data["resume"] is not None


@pytest.mark.django_db
def test_resume_upload_rejects_bad_extension(auth, seeker_a):
    client = auth(seeker_a)
    bad_file = SimpleUploadedFile("resume.exe", b"not a resume", content_type="application/octet-stream")
    r = client.patch(ME, {"resume": bad_file}, format="multipart")
    assert r.status_code == 400


@pytest.mark.django_db
def test_resume_upload_rejects_oversized_file(auth, seeker_a):
    client = auth(seeker_a)
    big_file = SimpleUploadedFile("resume.pdf", b"x" * (6 * 1024 * 1024), content_type="application/pdf")
    r = client.patch(ME, {"resume": big_file}, format="multipart")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_setting_skills_replaces_full_list(auth, seeker_a):
    client = auth(seeker_a)
    client.put(SKILLS, {"skills": ["Python", "Django"]}, format="json")
    r = client.put(SKILLS, {"skills": ["React"]}, format="json")
    names = {s["name"] for s in r.data["skills"]}
    assert names == {"React"}


@pytest.mark.django_db
def test_skills_reuse_existing_case_insensitively(auth, seeker_a, published_job):
    """
    Skill is the SAME table Job.skills uses (Phase 3). Setting "python" on a
    profile must join the existing "Python" row from a job posting, not
    create a duplicate -- this is what makes matching profiles against job
    requirements meaningful later.
    """
    from apps.jobs.models import Skill

    Skill.objects.create(name="Python")
    client = auth(seeker_a)
    client.put(SKILLS, {"skills": ["python"]}, format="json")
    assert Skill.objects.filter(name__iexact="python").count() == 1


@pytest.mark.django_db
def test_employer_cannot_set_seeker_skills(auth, employer):
    client = auth(employer)
    assert client.put(SKILLS, {"skills": ["Python"]}, format="json").status_code == 403


# ---------------------------------------------------------------------------
# Education -- ownership scoping
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_seeker_can_create_education_entry(auth, seeker_a):
    client = auth(seeker_a)
    r = client.post(
        EDUCATION,
        {"institution": "IIT Kharagpur", "degree": "B.Tech", "start_date": "2018-07-01", "end_date": "2022-05-01"},
        format="json",
    )
    assert r.status_code == 201
    assert Education.objects.get().profile.user == seeker_a


@pytest.mark.django_db
def test_education_end_before_start_rejected(auth, seeker_a):
    client = auth(seeker_a)
    r = client.post(
        EDUCATION,
        {"institution": "X", "degree": "Y", "start_date": "2022-01-01", "end_date": "2020-01-01"},
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_seeker_only_sees_own_education(auth, seeker_a, seeker_b):
    Education.objects.create(
        profile=seeker_b.jobseeker_profile, institution="Other Uni", degree="B.A.", start_date="2018-01-01"
    )
    client = auth(seeker_a)
    r = client.get(EDUCATION)
    assert r.data["results"] == []


@pytest.mark.django_db
def test_seeker_cannot_edit_another_seekers_education(auth, seeker_a, seeker_b):
    """
    Object-level isolation, same principle as Job ownership in Phase 3: the
    row is scoped out of the QUERYSET, so it 404s rather than 403s -- it is
    not merely forbidden to edit, it does not exist from this seeker's view.
    """
    entry = Education.objects.create(
        profile=seeker_b.jobseeker_profile, institution="Other Uni", degree="B.A.", start_date="2018-01-01"
    )
    client = auth(seeker_a)
    r = client.patch(f"{EDUCATION}{entry.id}/", {"degree": "Hijacked"}, format="json")
    assert r.status_code == 404


@pytest.mark.django_db
def test_seeker_can_delete_own_education(auth, seeker_a):
    client = auth(seeker_a)
    created = client.post(
        EDUCATION,
        {"institution": "IIT", "degree": "B.Tech", "start_date": "2018-01-01"},
        format="json",
    )
    r = client.delete(f"{EDUCATION}{created.data['id']}/")
    assert r.status_code == 204
    assert Education.objects.count() == 0


# ---------------------------------------------------------------------------
# Experience -- same pattern, lighter coverage
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_seeker_can_create_experience_entry(auth, seeker_a):
    client = auth(seeker_a)
    r = client.post(
        EXPERIENCE,
        {"company_name": "Acme", "title": "SWE", "start_date": "2022-01-01"},
        format="json",
    )
    assert r.status_code == 201
    assert r.data["is_current"] is True


@pytest.mark.django_db
def test_seeker_cannot_edit_another_seekers_experience(auth, seeker_a, seeker_b):
    entry = Experience.objects.create(
        profile=seeker_b.jobseeker_profile, company_name="X", title="Y", start_date="2020-01-01"
    )
    client = auth(seeker_a)
    r = client.delete(f"{EXPERIENCE}{entry.id}/")
    assert r.status_code == 404
    assert Experience.objects.filter(id=entry.id).exists()
