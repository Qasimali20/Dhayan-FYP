from __future__ import annotations

from datetime import date
from rest_framework import serializers
from django.contrib.auth import get_user_model

from accounts.models import Role, UserRole
from patients.models import ChildProfile, Guardian, TherapistChildAssignment

User = get_user_model()


class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = ("id", "name", "relation", "phone", "email", "address")


class ChildProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    guardians = GuardianSerializer(many=True, read_only=True)

    class Meta:
        model = ChildProfile
        fields = (
            "id",
            "email",
            "full_name",
            "date_of_birth",
            "gender",
            "diagnosis_notes",
            "clinical_notes",
            "consent_audio",
            "consent_video",
            "consent_face",
            "consent_ai",
            "guardians",
            "created_at",
            "updated_at",
        )


class ChildCreateSerializer(serializers.Serializer):
    """
    Creates:
    - User(email, full_name) for child
    - Role assignment child
    - ChildProfile
    - Optional guardian records
    - Assign to requesting therapist (if therapist), else admin must assign separately
    """
    email = serializers.EmailField()
    full_name = serializers.CharField(required=False, allow_blank=True, default="")

    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(choices=ChildProfile.Gender.choices, required=False)

    diagnosis_notes = serializers.CharField(required=False, allow_blank=True, default="")
    clinical_notes = serializers.CharField(required=False, allow_blank=True, default="")

    consent_audio = serializers.BooleanField(required=False, default=False)
    consent_video = serializers.BooleanField(required=False, default=False)
    consent_face = serializers.BooleanField(required=False, default=False)
    consent_ai = serializers.BooleanField(required=False, default=False)

    guardians = GuardianSerializer(many=True, required=False, default=list)

    def validate_email(self, value: str) -> str:
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        guardians_data = validated_data.pop("guardians", [])

        child_email = validated_data.pop("email")
        child_full_name = validated_data.pop("full_name", "")

        # Create child user (no usable password; child does not login)
        child_user = User.objects.create_user(email=child_email, password=None, full_name=child_full_name, is_active=True)

        # Ensure 'child' role exists
        child_role, _ = Role.objects.get_or_create(slug="child", defaults={"name": "Child"})
        UserRole.objects.get_or_create(user=child_user, role=child_role)

        profile = ChildProfile.objects.create(user=child_user, **validated_data)

        for g in guardians_data:
            Guardian.objects.create(child_profile=profile, **g)

        return profile


class ChildUpdateSerializer(serializers.ModelSerializer):
    guardians = GuardianSerializer(many=True, required=False)

    class Meta:
        model = ChildProfile
        fields = (
            "date_of_birth",
            "gender",
            "diagnosis_notes",
            "clinical_notes",
            "consent_audio",
            "consent_video",
            "consent_face",
            "consent_ai",
            "guardians",
        )

    def update(self, instance: ChildProfile, validated_data):
        guardians_data = validated_data.pop("guardians", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        # Replace guardians if provided
        if guardians_data is not None:
            instance.guardians.all().delete()
            for g in guardians_data:
                Guardian.objects.create(child_profile=instance, **g)

        return instance


class AssignTherapistSerializer(serializers.Serializer):
    therapist_user_id = serializers.IntegerField()
    is_primary = serializers.BooleanField(default=True)
