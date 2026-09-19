import pytest

from apps.applications.models import Application
from apps.jobs.models import Job
from apps.notifications.models import Notification


def apply_url(job_id):
    return f"/api/jobs/{job_id}/apply/"


def applicants_url(job_id):
    return f"/api/jobs/{job_id}/applicants/"


def status_url(app_id):
    return f"/api/applications/{app_id}/status/"


def withdraw_url(app_id):
    return f"/api/applications/{app_id}/withdraw/"


MINE = "/api/applications/mine/"
NOTIFICATIONS = "/api/notifications/"


# ---------------------------------------------------------------------------
# Applying
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_seeker_can_apply_to_published_job(auth, seeker, published_job, resume_file):
    client = auth(seeker)
    r = client.post(
        apply_url(published_job.id),
        {"resume": resume_file, "cover_letter": "I'd love this role."},
        format="multipart",
    )
    assert r.status_code == 201
    assert r.data["status"] == "applied"
    assert Application.objects.filter(job=published_job, applicant=seeker).exists()


@pytest.mark.django_db
def test_apply_requires_authentication(api_client, published_job, resume_file):
    r = api_client.post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    assert r.status_code == 401


@pytest.mark.django_db
def test_employer_cannot_apply(auth, employer, published_job, resume_file):
    client = auth(employer)
    r = client.post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    assert r.status_code == 403


@pytest.mark.django_db
def test_cannot_apply_twice(auth, seeker, published_job, resume_file):
    client = auth(seeker)
    client.post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    r = client.post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    assert r.status_code == 409
    assert Application.objects.filter(job=published_job, applicant=seeker).count() == 1


@pytest.mark.django_db
def test_cannot_apply_to_draft_job(auth, seeker, company, employer, resume_file):
    draft = Job.objects.create(
        company=company, posted_by=employer.employer_profile, title="Hidden",
        description="d", location="K", work_mode="remote", employment_type="full_time",
        status=Job.Status.DRAFT,
    )
    client = auth(seeker)
    r = client.post(apply_url(draft.id), {"resume": resume_file}, format="multipart")
    assert r.status_code == 404


@pytest.mark.django_db
def test_cannot_apply_to_closed_job(auth, seeker, closed_job, resume_file):
    client = auth(seeker)
    r = client.post(apply_url(closed_job.id), {"resume": resume_file}, format="multipart")
    assert r.status_code == 400


@pytest.mark.django_db
def test_cannot_apply_past_deadline(auth, seeker, company, employer, resume_file):
    from django.utils import timezone

    expired = Job.objects.create(
        company=company, posted_by=employer.employer_profile, title="Expired Role",
        description="d", location="K", work_mode="remote", employment_type="full_time",
        status=Job.Status.PUBLISHED, published_at=timezone.now(),
        application_deadline="2020-01-01",
    )
    client = auth(seeker)
    r = client.post(apply_url(expired.id), {"resume": resume_file}, format="multipart")
    assert r.status_code == 400


@pytest.mark.django_db
def test_apply_creates_notification_for_employer(auth, seeker, employer, published_job, resume_file):
    client = auth(seeker)
    client.post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    assert Notification.objects.filter(
        recipient=employer,
        notification_type=Notification.NotificationType.NEW_APPLICATION,
    ).exists()


@pytest.mark.django_db
def test_apply_resume_oversized_rejected(auth, seeker, published_job):
    from django.core.files.uploadedfile import SimpleUploadedFile

    big = SimpleUploadedFile("resume.pdf", b"x" * (6 * 1024 * 1024), content_type="application/pdf")
    client = auth(seeker)
    r = client.post(apply_url(published_job.id), {"resume": big}, format="multipart")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Tracking (seeker side)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_seeker_sees_own_applications(auth, seeker, published_job, resume_file):
    client = auth(seeker)
    client.post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    r = client.get(MINE)
    assert len(r.data) == 1
    assert r.data[0]["job"]["title"] == published_job.title


