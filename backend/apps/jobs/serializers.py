from django.utils import timezone
from rest_framework import serializers

from apps.companies.models import Company

from .models import Job, Skill


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name", "slug"]
        read_only_fields = ["id", "slug"]


class JobSerializer(serializers.ModelSerializer):
    """
    Used for reading jobs. Nested company/skill data is read-only here;
    writes go through JobWriteSerializer.
    """

    company_name = serializers.CharField(source="company.name", read_only=True)
    company_slug = serializers.CharField(source="company.slug", read_only=True)
    company_logo = serializers.ImageField(source="company.logo", read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id", "title", "description", "responsibilities", "qualifications",
            "benefits", "location", "work_mode", "employment_type",
            "experience_required", "salary_min", "salary_max", "skills",
            "status", "application_deadline", "published_at", "is_open",
            "company", "company_name", "company_slug", "company_logo",
            "created_at", "updated_at",
        ]
        read_only_fields = fields


class JobWriteSerializer(serializers.ModelSerializer):
    """
    Create/update serializer.

    `skills` accepts a list of plain strings rather than Skill primary keys.
    Making a recruiter look up skill IDs before posting a job would be a
    hostile API; instead we resolve or create each Skill server-side, which
    is also where the normalization lives so the lookup table stays clean.
    """

    skills = serializers.ListField(
        child=serializers.CharField(max_length=80),
        required=False,
        allow_empty=True,
        write_only=True,
    )

    class Meta:
        model = Job
        fields = [
            "id", "company", "title", "description", "responsibilities",
            "qualifications", "benefits", "location", "work_mode",
            "employment_type", "experience_required", "salary_min",
            "salary_max", "skills", "status", "application_deadline",
        ]
        read_only_fields = ["id"]

    def validate_company(self, company):
        """
        The critical check on this endpoint.

        `company` arrives in the request body, so without this an employer
        could POST a job with someone else's company id and publish jobs
        under their brand. We verify membership here rather than trusting
        the payload -- this is object-level authorization applied to a
        FOREIGN KEY, which is easy to overlook because the object being
        protected is not the object being created.
        """
        user = self.context["request"].user
        profile = getattr(user, "employer_profile", None)
        if profile is None:
            raise serializers.ValidationError("You do not have an employer profile.")

        if not company.memberships.filter(employer_profile=profile).exists():
            raise serializers.ValidationError("You are not a member of this company.")
        return company

    def validate_application_deadline(self, value):
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Deadline cannot be in the past.")
        return value

    def validate(self, attrs):
        # Mirror the DB check constraint so clients get a clean 400 with a
        # field-specific message instead of a 500 from an IntegrityError.
        smin = attrs.get("salary_min", getattr(self.instance, "salary_min", None))
        smax = attrs.get("salary_max", getattr(self.instance, "salary_max", None))
        if smin is not None and smax is not None and smin > smax:
            raise serializers.ValidationError(
                {"salary_max": "Maximum salary cannot be below the minimum."}
            )
        return attrs

    def _sync_skills(self, job, names):
        skills = []
        for raw in names:
            name = raw.strip()
            if not name:
                continue
            # Case-insensitive match first, so "python" joins the existing
            # "Python" row instead of creating a near-duplicate.
            skill = Skill.objects.filter(name__iexact=name).first()
            if skill is None:
                skill = Skill.objects.create(name=name)
            skills.append(skill)
        job.skills.set(skills)

    def create(self, validated_data):
        skill_names = validated_data.pop("skills", [])
        # posted_by comes from the token, never the request body.
        validated_data["posted_by"] = self.context["request"].user.employer_profile

        if validated_data.get("status") == Job.Status.PUBLISHED:
            validated_data["published_at"] = timezone.now()

        job = Job.objects.create(**validated_data)
        self._sync_skills(job, skill_names)
        return job

    def update(self, instance, validated_data):
        skill_names = validated_data.pop("skills", None)

        # Stamp published_at the first time a job goes live, and never
        # overwrite it on later edits -- "posted date" must stay stable.
        new_status = validated_data.get("status")
        if (
            new_status == Job.Status.PUBLISHED
            and instance.status != Job.Status.PUBLISHED
            and instance.published_at is None
        ):
            validated_data["published_at"] = timezone.now()

        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()

        if skill_names is not None:
            self._sync_skills(instance, skill_names)
        return instance

    def to_representation(self, instance):
        # Respond with the rich read shape so clients get nested company and
        # skill objects back immediately after a write.
        return JobSerializer(instance, context=self.context).data
