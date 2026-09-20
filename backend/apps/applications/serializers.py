from django.utils import timezone
from rest_framework import serializers

from apps.jobs.models import Job
from apps.jobs.serializers import JobSerializer
from apps.profiles.serializers import EducationSerializer, ExperienceSerializer

from .models import Application, SavedJob


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = ["id", "job", "created_at"]
        read_only_fields = fields


class ApplicantSerializer(serializers.Serializer):
    """
    The FULL candidate profile as an employer reviewing an application
    should see it: contact info, photo, links, bio, skills, and complete
    education/experience history -- not just the headline summary this
    serializer used to return. This is deliberately everything a hiring
    decision would actually need, in one response, rather than requiring
    the employer to separately open the candidate's public profile (job
    seekers don't have a public profile page at all -- this endpoint, in
    the context of a specific application, is the only place an employer
    is allowed to see this much about a candidate).

    Still NOT a ModelSerializer on User -- that would need every User
    field read_only'd by hand, and it is easy to forget one (is_staff, say)
    and leak it. Building the exact shape we want from scratch is safer
    than subtracting from a shape we do not fully control.
    """

    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()

    headline = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    phone = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    profile_photo = serializers.SerializerMethodField()
    years_of_experience = serializers.SerializerMethodField()
    expected_salary = serializers.SerializerMethodField()
    github_url = serializers.SerializerMethodField()
    linkedin_url = serializers.SerializerMethodField()
    portfolio_url = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    education = serializers.SerializerMethodField()
    experience = serializers.SerializerMethodField()

    def _profile(self, user):
        return getattr(user, "jobseeker_profile", None)

    def _photo_url(self, profile):
        if not profile.profile_photo:
            return None
        request = self.context.get("request")
        url = profile.profile_photo.url
        return request.build_absolute_uri(url) if request else url

    def get_headline(self, user):
        profile = self._profile(user)
        return profile.headline if profile else ""

    def get_bio(self, user):
        profile = self._profile(user)
        return profile.bio if profile else ""

    def get_phone(self, user):
        profile = self._profile(user)
        return profile.phone if profile else ""

    def get_location(self, user):
        profile = self._profile(user)
        return profile.location if profile else ""

    def get_profile_photo(self, user):
        profile = self._profile(user)
        return self._photo_url(profile) if profile else None

    def get_years_of_experience(self, user):
        profile = self._profile(user)
        return profile.years_of_experience if profile else 0

    def get_expected_salary(self, user):
        profile = self._profile(user)
        return profile.expected_salary if profile else None

    def get_github_url(self, user):
        profile = self._profile(user)
        return profile.github_url if profile else ""

    def get_linkedin_url(self, user):
        profile = self._profile(user)
        return profile.linkedin_url if profile else ""

    def get_portfolio_url(self, user):
        profile = self._profile(user)
        return profile.portfolio_url if profile else ""

    def get_skills(self, user):
        profile = self._profile(user)
        return [s.name for s in profile.skills.all()] if profile else []

    def get_education(self, user):
        profile = self._profile(user)
        return EducationSerializer(profile.education.all(), many=True).data if profile else []

    def get_experience(self, user):
        profile = self._profile(user)
        return ExperienceSerializer(profile.experience.all(), many=True).data if profile else []


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

    `resume` is OPTIONAL here, not required as it was originally: if the
    seeker doesn't attach one, the view falls back to a snapshot of their
    profile resume. Whether that fallback is even possible (does a profile
    resume exist?) is a question the VIEW has to answer -- by the time this
    serializer runs, all it knows is "no file was attached", which is a
    valid state, not an error, until the view checks further.
    """

    class Meta:
        model = Application
        fields = ["resume", "cover_letter"]
        extra_kwargs = {"resume": {"required": False}}

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
