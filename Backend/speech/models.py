from __future__ import annotations

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from therapy.models import SessionTrial, TherapySession


def speech_audio_upload_path(instance: "SpeechRecording", filename: str) -> str:
    ts = timezone.now().strftime("%Y/%m/%d")
    return f"speech_audio/{ts}/trial_{instance.trial_id}/{filename}"


# ─── Activity Library ───────────────────────────────────────────────────────

class SpeechActivity(models.Model):
    """
    Reusable speech therapy activity template.
    e.g. 'Word Repetition', 'Picture Naming', 'WH Questions', etc.
    """

    class PromptType(models.TextChoices):
        TEXT = "text", "Text"
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio"
        TEXT_IMAGE = "text_image", "Text + Image"

    class ActivityCategory(models.TextChoices):
        REPETITION = "repetition", "Repetition Practice"
        PICTURE_NAMING = "picture_naming", "Picture Naming"
        QUESTIONS = "questions", "Question & Answer"
        STORY_RETELL = "story_retell", "Story Retell"
        CATEGORY_NAMING = "category_naming", "Category Naming"

    id = models.BigAutoField(primary_key=True)

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=ActivityCategory.choices)
    description = models.TextField(blank=True, default="")

    prompt_type = models.CharField(max_length=20, choices=PromptType.choices, default=PromptType.TEXT)
    prompt_payload = models.JSONField(
        default=dict, blank=True,
        help_text='{"text": "...", "image_url": "...", "audio_url": "..."}'
    )
    expected_text = models.CharField(max_length=500, blank=True, default="",
                                     help_text="Expected response text for scoring")

    language = models.CharField(max_length=10, default="en")

    difficulty_level = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    difficulty_json = models.JSONField(default=dict, blank=True,
                                       help_text="Custom difficulty params per level")

    # ABA prompt fading levels
    prompt_levels = models.JSONField(
        default=list, blank=True,
        help_text='[{"level": 0, "instruction": "Full model"}, {"level": 3, "instruction": "Independent"}]'
    )

    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name="created_speech_activities")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Speech Activities"
        ordering = ["category", "difficulty_level", "name"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["language"]),
            models.Index(fields=["difficulty_level"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()}, L{self.difficulty_level})"


# ─── Trial-Level Models ─────────────────────────────────────────────────────

class SpeechTrialMeta(models.Model):
    """
    Speech-specific metadata attached to a generic SessionTrial.
    Links to a SpeechActivity and stores prompt-level used.
    """
    id = models.BigAutoField(primary_key=True)
    trial = models.OneToOneField(SessionTrial, on_delete=models.CASCADE, related_name="speech_meta")
    activity = models.ForeignKey(SpeechActivity, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name="trial_metas")

    target_text = models.CharField(max_length=500, blank=True, default="")
    target_phoneme = models.CharField(max_length=50, blank=True, default="")
    category = models.CharField(max_length=120, blank=True, default="")
    language = models.CharField(max_length=10, blank=True, default="en")

    difficulty = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    prompt_level = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(3)],
                                        help_text="0=Full model, 1=Partial, 2=Gesture, 3=Independent")

    attempt_number = models.IntegerField(default=1)
    latency_ms = models.IntegerField(null=True, blank=True, help_text="Time from prompt to first speech")

    therapist_transcript = models.CharField(max_length=500, blank=True, default="")
    therapist_score = models.CharField(max_length=20, blank=True, default="",
                                        help_text="success/fail/partial")
    therapist_notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["category", "language"]),
            models.Index(fields=["difficulty"]),
            models.Index(fields=["activity"]),
        ]

    def __str__(self) -> str:
        return f"SpeechTrialMeta(trial={self.trial_id}, target={self.target_text})"


