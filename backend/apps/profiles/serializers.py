from rest_framework import serializers

from apps.jobs.models import Skill
from apps.jobs.serializers import SkillSerializer

from .models import Education, EmployerProfile, Experience, JobSeekerProfile


class EmployerProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = EmployerProfile
        fields = [
            "id", "email", "full_name",
            "designation", "phone", "bio",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "email", "full_name", "created_at", "updated_at"]


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ["id", "institution", "degree", "field_of_study", "start_date", "end_date"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if end and start and end < start:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})
        return attrs


class ExperienceSerializer(serializers.ModelSerializer):
    is_current = serializers.BooleanField(read_only=True)

    class Meta:
        model = Experience
        fields = [
            "id", "company_name", "title", "start_date", "end_date",
            "description", "is_current",
        ]
        read_only_fields = ["id", "is_current"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if end and start and end < start:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})
        return attrs


class JobSeekerProfileSerializer(serializers.ModelSerializer):
    """
    Read shape for the candidate profile, used for /profiles/seeker/me/ and
    (from Phase 6) whatever an employer sees when reviewing an applicant.

    skills/education/experience are nested and READ-ONLY here. Writing them
    through a nested PATCH on the parent profile is the classic DRF trap:
    "did you mean to replace the whole list, or add one item?" is
    ambiguous, so each has its own dedicated endpoint/serializer instead
    (skills via a dedicated action below, education/experience via their
    own ViewSets).
    """

    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    experience = ExperienceSerializer(many=True, read_only=True)

    class Meta:
        model = JobSeekerProfile
        fields = [
            "id", "email", "full_name",
            "headline", "bio", "phone", "location",
            "profile_photo", "resume",
            "years_of_experience", "expected_salary",
            "github_url", "linkedin_url", "portfolio_url",
            "skills", "education", "experience",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "email", "full_name", "skills", "education", "experience",
            "created_at", "updated_at",
        ]


class JobSeekerProfileWriteSerializer(serializers.ModelSerializer):
    """
    PATCH /profiles/seeker/me/ -- scalar fields only. Note `user` is absent:
    the profile you may edit comes from request.user, never from the body
    (same IDOR-avoidance pattern as EmployerProfileMeView in Phase 3).
    """

    class Meta:
        model = JobSeekerProfile
        fields = [
            "headline", "bio", "phone", "location",
            "profile_photo", "resume",
            "years_of_experience", "expected_salary",
            "github_url", "linkedin_url", "portfolio_url",
        ]

    def validate_resume(self, value):
        # File upload validation: never trust client-supplied size/type
        # claims. Extension is checked at the model level (FileExtensionValidator);
        # size is checked here since that isn't expressible as a model validator.
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Resume must be under 5MB.")
        return value

    def validate_profile_photo(self, value):
        if value and value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Profile photo must be under 2MB.")
        return value

    def validate_expected_salary(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Expected salary cannot be negative.")
        return value

    def to_representation(self, instance):
        # Return the rich read shape (with nested skills/education/
        # experience) after a write, so the frontend doesn't need a second
        # request to re-sync its view of the profile.
        return JobSeekerProfileSerializer(instance, context=self.context).data


class UpdateSkillsSerializer(serializers.Serializer):
    """
    PUT /profiles/seeker/me/skills/  body: {"skills": ["Python", "Django"]}

    A full replace, not an add/remove -- the same reasoning as Job's skills
    field in Phase 3: accepting plain strings and resolving/creating Skill
    rows server-side is a much friendlier API than requiring the client to
    look up skill IDs first, and it is the one place skill-name
    normalization needs to live.
    """

    skills = serializers.ListField(
        child=serializers.CharField(max_length=80), allow_empty=True
    )

    def save(self):
        names = self.validated_data["skills"]
        resolved = []
        for raw in names:
            name = raw.strip()
            if not name:
                continue
            skill = Skill.objects.filter(name__iexact=name).first()
            if skill is None:
                skill = Skill.objects.create(name=name)
            resolved.append(skill)

        profile = self.context["profile"]
        profile.skills.set(resolved)
        return profile
