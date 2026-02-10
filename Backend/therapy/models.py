from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from patients.models import ChildProfile


class TherapySession(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    class SupervisionMode(models.TextChoices):
        THERAPIST = "therapist", "Therapist"
        CAREGIVER = "caregiver", "Caregiver"
        MIXED = "mixed", "Mixed"

    id = models.BigAutoField(primary_key=True)

    child = models.ForeignKey(ChildProfile, on_delete=models.PROTECT, related_name="therapy_sessions")
    therapist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="therapy_sessions")

    # Who actually started/created the session record (therapist, caregiver, admin)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_therapy_sessions",
        null=True,
        blank=True,
    )

    supervision_mode = models.CharField(
        max_length=20,
        choices=SupervisionMode.choices,
        default=SupervisionMode.THERAPIST,
    )

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    session_date = models.DateField(default=timezone.localdate)

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    title = models.CharField(max_length=200, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["child", "session_date"]),
            models.Index(fields=["therapist", "session_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Session({self.id}) child={self.child_id} status={self.status}"


class SessionTrial(models.Model):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"

    id = models.BigAutoField(primary_key=True)

    session = models.ForeignKey(TherapySession, on_delete=models.CASCADE, related_name="trials")

    trial_type = models.CharField(max_length=120)  # e.g., "joint_attention", "speech_prompt", "imitation"
    prompt = models.TextField(blank=True, default="")
    target_behavior = models.CharField(max_length=200, blank=True, default="")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    score = models.IntegerField(null=True, blank=True)  # 0-10 (validate in serializer)
    success = models.BooleanField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["trial_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Trial({self.id}) type={self.trial_type} status={self.status}"


class Observation(models.Model):
    """
    Observation can be attached to a session or a specific trial.
    Also used for structured telemetry (JSON tags) for games and AI signals.
    """
    id = models.BigAutoField(primary_key=True)

    session = models.ForeignKey(TherapySession, on_delete=models.CASCADE, related_name="observations")
    trial = models.ForeignKey(SessionTrial, on_delete=models.SET_NULL, null=True, blank=True, related_name="observations")

    therapist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="observations")

    note = models.TextField(blank=True, default="")

    # IMPORTANT: dict is required for structured telemetry
    tags = models.JSONField(default=dict, blank=True)
    rating = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["therapist", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Obs({self.id}) session={self.session_id} trial={self.trial_id}"


class ScenarioImage(models.Model):
    """
    A scenario image/video used in the Scene Description game.
    Stores the image, expected description, and metadata for adaptive difficulty.
    """
    id = models.BigAutoField(primary_key=True)

    # Scenario details
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="scenarios/")  # or VideoField for videos
    expected_description = models.TextField(help_text="Expected key elements child should describe")

    # Difficulty level (1-3)
    level = models.IntegerField(default=1, choices=[(1, "Easy"), (2, "Medium"), (3, "Hard")])

    # Key elements to look for (JSON list)
    key_elements = models.JSONField(default=list, blank=True, help_text="List of key things to describe")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"Scenario({self.id}) {self.title} (Level {self.level})"


class SceneDescriptionResponse(models.Model):
    """
    Tracks a child's response to a scenario image in the Scene Description game.
    """
    id = models.BigAutoField(primary_key=True)

    trial = models.ForeignKey(SessionTrial, on_delete=models.CASCADE, related_name="scene_responses")
    scenario = models.ForeignKey(ScenarioImage, on_delete=models.PROTECT, related_name="responses")

    child_response = models.TextField(help_text="Child's description of the scenario")

    # LLM Evaluation Results
    llm_feedback = models.TextField(blank=True, default="", help_text="Detailed feedback from LLM")
    llm_score = models.IntegerField(null=True, blank=True, help_text="0-100 score from LLM")
    key_elements_found = models.JSONField(default=list, blank=True, help_text="Which key elements were mentioned")
    clarity_score = models.IntegerField(null=True, blank=True, help_text="0-10 clarity/coherence")
    completeness_score = models.IntegerField(null=True, blank=True, help_text="0-10 how complete the description is")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["trial"]),
            models.Index(fields=["scenario"]),
        ]

    def __str__(self) -> str:
        return f"Response({self.id}) trial={self.trial_id} score={self.llm_score}"