class SpeechRecording(models.Model):
    """
    Stores uploaded audio for a speech trial.
    Consent-aware: raw audio can be deleted after analysis.
    """
    id = models.BigAutoField(primary_key=True)
    trial = models.OneToOneField(SessionTrial, on_delete=models.CASCADE, related_name="speech_recording")

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="speech_recordings")
    uploaded_at = models.DateTimeField(default=timezone.now)

    content_type = models.CharField(max_length=120, blank=True, default="")
    size_bytes = models.BigIntegerField(default=0)
    duration_ms = models.IntegerField(null=True, blank=True)
    sample_rate = models.IntegerField(null=True, blank=True)

    file = models.FileField(upload_to=speech_audio_upload_path)

    # Consent snapshot at time of recording
    consent_snapshot = models.JSONField(default=dict, blank=True,
                                         help_text='{"store_audio": false, "retention_days": 0}')
    raw_deleted = models.BooleanField(default=False, help_text="True if raw audio was purged after analysis")

    class Meta:
        indexes = [
            models.Index(fields=["uploaded_at"]),
            models.Index(fields=["trial"]),
        ]

    def __str__(self) -> str:
        return f"SpeechRecording(trial={self.trial_id}, size={self.size_bytes})"


# ─── Analysis ──────────────────────────────────────────────────────────────

class SpeechAnalysis(models.Model):
    """
    Stores outputs of the audio processing pipeline.
    Separate from trial so analysis can be re-run without touching trial data.
    """

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        DONE = "done", "Done"
        FAILED = "failed", "Failed"

    id = models.BigAutoField(primary_key=True)
    trial = models.ForeignKey(SessionTrial, on_delete=models.CASCADE, related_name="speech_analyses")
    recording = models.ForeignKey(SpeechRecording, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="analyses")

    processing_status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    error_message = models.TextField(blank=True, default="")

    # ASR results
    transcript_text = models.TextField(blank=True, default="")
    transcript_json = models.JSONField(default=dict, blank=True,
                                        help_text="Segments with timestamps")

    # VAD results
    vad_json = models.JSONField(default=dict, blank=True,
                                 help_text='{"segments": [...], "speech_time_ms": ..., "pause_count": ..., "pause_total_ms": ...}')

    # Prosody / voice features
    features_json = models.JSONField(default=dict, blank=True,
                                      help_text='{"duration_ms": ..., "speech_rate_wpm": ..., "energy_mean": ..., ...}')

    # Target alignment scoring
    target_score_json = models.JSONField(default=dict, blank=True,
                                          help_text='{"keyword_match": 0.8, "text_similarity": 0.7, "missing_keywords": [...]}')

    # AI / rule-based feedback
    feedback_json = models.JSONField(default=dict, blank=True,
                                      help_text='{"suggestions": [...], "severity": "info"}')

    # Model versions used
    model_versions = models.JSONField(default=dict, blank=True,
                                       help_text='{"asr": "whisper-base", "vad": "silero-v4"}')

    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Speech Analyses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["trial", "created_at"]),
            models.Index(fields=["processing_status"]),
        ]

    def __str__(self):
        return f"SpeechAnalysis({self.id}) trial={self.trial_id} status={self.processing_status}"


# ─── Legacy compat (keep existing ASRJob for backward compat) ────────────

class ASRJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RUNNING = "running", "Running"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    id = models.BigAutoField(primary_key=True)
    trial = models.ForeignKey(SessionTrial, on_delete=models.CASCADE, related_name="asr_jobs")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="asr_jobs_created")
    created_at = models.DateTimeField(default=timezone.now)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    provider = models.CharField(max_length=50, default="http")
    model_name = models.CharField(max_length=120, blank=True, default="")

    result_text = models.TextField(blank=True, default="")
    result_confidence = models.FloatField(null=True, blank=True)
    error = models.TextField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["trial", "created_at"]),
        ]

    def __str__(self):
        return f"ASRJob({self.id}) trial={self.trial_id} status={self.status}"


# ─── Backward compat alias ──────────────────────────────────────────────────
SpeechTrialAudio = SpeechRecording
