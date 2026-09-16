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
