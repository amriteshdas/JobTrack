from rest_framework import serializers

from apps.jobs.serializers import JobSerializer

from .models import SavedJob


class SavedJobSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = ["id", "job", "created_at"]
        read_only_fields = fields
