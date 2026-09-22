from django.utils import timezone
from rest_framework import serializers

from .models import Interview


class InterviewSerializer(serializers.ModelSerializer):
    """
    Read shape, used for both the seeker's and employer's view of the same
    row (same pattern as ApplicationSerializer in Phase 6). Flattens a few
    fields off the related application/job so the frontend doesn't need a
    second request just to show "interview for Backend Engineer at Acme".
    """

    job_title = serializers.CharField(source="application.job.title", read_only=True)
    company_name = serializers.CharField(source="application.job.company.name", read_only=True)
    applicant_name = serializers.SerializerMethodField()
    applicant_email = serializers.EmailField(source="application.applicant.email", read_only=True)

    class Meta:
        model = Interview
        fields = [
            "id", "application", "job_title", "company_name",
            "applicant_name", "applicant_email",
            "interview_type", "scheduled_at", "meeting_link", "location",
            "notes", "status", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_applicant_name(self, obj) -> str:
        return obj.application.applicant.full_name or obj.application.applicant.email


class InterviewCreateSerializer(serializers.ModelSerializer):
    """
    POST /api/applications/{id}/interviews/

    `application` and `scheduled_by` are NOT writable here -- both come
    from the URL and the authenticated user, never the request body. Same
    "don't trust a body-supplied FK" rule as every create serializer since
    Phase 3's JobWriteSerializer.
    """

    class Meta:
        model = Interview
        fields = ["interview_type", "scheduled_at", "meeting_link", "location", "notes"]

    def validate_scheduled_at(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Interview time cannot be in the past.")
        return value

    def validate(self, attrs):
        # Mirrors Interview.clean() so a bad request gets a field-specific
        # 400 instead of surfacing as an IntegrityError/ValidationError from
        # a bare .save() -- same reasoning as Job's salary-range check in
        # Phase 3.
        if not attrs.get("meeting_link") and not attrs.get("location"):
            raise serializers.ValidationError(
                "Provide a meeting link (phone/video) or a location (onsite)."
            )
        return attrs

    def to_representation(self, instance):
        return InterviewSerializer(instance, context=self.context).data


class InterviewUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH /api/interviews/{id}/ -- reschedule, add notes, or change status
    (mark completed/cancelled). Deliberately allows partial updates to
    scheduling fields AND status through one endpoint rather than splitting
    "reschedule" and "cancel" into separate actions -- there is no
    meaningful authorization difference between them (any member of the
    company that owns the underlying job may do either, mirroring how Job
    editing works since Phase 3 -- `scheduled_by` is an audit trail, not an
    ownership gate, same as `Job.posted_by`), so splitting them would just
    be two endpoints enforcing the identical rule.
    """

    class Meta:
        model = Interview
        fields = ["interview_type", "scheduled_at", "meeting_link", "location", "notes", "status"]
        extra_kwargs = {field: {"required": False} for field in
                         ["interview_type", "scheduled_at", "meeting_link", "location", "notes", "status"]}

    def validate(self, attrs):
        link = attrs.get("meeting_link", self.instance.meeting_link)
        location = attrs.get("location", self.instance.location)
        if not link and not location:
            raise serializers.ValidationError(
                "Provide a meeting link (phone/video) or a location (onsite)."
            )
        return attrs

    def to_representation(self, instance):
        return InterviewSerializer(instance, context=self.context).data
