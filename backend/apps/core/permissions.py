from rest_framework.permissions import BasePermission


class IsJobSeeker(BasePermission):
    """
    Allows access only to authenticated users whose role is 'seeker'.

    Note this reads `request.user.role` -- the database-backed value on the
    authenticated user instance -- not the `role` claim baked into the JWT.
    That distinction matters: the claim reflects state at login time, the
    user object reflects state now.
    """

    message = "This action is only available to job seekers."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_job_seeker
        )


class IsEmployer(BasePermission):
    """
    Allows access only to authenticated users whose role is 'employer'.

    This is a ROLE check only. It answers "is this person an employer?",
    never "does this person own the specific job/company being touched?".
    Object ownership is a separate object-level check, added in Phase 3
    alongside the models it protects. Relying on a role check alone is
    exactly how one employer ends up able to edit another employer's jobs.
    """

    message = "This action is only available to employers."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_employer
        )


class IsCompanyMember(BasePermission):
    """
    Object-level check: is the requesting employer a member of the company
    that owns this object?

    This is the permission that actually protects the marketplace. IsEmployer
    answers "is this person an employer?" -- which every employer passes,
    including the one trying to edit a competitor's job posting. Role checks
    gate the ENDPOINT; this gates the ROW.

    DRF only calls has_object_permission() when the view calls
    get_object(). A custom action that fetches a row some other way
    (Model.objects.get(pk=...)) silently skips this check -- a genuinely
    common and serious bug. Views here either use get_object() or filter the
    queryset by membership so unauthorized rows are never reachable at all.
    """

    message = "You do not have access to this company."

    def _company_of(self, obj):
        # Works for both Company instances and anything with a .company FK
        # (Job today, Application later), so one class covers every
        # company-owned resource.
        return obj if obj.__class__.__name__ == "Company" else getattr(obj, "company", None)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated and user.is_employer):
            return False

        profile = getattr(user, "employer_profile", None)
        if profile is None:
            return False

        company = self._company_of(obj)
        if company is None:
            return False

        return company.memberships.filter(employer_profile=profile).exists()


class IsCompanyOwner(IsCompanyMember):
    """
    Stricter variant for managing membership itself. Any recruiter may post
    jobs; only an owner may add or remove colleagues, because that is the
    permission that grants all the others.
    """

    message = "Only a company owner can perform this action."

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated and user.is_employer):
            return False

        profile = getattr(user, "employer_profile", None)
        company = self._company_of(obj)
        if profile is None or company is None:
            return False

        return company.memberships.filter(
            employer_profile=profile, membership_role="owner"
        ).exists()
