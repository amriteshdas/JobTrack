from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.applications.models import Application

MINE = "/api/interviews/mine/"


def schedule_url(app_id):
    return f"/api/applications/{app_id}/interviews/"


@pytest.mark.django_db
def test_employer_interviews_mine_query_count_is_constant(
    auth, employer, company, published_job
):
    """
    GET /interviews/mine/ (employer branch) nests job title, company name,
    and applicant name/email per interview. Proved constant the same way
    as the other query-count tests: 3 interviews vs 10, not an arbitrary
    ceiling.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    client = auth(employer)

    def add_interviews(n, start):
        for i in range(start, start + n):
            seeker = User.objects.create_user(
                email=f"seeker{i}@example.com", password="StrongPass123!", role=User.Role.JOB_SEEKER
            )
            app = Application.objects.create(
                job=published_job,
                applicant=seeker,
                resume="resumes/fake.pdf",
                status=Application.Status.APPLIED,
            )
            client.post(
                schedule_url(app.id),
                {
                    "interview_type": "video",
                    "scheduled_at": (timezone.now() + timedelta(days=3)).isoformat(),
                    "meeting_link": "https://meet.example.com/x",
                },
                format="json",
            )

    add_interviews(3, 0)
    with CaptureQueriesContext(connection) as ctx_small:
        r_small = client.get(MINE)
    assert len(r_small.data) == 3

    add_interviews(7, 3)
    with CaptureQueriesContext(connection) as ctx_large:
        r_large = client.get(MINE)
    assert len(r_large.data) == 10

    assert len(ctx_large.captured_queries) <= len(ctx_small.captured_queries) + 2, (
        f"Query count grew from {len(ctx_small.captured_queries)} (3 interviews) to "
        f"{len(ctx_large.captured_queries)} (10 interviews) -- looks like an N+1."
    )
