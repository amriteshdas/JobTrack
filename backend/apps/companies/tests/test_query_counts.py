import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.jobs.models import Job, Skill


@pytest.mark.django_db
def test_company_jobs_endpoint_query_count_is_constant(api_client, company, employer):
    """
    GET /companies/{slug}/jobs/ nests skills per job (see the view's
    select_related/prefetch_related). Proved constant the same way as
    Phase 4's job-list test: compare 3 vs 10 jobs rather than assert an
    arbitrary ceiling, so a real regression can't hide behind a threshold
    picked too loosely.
    """
    counter = {"n": 0}

    def add_jobs(n):
        for _ in range(n):
            i = counter["n"]
            counter["n"] += 1
            job = Job.objects.create(
                company=company, posted_by=employer.employer_profile,
                title=f"Job {i}", description="d", location="K",
                work_mode=Job.WorkMode.REMOTE, employment_type=Job.EmploymentType.FULL_TIME,
                status=Job.Status.PUBLISHED, published_at=timezone.now(),
            )
            job.skills.add(Skill.objects.create(name=f"Skill{company.id}-{i}"))

    add_jobs(3)
    with CaptureQueriesContext(connection) as ctx_small:
        r_small = api_client.get(f"/api/companies/{company.slug}/jobs/")
    assert r_small.data["count"] == 3

    add_jobs(7)
    with CaptureQueriesContext(connection) as ctx_large:
        r_large = api_client.get(f"/api/companies/{company.slug}/jobs/")
    assert r_large.data["count"] == 10

    assert len(ctx_large.captured_queries) <= len(ctx_small.captured_queries) + 2, (
        f"Query count grew from {len(ctx_small.captured_queries)} (3 jobs) to "
        f"{len(ctx_large.captured_queries)} (10 jobs) -- looks like an N+1."
    )
