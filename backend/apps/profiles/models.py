from django.conf import settings
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

    JobSeekerProfile is deliberately NOT here yet -- that is Phase 5.
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
