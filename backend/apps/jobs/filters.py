import django_filters
from django.utils import timezone

from .models import Job


class JobFilter(django_filters.FilterSet):
    """
    Backs GET /api/jobs/?location=...&work_mode=...&salary_min=...

    Deliberately one FilterSet, not one endpoint per filter (the Phase 0 API
    design called this out explicitly). Adding a new filterable field later
    is a one-line addition here, not a new URL, a new view, and a new
    frontend service call.

    Every field here is either an exact match against an indexed/choice
    column (cheap) or a range comparison against a numeric column (still
    cheap with the right index). Free-text search on `description` is
    handled separately by DRF's SearchFilter, not here -- see the note on
    SearchFilter in views.py about why that is NOT the same as full-text
    search.
    """

    location = django_filters.CharFilter(lookup_expr="icontains")

    # ChoiceFilter (not CharFilter) means an invalid value like
    # ?work_mode=banana is rejected with a clear 400 instead of silently
    # matching nothing, which is what a plain exact-match CharFilter would do.
    work_mode = django_filters.ChoiceFilter(choices=Job.WorkMode.choices)
    employment_type = django_filters.ChoiceFilter(choices=Job.EmploymentType.choices)

    experience_min = django_filters.NumberFilter(
        field_name="experience_required", lookup_expr="gte",
        help_text="Jobs requiring at least this many years.",
    )
    experience_max = django_filters.NumberFilter(
        field_name="experience_required", lookup_expr="lte",
    )

    # A job "matches" a salary range if the ranges overlap, not if the job's
    # minimum happens to exceed the searched minimum -- a job paying
    # 40k-90k should show up for a search of "at least 60k" even though its
    # own salary_min (40k) is below 60k.
    salary_min = django_filters.NumberFilter(
        field_name="salary_max", lookup_expr="gte",
        help_text="Jobs whose range reaches at least this amount.",
    )
    salary_max = django_filters.NumberFilter(
        field_name="salary_min", lookup_expr="lte",
        help_text="Jobs whose range starts at or below this amount.",
    )

    company = django_filters.CharFilter(field_name="company__slug")

    skill = django_filters.CharFilter(
        field_name="skills__name", lookup_expr="iexact",
        help_text="Exact skill name, e.g. ?skill=Python.",
    )

    posted_after = django_filters.DateFilter(
        field_name="published_at", lookup_expr="gte",
    )

    class Meta:
        model = Job
        fields = [
            "location", "work_mode", "employment_type",
            "experience_min", "experience_max",
            "salary_min", "salary_max",
            "company", "skill", "posted_after",
        ]
