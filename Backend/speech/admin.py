from django.contrib import admin
from speech.models import SpeechActivity, SpeechTrialMeta, SpeechRecording, SpeechAnalysis, ASRJob


@admin.register(SpeechActivity)
class SpeechActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "language", "difficulty_level", "is_active", "created_at")
    list_filter = ("category", "language", "difficulty_level", "is_active")
    search_fields = ("name", "description", "expected_text")


@admin.register(SpeechTrialMeta)
class SpeechTrialMetaAdmin(admin.ModelAdmin):
    list_display = ("trial", "activity", "category", "prompt_level", "therapist_score", "created_at")
    list_filter = ("category", "prompt_level", "therapist_score")


@admin.register(SpeechRecording)
class SpeechRecordingAdmin(admin.ModelAdmin):
    list_display = ("trial", "uploaded_by", "duration_ms", "size_bytes", "raw_deleted", "uploaded_at")
    list_filter = ("raw_deleted",)


@admin.register(SpeechAnalysis)
class SpeechAnalysisAdmin(admin.ModelAdmin):
    list_display = ("trial", "processing_status", "transcript_text", "created_at", "completed_at")
    list_filter = ("processing_status",)


@admin.register(ASRJob)
class ASRJobAdmin(admin.ModelAdmin):
    list_display = ("trial", "status", "provider", "result_text", "created_at")
    list_filter = ("status", "provider")
