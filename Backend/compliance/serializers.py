from rest_framework import serializers
from compliance.models import Consent


class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = (
            "id", "child", "guardian", "consent_type", "scope",
            "granted_at", "revoked_at", "created_by",
        )
        read_only_fields = ("id", "granted_at", "created_by")


class CreateConsentSerializer(serializers.Serializer):
    child_id = serializers.IntegerField()
    guardian_id = serializers.IntegerField()
    consent_type = serializers.ChoiceField(choices=Consent.ConsentType.choices)
    scope = serializers.JSONField(required=False, default=dict)
