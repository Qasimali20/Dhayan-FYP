from __future__ import annotations

from rest_framework import serializers

from speech.models import (
    SpeechActivity,
    SpeechTrialMeta,
    SpeechRecording,
    SpeechAnalysis,
    ASRJob,
)


# ─── Activity Library ───────────────────────────────────────────────────────

class SpeechActivitySerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    prompt_type_display = serializers.CharField(source="get_prompt_type_display", read_only=True)

    class Meta:
        model = SpeechActivity
        fields = (
            "id", "name", "category", "category_display",
            "description", "prompt_type", "prompt_type_display",
            "prompt_payload", "expected_text", "language",
            "difficulty_level", "difficulty_json", "prompt_levels",
            "is_active", "created_by", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_by", "created_at", "updated_at")


class SpeechActivityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechActivity
        fields = (
            "name", "category", "description", "prompt_type",
            "prompt_payload", "expected_text", "language",
            "difficulty_level", "difficulty_json", "prompt_levels",
            "is_active",
        )


# ─── Trial Meta ──────────────────────────────────────────────────────────────

class SpeechMetaUpsertSerializer(serializers.Serializer):
    activity_id = serializers.IntegerField(required=False, allow_null=True)
    target_text = serializers.CharField(required=False, allow_blank=True, default="")
    target_phoneme = serializers.CharField(required=False, allow_blank=True, default="")
    category = serializers.CharField(required=False, allow_blank=True, default="")
    language = serializers.CharField(required=False, allow_blank=True, default="en")
    difficulty = serializers.IntegerField(required=False, min_value=1, max_value=10, default=1)
    prompt_level = serializers.IntegerField(required=False, min_value=0, max_value=3, default=0)
    therapist_transcript = serializers.CharField(required=False, allow_blank=True, default="")
    therapist_score = serializers.ChoiceField(
        choices=["success", "fail", "partial", ""],
        required=False, default=""
    )
    therapist_notes = serializers.CharField(required=False, allow_blank=True, default="")


class SpeechTrialMetaSerializer(serializers.ModelSerializer):
    activity_name = serializers.SerializerMethodField()

    class Meta:
        model = SpeechTrialMeta
        fields = (
            "id", "trial", "activity", "activity_name",
            "target_text", "target_phoneme", "category", "language",
            "difficulty", "prompt_level", "attempt_number", "latency_ms",
            "therapist_transcript", "therapist_score", "therapist_notes",
            "created_at",
        )
        read_only_fields = ("id", "created_at")

    def get_activity_name(self, obj):
        return obj.activity.name if obj.activity else None


# ─── Audio / Recording ───────────────────────────────────────────────────────

class SpeechAudioUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    duration_ms = serializers.IntegerField(required=False, min_value=1)

    def validate_file(self, f):
        allowed = {
            "audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3",
            "audio/mp4", "audio/x-m4a", "audio/aac", "audio/ogg",
            "audio/webm",
        }
        ct = getattr(f, "content_type", "") or ""
        if ct and ct not in allowed:
            raise serializers.ValidationError(f"Unsupported content type: {ct}")
        max_mb = 25
        if f.size > max_mb * 1024 * 1024:
            raise serializers.ValidationError(f"File too large. Max {max_mb}MB.")
        return f


class SpeechRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechRecording
        fields = (
            "id", "trial", "uploaded_by", "uploaded_at",
            "content_type", "size_bytes", "duration_ms", "sample_rate",
            "file", "raw_deleted",
        )
        read_only_fields = ("id", "uploaded_by", "uploaded_at", "content_type", "size_bytes")

# backward compat alias
SpeechTrialAudioSerializer = SpeechRecordingSerializer


# ─── Analysis ────────────────────────────────────────────────────────────────

class SpeechAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpeechAnalysis
        fields = (
            "id", "trial", "recording",
            "processing_status", "error_message",
            "transcript_text", "transcript_json",
            "vad_json", "features_json",
            "target_score_json", "feedback_json",
            "model_versions",
            "created_at", "completed_at",
        )
        read_only_fields = fields


# ─── Therapist Scoring ───────────────────────────────────────────────────────

class TherapistScoreSerializer(serializers.Serializer):
    score = serializers.ChoiceField(choices=["success", "fail", "partial"])
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    override_transcript = serializers.CharField(required=False, allow_blank=True, default="")


# ─── Session Start ───────────────────────────────────────────────────────────

class SpeechSessionStartSerializer(serializers.Serializer):
    child_id = serializers.IntegerField()
    activity_id = serializers.IntegerField()
    trials_planned = serializers.IntegerField(min_value=1, max_value=50, default=8)
    supervision_mode = serializers.ChoiceField(
        choices=["therapist", "caregiver", "mixed"], default="therapist"
    )
    prompt_level = serializers.IntegerField(min_value=0, max_value=3, default=0)


# ─── Legacy ASR ──────────────────────────────────────────────────────────────

class ASRJobCreateSerializer(serializers.Serializer):
    model_name = serializers.CharField(required=False, allow_blank=True, default="")


class ASRJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ASRJob
        fields = (
            "id", "trial", "created_by", "created_at",
            "status", "provider", "model_name",
            "result_text", "result_confidence", "error",
        )
        read_only_fields = (
            "id", "created_by", "created_at", "status",
            "provider", "result_text", "result_confidence", "error",
        )
