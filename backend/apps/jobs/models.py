from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Skill(models.Model):
    """
    Normalized skills, shared between jobs and (from Phase 5) job seekers.

    Why not a comma-separated CharField on Job:
    string skills drift instantly -- "Python", "python", "python3", "Pyton"
    all become distinct values, so "find jobs requiring Python" silently
    misses results and a skills filter is impossible to build correctly.
    A lookup table makes the filter a join instead of a LIKE scan.
    """

    name = models.CharField(max_length=80, unique=True, db_index=True)
    slug = models.SlugField(max_length=90, unique=True)

    class Meta:
        db_table = "skills"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Canonicalize on the way in so "  pyThon " and "Python" converge.
        self.name = self.name.strip()
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Job(models.Model):
    class WorkMode(models.TextChoices):
        REMOTE = "remote", "Remote"
        HYBRID = "hybrid", "Hybrid"
        ONSITE = "onsite", "On-site"

    class EmploymentType(models.TextChoices):
        FULL_TIME = "full_time", "Full-time"
        PART_TIME = "part_time", "Part-time"
        INTERNSHIP = "internship", "Internship"
        CONTRACT = "contract", "Contract"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        CLOSED = "closed", "Closed"

    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="jobs"
    )
    # Audit trail: which recruiter created this. PROTECT rather than CASCADE
    # because deleting a recruiter must never silently delete the company's
    # job postings and their attached applications.
    posted_by = models.ForeignKey(
        "profiles.EmployerProfile",
        on_delete=models.PROTECT,
        related_name="posted_jobs",
    )

    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    responsibilities = models.TextField(blank=True)
    qualifications = models.TextField(blank=True)
    benefits = models.TextField(blank=True)

    location = models.CharField(max_length=200, db_index=True)
    work_mode = models.CharField(max_length=20, choices=WorkMode.choices)
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    experience_required = models.PositiveIntegerField(
        default=0, help_text="Minimum years of experience."
    )

    salary_min = models.PositiveIntegerField(blank=True, null=True)
    salary_max = models.PositiveIntegerField(blank=True, null=True)

    skills = models.ManyToManyField(Skill, related_name="jobs", blank=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    application_deadline = models.DateField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jobs"
        ordering = ["-created_at"]
        constraints = [
            # A check constraint, not just serializer validation. Serializers
            # protect the API; a check constraint protects the DATA -- from
            # the admin, a shell, a management command, or a future endpoint
            # someone forgets to validate.
            models.CheckConstraint(
                condition=models.Q(salary_max__gte=models.F("salary_min"))
                | models.Q(salary_min__isnull=True)
                | models.Q(salary_max__isnull=True),
                name="salary_max_gte_min",
            ),
        ]
        indexes = [
            # THE index for this project. The public job board always filters
            # status='published' and sorts by recency; this composite serves
            # both the WHERE and the ORDER BY from one structure, so Postgres
            # never sorts the result set at query time.
            models.Index(fields=["status", "-published_at"], name="idx_job_status_pub"),
            # Supports "show me my company's jobs" on the employer dashboard.
            models.Index(fields=["company", "status"], name="idx_job_company_status"),
        ]

    def __str__(self):
        return f"{self.title} @ {self.company.name}"

    def clean(self):
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValidationError({"salary_max": "Maximum salary cannot be below the minimum."})

    @property
    def is_open(self):
        """Published and not past its deadline -- the condition for applying."""
        if self.status != self.Status.PUBLISHED:
            return False
        if self.application_deadline and self.application_deadline < timezone.now().date():
            return False
        return True
