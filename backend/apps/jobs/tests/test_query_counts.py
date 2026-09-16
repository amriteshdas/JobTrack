import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.jobs.models import Job, Skill


@pytest.mark.django_db
def test_job_list_does_not_scale_queries_with_result_count(
    api_client, company_a, employer_a
):
    """
    Guards against N+1 regressions.

    Without select_related("company") and prefetch_related("skills"),
    serializing 20 jobs would fire roughly 40 extra queries -- one per job
    for the company, one per job for its skills. This test fails loudly if
    someone later removes those calls.

    Asserting an absolute ceiling rather than an exact number keeps the test
    from breaking every time an unrelated middleware query is added.
    """
    skills = [Skill.objects.create(name=f"Skill{i}") for i in range(3)]
    for i in range(20):
        job = Job.objects.create(
            company=company_a,
            posted_by=employer_a.employer_profile,
            title=f"Job {i}",
            description="d",
            location="Kolkata",
            work_mode=Job.WorkMode.REMOTE,
            employment_type=Job.EmploymentType.FULL_TIME,
            status=Job.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        job.skills.set(skills)

    with CaptureQueriesContext(connection) as ctx:
        response = api_client.get("/api/jobs/")

    assert response.status_code == 200
    assert len(response.data["results"]) == 20
    assert len(ctx.captured_queries) <= 5, (
        f"Expected a constant number of queries, got {len(ctx.captured_queries)} "
        "- select_related/prefetch_related likely removed."
    )
