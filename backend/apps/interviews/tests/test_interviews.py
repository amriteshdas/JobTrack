import pytest
from datetime import timedelta

from apps.applications.models import Application
from apps.interviews.models import Interview
from apps.notifications.models import Notification


def schedule_url(app_id):
    return f"/api/applications/{app_id}/interviews/"


def detail_url(interview_id):
    return f"/api/interviews/{interview_id}/"


MINE = "/api/interviews/mine/"


def future_time(**kwargs):
    from django.utils import timezone

    return (timezone.now() + timedelta(**kwargs)).isoformat()


def video_payload(**overrides):
    payload = {
        "interview_type": "video",
        "scheduled_at": future_time(days=3),
        "meeting_link": "https://meet.example.com/abc",
        "notes": "Technical round",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_can_schedule_interview(auth, employer, application):
    client = auth(employer)
    r = client.post(schedule_url(application.id), video_payload(), format="json")
    assert r.status_code == 201
    assert r.data["interview_type"] == "video"
    assert r.data["status"] == "scheduled"


@pytest.mark.django_db
def test_scheduling_interview_advances_application_status(auth, employer, application):
    assert application.status == Application.Status.APPLIED
    client = auth(employer)
    client.post(schedule_url(application.id), video_payload(), format="json")

    application.refresh_from_db()
    assert application.status == Application.Status.INTERVIEW


@pytest.mark.django_db
def test_scheduling_does_not_regress_a_further_along_application(auth, employer, application):
    """If the application is already SELECTED, scheduling a follow-up round shouldn't demote it."""
    auth(employer).patch(
        f"/api/applications/{application.id}/status/", {"status": "selected"}, format="json"
    )
    client = auth(employer)
    client.post(schedule_url(application.id), video_payload(), format="json")

    application.refresh_from_db()
    assert application.status == Application.Status.SELECTED


@pytest.mark.django_db
def test_scheduling_creates_notification_for_applicant(auth, employer, seeker, application):
    client = auth(employer)
    client.post(schedule_url(application.id), video_payload(), format="json")
    assert Notification.objects.filter(
        recipient=seeker,
        notification_type=Notification.NotificationType.APPLICATION_STATUS_CHANGED,
        title="Interview scheduled",
    ).exists()


@pytest.mark.django_db
def test_colleague_at_same_company_can_also_schedule(auth, colleague, application):
    """scheduled_by is an audit trail, not an ownership gate -- any company member may act."""
    client = auth(colleague)
    r = client.post(schedule_url(application.id), video_payload(), format="json")
    assert r.status_code == 201


@pytest.mark.django_db
def test_other_employer_cannot_schedule(auth, other_employer, application):
    client = auth(other_employer)
    r = client.post(schedule_url(application.id), video_payload(), format="json")
    assert r.status_code == 404


@pytest.mark.django_db
def test_seeker_cannot_schedule_own_interview(auth, seeker, application):
    client = auth(seeker)
    r = client.post(schedule_url(application.id), video_payload(), format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_cannot_schedule_interview_for_withdrawn_application(auth, employer, seeker, application):
    auth(seeker).post(f"/api/applications/{application.id}/withdraw/")
    client = auth(employer)
    r = client.post(schedule_url(application.id), video_payload(), format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_cannot_schedule_in_the_past(auth, employer, application):
    client = auth(employer)
    r = client.post(
        schedule_url(application.id),
        video_payload(scheduled_at=future_time(days=-1)),
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_must_provide_meeting_link_or_location(auth, employer, application):
    client = auth(employer)
    r = client.post(
        schedule_url(application.id),
        {"interview_type": "video", "scheduled_at": future_time(days=3)},
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_onsite_interview_accepts_location_instead_of_link(auth, employer, application):
    client = auth(employer)
    r = client.post(
        schedule_url(application.id),
        {"interview_type": "onsite", "scheduled_at": future_time(days=3), "location": "Acme HQ, Kolkata"},
        format="json",
    )
    assert r.status_code == 201


@pytest.mark.django_db
def test_multiple_interview_rounds_allowed_per_application(auth, employer, application):
    """Interview is 1:many against Application by design -- phone screen, then onsite."""
    client = auth(employer)
    client.post(schedule_url(application.id), video_payload(interview_type="phone"), format="json")
    client.post(schedule_url(application.id), video_payload(interview_type="onsite", location="HQ"), format="json")
    assert Interview.objects.filter(application=application).count() == 2


# ---------------------------------------------------------------------------
# Viewing (mine)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_seeker_sees_own_interview(auth, employer, seeker, application):
    auth(employer).post(schedule_url(application.id), video_payload(), format="json")
    r = auth(seeker).get(MINE)
    assert len(r.data) == 1
    assert r.data[0]["job_title"] == application.job.title


@pytest.mark.django_db
def test_seeker_does_not_see_other_seekers_interviews(
    auth, employer, seeker, other_seeker, published_job, resume_file
):
    other_app = auth(other_seeker).post(
        f"/api/jobs/{published_job.id}/apply/", {"resume": resume_file()}, format="multipart"
    ).data
    auth(employer).post(schedule_url(other_app["id"]), video_payload(), format="json")

    r = auth(seeker).get(MINE)
    assert r.data == []


@pytest.mark.django_db
def test_employer_sees_interviews_across_own_companys_jobs(auth, employer, application):
    auth(employer).post(schedule_url(application.id), video_payload(), format="json")
    r = auth(employer).get(MINE)
    assert len(r.data) == 1


@pytest.mark.django_db
def test_colleague_also_sees_interview_they_did_not_personally_schedule(
    auth, employer, colleague, application
):
    auth(employer).post(schedule_url(application.id), video_payload(), format="json")
    r = auth(colleague).get(MINE)
    assert len(r.data) == 1


@pytest.mark.django_db
def test_other_employer_does_not_see_this_companys_interviews(
    auth, employer, other_employer, application
):
    auth(employer).post(schedule_url(application.id), video_payload(), format="json")
    r = auth(other_employer).get(MINE)
    assert r.data == []


# ---------------------------------------------------------------------------
# Updating (reschedule / cancel / complete)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_employer_can_reschedule(auth, employer, application):
    created = auth(employer).post(schedule_url(application.id), video_payload(), format="json").data
    new_time = future_time(days=10)
    r = auth(employer).patch(detail_url(created["id"]), {"scheduled_at": new_time}, format="json")
    assert r.status_code == 200
    assert r.data["scheduled_at"].startswith(new_time[:16])


@pytest.mark.django_db
def test_employer_can_cancel(auth, employer, application):
    created = auth(employer).post(schedule_url(application.id), video_payload(), format="json").data
    r = auth(employer).patch(detail_url(created["id"]), {"status": "cancelled"}, format="json")
    assert r.status_code == 200
    assert r.data["status"] == "cancelled"


@pytest.mark.django_db
def test_employer_can_mark_completed(auth, employer, application):
    created = auth(employer).post(schedule_url(application.id), video_payload(), format="json").data
    r = auth(employer).patch(detail_url(created["id"]), {"status": "completed"}, format="json")
    assert r.status_code == 200
    assert r.data["status"] == "completed"


@pytest.mark.django_db
def test_colleague_can_also_reschedule(auth, employer, colleague, application):
    created = auth(employer).post(schedule_url(application.id), video_payload(), format="json").data
    r = auth(colleague).patch(detail_url(created["id"]), {"status": "cancelled"}, format="json")
    assert r.status_code == 200


@pytest.mark.django_db
def test_other_employer_cannot_update_interview(auth, employer, other_employer, application):
    created = auth(employer).post(schedule_url(application.id), video_payload(), format="json").data
    r = auth(other_employer).patch(detail_url(created["id"]), {"status": "cancelled"}, format="json")
    assert r.status_code == 404


@pytest.mark.django_db
def test_seeker_cannot_update_interview(auth, employer, seeker, application):
    created = auth(employer).post(schedule_url(application.id), video_payload(), format="json").data
    r = auth(seeker).patch(detail_url(created["id"]), {"status": "cancelled"}, format="json")
    assert r.status_code == 403


@pytest.mark.django_db
def test_clearing_both_link_and_location_is_rejected(auth, employer, application):
    created = auth(employer).post(schedule_url(application.id), video_payload(), format="json").data
    r = auth(employer).patch(detail_url(created["id"]), {"meeting_link": ""}, format="json")
    assert r.status_code == 400