@pytest.mark.django_db
def test_seeker_does_not_see_others_applications(auth, seeker, other_seeker, published_job, resume_file):
    auth(other_seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(seeker)
    r = client.get(MINE)
    assert r.data == []


@pytest.mark.django_db
def test_withdraw_sets_status(auth, seeker, published_job, resume_file):
    client = auth(seeker)
    created = client.post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    r = client.post(withdraw_url(created.data["id"]))
    assert r.status_code == 200
    assert r.data["status"] == "withdrawn"


@pytest.mark.django_db
def test_cannot_withdraw_twice(auth, seeker, published_job, resume_file):
    client = auth(seeker)
    created = client.post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client.post(withdraw_url(created.data["id"]))
    r = client.post(withdraw_url(created.data["id"]))
    assert r.status_code == 409


@pytest.mark.django_db
def test_cannot_withdraw_someone_elses_application(auth, seeker, other_seeker, published_job, resume_file):
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(other_seeker)
    r = client.post(withdraw_url(created.data["id"]))
    assert r.status_code == 404
    assert Application.objects.get(id=created.data["id"]).status == "applied"


# ---------------------------------------------------------------------------
# Employer review
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_sees_applicants_for_own_job(auth, seeker, employer, published_job, resume_file):
    auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(employer)
    r = client.get(applicants_url(published_job.id))
    assert r.status_code == 200
    assert len(r.data) == 1
    assert r.data[0]["applicant"]["email"] == seeker.email


@pytest.mark.django_db
def test_applicant_shape_includes_profile_data_not_raw_user_fields(
    auth, seeker, employer, published_job, resume_file
):
    seeker.jobseeker_profile.headline = "Backend Engineer, 3 YOE"
    seeker.jobseeker_profile.save()

    auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(employer)
    r = client.get(applicants_url(published_job.id))
    applicant = r.data[0]["applicant"]

    assert applicant["headline"] == "Backend Engineer, 3 YOE"
    assert "password" not in applicant
    assert "is_staff" not in applicant


@pytest.mark.django_db
def test_other_employer_cannot_see_applicants(
    auth, seeker, other_employer, published_job, resume_file
):
    """
    other_employer is a real employer, just not a member of the company
    that owns this job -- exactly the Phase 3 attacker shape.
    """
    auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(other_employer)
    r = client.get(applicants_url(published_job.id))
    assert r.status_code == 404


@pytest.mark.django_db
def test_seeker_cannot_see_applicants_endpoint(auth, seeker, published_job):
    client = auth(seeker)
    r = client.get(applicants_url(published_job.id))
    assert r.status_code == 403


# ---------------------------------------------------------------------------
# Status changes
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_can_shortlist_applicant(auth, seeker, employer, published_job, resume_file):
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(employer)
    r = client.patch(status_url(created.data["id"]), {"status": "shortlisted"}, format="json")
    assert r.status_code == 200
    assert r.data["status"] == "shortlisted"


@pytest.mark.django_db
def test_status_change_notifies_applicant(auth, seeker, employer, published_job, resume_file):
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(employer)
    client.patch(status_url(created.data["id"]), {"status": "shortlisted"}, format="json")

    assert Notification.objects.filter(
        recipient=seeker,
        notification_type=Notification.NotificationType.APPLICATION_STATUS_CHANGED,
    ).exists()


@pytest.mark.django_db
def test_employer_cannot_set_status_to_withdrawn(auth, seeker, employer, published_job, resume_file):
    """WITHDRAWN is applicant-only, via the dedicated withdraw endpoint."""
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(employer)
    r = client.patch(status_url(created.data["id"]), {"status": "withdrawn"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_cannot_change_status_of_withdrawn_application(
    auth, seeker, employer, published_job, resume_file
):
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    auth(seeker).post(withdraw_url(created.data["id"]))

    client = auth(employer)
    r = client.patch(status_url(created.data["id"]), {"status": "shortlisted"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_other_employer_cannot_change_status(
    auth, seeker, other_employer, published_job, resume_file
):
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(other_employer)
    r = client.patch(status_url(created.data["id"]), {"status": "shortlisted"}, format="json")
    assert r.status_code == 404


@pytest.mark.django_db
def test_seeker_cannot_change_own_application_status(auth, seeker, published_job, resume_file):
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(seeker)
    r = client.patch(status_url(created.data["id"]), {"status": "selected"}, format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_invalid_status_value_rejected(auth, seeker, employer, published_job, resume_file):
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(employer)
    r = client.patch(status_url(created.data["id"]), {"status": "made_up_status"}, format="json")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_notifications_scoped_to_recipient(auth, seeker, other_seeker, employer, published_job, resume_file):
    auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    client = auth(other_seeker)
    r = client.get(NOTIFICATIONS)
    assert r.data == []


@pytest.mark.django_db
def test_mark_notification_read(auth, seeker, employer, published_job, resume_file):
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    auth(employer).patch(status_url(created.data["id"]), {"status": "shortlisted"}, format="json")

    client = auth(seeker)
    notif = client.get(NOTIFICATIONS).data[0]
    assert notif["is_read"] is False

    r = client.patch(f"{NOTIFICATIONS}{notif['id']}/read/")
    assert r.status_code == 200
    assert r.data["is_read"] is True


@pytest.mark.django_db
def test_cannot_mark_another_users_notification_read(
    auth, seeker, other_seeker, employer, published_job, resume_file
):
    created = auth(seeker).post(apply_url(published_job.id), {"resume": resume_file}, format="multipart")
    auth(employer).patch(status_url(created.data["id"]), {"status": "shortlisted"}, format="json")
    notif_id = auth(seeker).get(NOTIFICATIONS).data[0]["id"]

    client = auth(other_seeker)
    r = client.patch(f"{NOTIFICATIONS}{notif_id}/read/")
    assert r.status_code == 404
