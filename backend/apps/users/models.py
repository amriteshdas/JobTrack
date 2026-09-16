from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    JobTrack's user account.

    Why AbstractBaseUser instead of AbstractUser:
    AbstractUser ships a `username` field we do not want. We authenticate by
    email, so carrying a second unique identifier around means two things to
    keep in sync and a pointless NOT NULL column. AbstractBaseUser gives us
    the password/last_login machinery without the username baggage, and
    PermissionsMixin adds is_superuser/groups/permissions so Django admin
    still works normally.

    Why `role` lives on User and not in a separate table:
    A user is exactly one of seeker/employer for the life of the account,
    it is read on virtually every permission check, and it never grows past
    a handful of values. A CharField with choices is the cheapest correct
    model. Django Groups would also work but adds a join to answer a
    question we ask constantly.
    """

    class Role(models.TextChoices):
        JOB_SEEKER = "seeker", "Job Seeker"
        EMPLOYER = "employer", "Employer"

    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Used as the login identifier.",
    )
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        help_text="Set once at registration. Never editable through the API.",
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    # REQUIRED_FIELDS is what `createsuperuser` prompts for *in addition to*
    # USERNAME_FIELD and password. Role is excluded because the manager
    # defaults superusers to employer.
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_job_seeker(self):
        return self.role == self.Role.JOB_SEEKER

    @property
    def is_employer(self):
        return self.role == self.Role.EMPLOYER
