from __future__ import annotations

from rest_framework import serializers
from django.contrib.auth import get_user_model

from patients.models import ChildProfile
from therapy.models import TherapySession, SessionTrial, Observation

User = get_user_model()


class SessionTrialSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionTrial
        fields = (
            "id",
            "trial_type",
            "prompt",
            "target_behavior",
            "status",
            "started_at",
            "ended_at",
            "score",
            "success",
            "created_at",
        )
        read_only_fields = ("id", "started_at", "ended_at", "created_at", "status")

    def validate_score(self, value):
        if value is None:
            return value
        if not (0 <= value <= 10):
            raise serializers.ValidationError("score must be between 0 and 10")
        return value


class ObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observation
        fields = ("id", "trial", "note", "tags", "rating", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_rating(self, value):
        if value is None:
            return value
        if not (0 <= value <= 10):
            raise serializers.ValidationError("rating must be between 0 and 10")
        return value


class TherapySessionSerializer(serializers.ModelSerializer):
    child_id = serializers.IntegerField(source="child.id", read_only=True)
    child_email = serializers.EmailField(source="child.user.email", read_only=True)
    therapist_id = serializers.IntegerField(source="therapist.id", read_only=True)
    therapist_email = serializers.EmailField(source="therapist.email", read_only=True)

    trials = SessionTrialSerializer(many=True, read_only=True)
    observations = ObservationSerializer(many=True, read_only=True)

    class Meta:
        model = TherapySession
        fields = (
            "id",
            "status",
            "session_date",
            "started_at",
            "ended_at",
            "title",
            "notes",
            "child_id",
            "child_email",
            "therapist_id",
            "therapist_email",
            "trials",
            "observations",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "started_at", "ended_at", "created_at", "updated_at")


class CreateSessionSerializer(serializers.Serializer):
    child_profile_id = serializers.IntegerField()
    title = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    session_date = serializers.DateField(required=False)

    def validate_child_profile_id(self, value):
        if not ChildProfile.objects.filter(id=value).exists():
            raise serializers.ValidationError("Child profile not found")
        return value


class AddTrialSerializer(serializers.Serializer):
    trial_type = serializers.CharField(max_length=120)
    prompt = serializers.CharField(required=False, allow_blank=True, default="")
    target_behavior = serializers.CharField(required=False, allow_blank=True, default="")


class UpdateTrialResultSerializer(serializers.Serializer):
    score = serializers.IntegerField(required=False, allow_null=True)
    success = serializers.BooleanField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=["completed", "skipped"], required=False)

    def validate_score(self, value):
        if value is None:
            return value
        if not (0 <= value <= 10):
            raise serializers.ValidationError("score must be between 0 and 10")
        return value
