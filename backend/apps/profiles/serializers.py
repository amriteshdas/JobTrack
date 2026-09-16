from rest_framework import serializers

from .models import EmployerProfile


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
        # `user` is absent entirely: the profile you may edit is determined
        # by your token, never by a field in the request body. Accepting a
        # user id here would let anyone PATCH anyone else's profile.
        read_only_fields = ["id", "email", "full_name", "created_at", "updated_at"]
