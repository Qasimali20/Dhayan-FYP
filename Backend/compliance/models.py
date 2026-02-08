from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from patients.models import ChildProfile, Guardian


class Consent(models.Model):
    """
    Legal-grade consent record.
    You can revoke consent without deleting history.
    """
    class ConsentType(models.TextChoices):
        DATA = "data", "Data processing"
        AUDIO = "audio", "Audio recording"
        VIDEO = "video", "Video recording"
        FACE = "face", "Face analysis"
        AI = "ai", "AI-assisted therapy"
        RESEARCH = "research", "Research use"

    id = models.BigAutoField(primary_key=True)

    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name="consents")
    guardian = models.ForeignKey(Guardian, on_delete=models.PROTECT, related_name="consents")

    consent_type = models.CharField(max_length=20, choices=ConsentType.choices)
    scope = models.JSONField(default=dict, blank=True)  # e.g. {"modules":["joint_attention"],"purpose":"therapy"}

    granted_at = models.DateTimeField(default=timezone.now)
    revoked_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="consents_created",
        null=True,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["child", "consent_type"]),
            models.Index(fields=["guardian"]),
            models.Index(fields=["granted_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["child", "guardian", "consent_type", "granted_at"],
                name="uniq_consent_event",
            ),
        ]

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None
