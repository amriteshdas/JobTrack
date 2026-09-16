from django.db import models
from django.utils.text import slugify


class Company(models.Model):
    """
    An employer organisation. Jobs belong to a Company, never directly to a
    User -- if a recruiter leaves, their jobs must not leave with them.
    """

    class Size(models.TextChoices):
        MICRO = "1-10", "1-10 employees"
        SMALL = "11-50", "11-50 employees"
        MEDIUM = "51-200", "51-200 employees"
        LARGE = "201-1000", "201-1000 employees"
        ENTERPRISE = "1000+", "1000+ employees"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)

    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    website = models.URLField(blank=True)
    industry = models.CharField(max_length=120, blank=True, db_index=True)
    company_size = models.CharField(max_length=20, choices=Size.choices, blank=True)
    location = models.CharField(max_length=200, blank=True, db_index=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "companies"
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Slug gives us clean public URLs (/companies/acme-corp) without
        # exposing sequential integer IDs, which leak how many companies
        # exist and invite enumeration.
        if not self.slug:
            base = slugify(self.name)[:200] or "company"
            slug, n = base, 1
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        super().save(*args, **kwargs)


class CompanyMembership(models.Model):
    """
    Join table between employers and companies, as recommended in Phase 0.

    This is what makes "can this user edit this job?" answerable. Without it
    a Company would need a single owner FK, and the first time two recruiters
    from the same firm needed access we would be doing a data migration.

    `membership_role` distinguishes the person who can manage other members
    from an ordinary recruiter who can only manage jobs.
    """

    class MembershipRole(models.TextChoices):
        OWNER = "owner", "Owner"
        RECRUITER = "recruiter", "Recruiter"

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="memberships"
    )
    employer_profile = models.ForeignKey(
        "profiles.EmployerProfile",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    membership_role = models.CharField(
        max_length=20,
        choices=MembershipRole.choices,
        default=MembershipRole.RECRUITER,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "company_memberships"
        constraints = [
            # A person cannot be added to the same company twice. Enforced in
            # the DATABASE, not just the serializer, so a double-submitted
            # invite under concurrency still cannot create a duplicate row.
            models.UniqueConstraint(
                fields=["company", "employer_profile"],
                name="uniq_company_member",
            ),
        ]
        indexes = [
            # Every job/company write checks "is this user a member of this
            # company?". That lookup must be O(1), not a table scan.
            models.Index(
                fields=["employer_profile", "company"],
                name="idx_member_company",
            ),
        ]

    def __str__(self):
        return f"{self.employer_profile.user.email} @ {self.company.name}"
