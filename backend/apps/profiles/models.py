from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


class EmployerProfile(models.Model):
    """
    The recruiter-as-a-person record, kept separate from Company.

    Why not just put `designation` and `phone` on User?
    Because those fields are meaningless for job seekers. Putting
    role-specific fields on a shared User table gives you a wide table full
    of NULLs where half the columns are invalid for half the rows, and no
    way to enforce "employers must have a designation" at the DB level.
    A 1:1 profile per role keeps each table internally coherent.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employer_profile",
    )
    designation = models.CharField(
        max_length=150,
        blank=True,
        help_text="e.g. 'Head of Talent', 'Technical Recruiter'.",
    )
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "employer_profiles"

    def __str__(self):
        return f"EmployerProfile<{self.user.email}>"


def resume_upload_path(instance, filename):
    # Namespaced by user id so two candidates uploading "resume.pdf" on the
    # same day never collide, and so a leaked URL from one candidate cannot
    # be guessed by incrementing another candidate's.
    return f"resumes/user_{instance.user_id}/{filename}"


def profile_photo_upload_path(instance, filename):
    return f"profile_photos/user_{instance.user_id}/{filename}"


class JobSeekerProfile(models.Model):
    """
    The candidate-facing profile shown to employers reviewing an application.

    Skills are a ManyToManyField to the same normalized Skill table Job
    uses (Phase 3) -- this is precisely why Skill was pulled into its own
    table back then rather than left as a string field on Job: it is now
    reused, unmodified, as the shared vocabulary for both job requirements
    and candidate skills, which is what makes matching one against the
    other (Phase 10, AI matching) possible at all.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="jobseeker_profile",
    )

    headline = models.CharField(
        max_length=200, blank=True, help_text="e.g. 'Backend Engineer, 3 YOE'."
    )
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True, db_index=True)

    profile_photo = models.ImageField(
        upload_to=profile_photo_upload_path, blank=True, null=True
    )
    resume = models.FileField(
        upload_to=resume_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])],
        help_text="PDF or Word document, max 5MB (enforced in the serializer).",
    )

    years_of_experience = models.PositiveIntegerField(default=0)
    expected_salary = models.PositiveIntegerField(blank=True, null=True)

    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    skills = models.ManyToManyField("jobs.Skill", related_name="jobseekers", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jobseeker_profiles"

    def __str__(self):
        return f"JobSeekerProfile<{self.user.email}>"


class Education(models.Model):
    profile = models.ForeignKey(
        JobSeekerProfile, on_delete=models.CASCADE, related_name="education"
    )
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=150)
    field_of_study = models.CharField(max_length=150, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(
        blank=True, null=True, help_text="Leave blank if currently studying."
    )

    class Meta:
        db_table = "education_entries"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.degree} @ {self.institution}"

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})


class Experience(models.Model):
    profile = models.ForeignKey(
        JobSeekerProfile, on_delete=models.CASCADE, related_name="experience"
    )
    company_name = models.CharField(max_length=200)
    title = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField(
        blank=True, null=True, help_text="Leave blank if this is the current role."
    )
    description = models.TextField(blank=True)

    class Meta:
        db_table = "experience_entries"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.title} @ {self.company_name}"

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

    @property
    def is_current(self):
        return self.end_date is None
