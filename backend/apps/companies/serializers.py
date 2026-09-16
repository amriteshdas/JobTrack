from rest_framework import serializers

from .models import Company, CompanyMembership


class CompanySerializer(serializers.ModelSerializer):
    open_jobs_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Company
        fields = [
            "id", "name", "slug", "description", "logo", "website",
            "industry", "company_size", "location", "founded_year",
            "open_jobs_count", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "slug", "open_jobs_count", "created_at", "updated_at"]

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Company name is too short.")
        return value

    def validate_founded_year(self, value):
        from django.utils import timezone
        if value and (value < 1800 or value > timezone.now().year):
            raise serializers.ValidationError("Enter a realistic founding year.")
        return value

    def validate_logo(self, value):
        # File upload validation. Never trust a client-supplied filename or
        # content-type; cap the size so an upload cannot exhaust disk.
        if value and value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Logo must be under 2MB.")
        return value


class CompanyMembershipSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="employer_profile.user.email", read_only=True)
    full_name = serializers.CharField(source="employer_profile.user.full_name", read_only=True)

    class Meta:
        model = CompanyMembership
        fields = ["id", "email", "full_name", "membership_role", "created_at"]
        read_only_fields = fields


class AddMemberSerializer(serializers.Serializer):
    """Adds an existing employer account to a company by email."""

    email = serializers.EmailField()
    membership_role = serializers.ChoiceField(
        choices=CompanyMembership.MembershipRole.choices,
        default=CompanyMembership.MembershipRole.RECRUITER,
    )

    def validate_email(self, value):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.filter(email=value.lower()).first()
        if not user:
            raise serializers.ValidationError("No account found with this email.")
        if not user.is_employer:
            raise serializers.ValidationError("That account is not an employer account.")
        if not hasattr(user, "employer_profile"):
            raise serializers.ValidationError("That employer has no profile yet.")
        return value.lower()
