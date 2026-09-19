from django.utils import timezone
from rest_framework import serializers

from apps.jobs.models import Job
from apps.jobs.serializers import JobSerializer

from .models import Application, SavedJob


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = ["id", "job", "created_at"]
        read_only_fields = fields


class ApplicantSerializer(serializers.Serializer):
    """
    Read-only view of the applicant as an employer should see them: name,
    contact, and whatever their seeker profile exposes. NOT a
    ModelSerializer on User -- that would need every User field
    read_only'd by hand, and it is easy to forget one (is_staff, say) and
    leak it. Building the exact shape we want from scratch is safer than
    subtracting from a shape we do not fully control.
    """

    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    headline = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    years_of_experience = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()

    def _profile(self, user):
        return getattr(user, "jobseeker_profile", None)

    def get_headline(self, user):
        profile = self._profile(user)
        return profile.headline if profile else ""

    def get_location(self, user):
        profile = self._profile(user)
        return profile.location if profile else ""

    def get_years_of_experience(self, user):
        profile = self._profile(user)
        return profile.years_of_experience if profile else 0

    def get_skills(self, user):
        profile = self._profile(user)
        return [s.name for s in profile.skills.all()] if profile else []


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Read shape used for BOTH "my applications" (seeker) and "applicants for
    this job" (employer) -- the same row, viewed by its two legitimate
    audiences. `job` is nested for the seeker's view; `applicant` is nested
    for the employer's view. Both are always present; the frontend simply
    uses whichever one is relevant to the page it's rendering.
    """

    job = JobSerializer(read_only=True)
    applicant = ApplicantSerializer(read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "job", "applicant", "resume", "cover_letter",
            "status", "applied_at", "updated_at",
        ]
        read_only_fields = fields


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/jobs/{id}/apply/

    `job` and `applicant` are NOT writable fields here -- both come from the
    URL and the authenticated user respectively, in the view, never from
    the request body. This is the same "don't trust a body-supplied FK"
    lesson as Job.company in Phase 3's JobWriteSerializer.
    """

    class Meta:
        model = Application
        fields = ["resume", "cover_letter"]

    def validate_resume(self, value):
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Resume must be under 5MB.")
        return value

    def to_representation(self, instance):
        return ApplicationSerializer(instance, context=self.context).data


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    """
    PATCH /api/applications/{id}/status/   body: {"status": "shortlisted"}

    A plain Serializer, not a ModelSerializer -- this endpoint changes
    exactly one field, and validating "is this transition allowed" needs
    the CURRENT status (on the instance) compared against the requested
    one, which is business logic that belongs here, not in a generic
    partial_update.
    """

    status = serializers.ChoiceField(choices=Application.Status.choices)

    def validate_status(self, value):
        if value not in Application.EMPLOYER_ALLOWED_STATUSES:
            raise serializers.ValidationError(
                "Employers cannot set this status. "
                f"Allowed: {', '.join(Application.EMPLOYER_ALLOWED_STATUSES)}."
            )
        return value

    def validate(self, attrs):
        instance = self.instance
        if instance.status == Application.Status.WITHDRAWN:
            raise serializers.ValidationError(
                "This application was withdrawn by the candidate and cannot be updated."
            )
        return attrs

    def save(self):
        self.instance.status = self.validated_data["status"]
        self.instance.save(update_fields=["status", "updated_at"])
        return self.instance
