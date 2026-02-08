from django.urls import path
from speech.views import (
    # Activity library
    SpeechActivityListCreateView,
    SpeechActivityDetailView,
    # Session
    SpeechSessionStartView,
    SpeechSessionSummaryView,
    # Trial endpoints
    SpeechTrialMetaUpsertView,
    SpeechTrialAudioUploadView,
    SpeechTrialAnalysisView,
    SpeechTrialScoreView,
    # Legacy
    SpeechTrialTranscribeView,
    # Progress
    SpeechProgressView,
)

urlpatterns = [
    # ── Activity Library ──
    path("activities", SpeechActivityListCreateView.as_view(), name="speech-activities"),
    path("activities/<int:activity_id>", SpeechActivityDetailView.as_view(), name="speech-activity-detail"),

    # ── Session ──
    path("sessions/start", SpeechSessionStartView.as_view(), name="speech-session-start"),
    path("sessions/<int:session_id>/summary", SpeechSessionSummaryView.as_view(), name="speech-session-summary"),

    # ── Trial ──
    path("trials/<int:trial_id>/meta", SpeechTrialMetaUpsertView.as_view(), name="speech-trial-meta"),
    path("trials/<int:trial_id>/upload-audio", SpeechTrialAudioUploadView.as_view(), name="speech-trial-upload"),
    path("trials/<int:trial_id>/analysis", SpeechTrialAnalysisView.as_view(), name="speech-trial-analysis"),
    path("trials/<int:trial_id>/score", SpeechTrialScoreView.as_view(), name="speech-trial-score"),

    # ── Legacy ──
    path("trials/<int:trial_id>/transcribe", SpeechTrialTranscribeView.as_view(), name="speech-trial-transcribe"),
    path("trials/<int:trial_id>/audio", SpeechTrialAudioUploadView.as_view(), name="speech-trial-audio-legacy"),

    # ── Progress ──
    path("children/<int:child_profile_id>/progress", SpeechProgressView.as_view(), name="speech-progress"),
]
