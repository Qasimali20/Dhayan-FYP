"""
Speech Therapy API Views.

Endpoints:
  Activities:   CRUD for the activity library
  Sessions:     Start a speech therapy session
  Trials:       Upload audio, get analysis, therapist scoring
  Progress:     Per-child speech progress metrics
"""
from __future__ import annotations

import logging
import random
import threading

from django.conf import settings
from django.db.models import Avg, Count, Q
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from therapy.models import SessionTrial, TherapySession
from patients.models import ChildProfile

from speech.models import (
    SpeechActivity,
    SpeechTrialMeta,
    SpeechRecording,
    SpeechAnalysis,
    ASRJob,
)
from speech.serializers import (
    SpeechActivitySerializer,
    SpeechActivityCreateSerializer,
    SpeechMetaUpsertSerializer,
    SpeechTrialMetaSerializer,
    SpeechAudioUploadSerializer,
    SpeechRecordingSerializer,
    SpeechAnalysisSerializer,
    TherapistScoreSerializer,
    SpeechSessionStartSerializer,
    ASRJobCreateSerializer,
    ASRJobSerializer,
)
from speech.permissions import CanAccessSpeechTrial, is_admin, is_therapist, therapist_has_child

logger = logging.getLogger(__name__)


def _is_speech_trial(trial: SessionTrial) -> bool:
    return (trial.trial_type or "").lower() in {
        "speech_prompt", "speech", "speech_therapy",
    }


def _resolve_prompt(activity: SpeechActivity, trial_index: int, used: set) -> tuple[str, str]:
    """
    Pick a concrete item from the activity's prompt pool and fill in the
    template.  Returns (prompt_text, target_text).

    Pool keys tried (in order):
      questions_pool → phrases_pool → sentences_pool → words_pool → items_pool

    Falls back to the raw template text if no pool is found.
    """
    payload = activity.prompt_payload or {}
    template = payload.get("text", activity.name)

    # ── Questions (yes/no, WH) ──────────────────────────────────────────
    pool = payload.get("questions_pool")
    if pool:
        item = _pick_unique(pool, used, key=lambda q: q if isinstance(q, str) else q.get("question", ""))
        if isinstance(item, dict):
            question = item.get("question", "")
            target = item.get("answer", item.get("expected_keywords", ""))
            if isinstance(target, list):
                target = ", ".join(target)
            return question, str(target)
        return str(item), ""

    # ── Sentences ────────────────────────────────────────────────────────
    pool = payload.get("sentences_pool")
    if pool:
        sentence = _pick_unique(pool, used)
        prompt = template.replace("{sentence}", sentence)
        return prompt, sentence

    # ── Phrases ──────────────────────────────────────────────────────────
    pool = payload.get("phrases_pool")
    if pool:
        phrase = _pick_unique(pool, used)
        prompt = template.replace("{phrase}", phrase)
        return prompt, phrase

    # ── Words ────────────────────────────────────────────────────────────
    pool = payload.get("words_pool")
    if pool:
        word = _pick_unique(pool, used)
        prompt = template.replace("{word}", word)
        return prompt, word

    # ── Items (picture naming) ───────────────────────────────────────────
    pool = payload.get("items_pool")
    if pool:
        item = _pick_unique(pool, used, key=lambda x: x if isinstance(x, str) else x.get("word", ""))
        word = item.get("word", str(item)) if isinstance(item, dict) else str(item)
        prompt = template.replace("{item}", word)
        return prompt, word

    # ── No pool — use template as-is ────────────────────────────────────
    return template, activity.expected_text or ""


def _pick_unique(pool: list, used: set, key=None) -> object:
    """Pick a random item from *pool* that hasn't been used yet.
    Resets *used* and retries once if all items are exhausted."""
    identity = key or (lambda x: x)
    available = [item for item in pool if identity(item) not in used]
    if not available:
        used.clear()
        available = list(pool)
    choice = random.choice(available)
    used.add(identity(choice))
    return choice


# ═══════════════════════════════════════════════════════════════════════════
# Activity Library
# ═══════════════════════════════════════════════════════════════════════════

class SpeechActivityListCreateView(APIView):
    """
    GET  /speech/activities          — list all active activities
    POST /speech/activities          — create a new activity
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = SpeechActivity.objects.filter(is_active=True)

        # Filters
        category = request.query_params.get("category")
        language = request.query_params.get("language")
        difficulty = request.query_params.get("difficulty_level")

        if category:
            qs = qs.filter(category=category)
        if language:
            qs = qs.filter(language=language)
        if difficulty:
            qs = qs.filter(difficulty_level=int(difficulty))

        return Response(SpeechActivitySerializer(qs, many=True).data)

    def post(self, request):
        ser = SpeechActivityCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        activity = ser.save(created_by=request.user)
        return Response(SpeechActivitySerializer(activity).data, status=status.HTTP_201_CREATED)


class SpeechActivityDetailView(APIView):
    """
    GET    /speech/activities/{id}   — detail
    PATCH  /speech/activities/{id}   — update
    DELETE /speech/activities/{id}   — soft-delete
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, activity_id: int):
        try:
            activity = SpeechActivity.objects.get(id=activity_id)
        except SpeechActivity.DoesNotExist:
            return Response({"detail": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(SpeechActivitySerializer(activity).data)

    def patch(self, request, activity_id: int):
        try:
            activity = SpeechActivity.objects.get(id=activity_id)
        except SpeechActivity.DoesNotExist:
            return Response({"detail": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

        ser = SpeechActivityCreateSerializer(activity, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(SpeechActivitySerializer(activity).data)

    def delete(self, request, activity_id: int):
        try:
            activity = SpeechActivity.objects.get(id=activity_id)
        except SpeechActivity.DoesNotExist:
            return Response({"detail": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)
        activity.is_active = False
        activity.save(update_fields=["is_active"])
        return Response({"detail": "Activity deactivated"}, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════
# Session Start
# ═══════════════════════════════════════════════════════════════════════════

class SpeechSessionStartView(APIView):
    """
    POST /speech/sessions/start
    Creates a TherapySession + N planned SessionTrials for speech therapy.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = SpeechSessionStartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # Validate child
        try:
            child = ChildProfile.objects.select_related("user").get(id=data["child_id"])
        except ChildProfile.DoesNotExist:
            return Response({"detail": "Child not found"}, status=status.HTTP_404_NOT_FOUND)

        # Validate activity
        try:
            activity = SpeechActivity.objects.get(id=data["activity_id"], is_active=True)
        except SpeechActivity.DoesNotExist:
            return Response({"detail": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create session
        session = TherapySession.objects.create(
            child=child,
            therapist=request.user,
            created_by=request.user,
            supervision_mode=data.get("supervision_mode", "therapist"),
            status=TherapySession.Status.IN_PROGRESS,
            title=f"Speech: {activity.name}",
            started_at=timezone.now(),
        )

        # Create planned trials
        used_prompts: set = set()     # avoid duplicate prompts across trials
        trials = []
        for i in range(data["trials_planned"]):
            prompt_text, target_text = _resolve_prompt(activity, i, used_prompts)

            trial = SessionTrial.objects.create(
                session=session,
                trial_type="speech_therapy",
                prompt=prompt_text,
                target_behavior=target_text or activity.expected_text,
                status=SessionTrial.Status.PLANNED,
            )
            # Create speech meta for each trial
            SpeechTrialMeta.objects.create(
                trial=trial,
                activity=activity,
                target_text=target_text or activity.expected_text,
                category=activity.category,
                language=activity.language,
                difficulty=activity.difficulty_level,
                prompt_level=data.get("prompt_level", 0),
                attempt_number=i + 1,
            )
            trials.append({
                "trial_id": trial.id,
                "trial_number": i + 1,
                "prompt": prompt_text,
                "target_text": target_text or activity.expected_text,
                "status": trial.status,
            })

        return Response({
            "session_id": session.id,
            "activity": SpeechActivitySerializer(activity).data,
            "trials_planned": data["trials_planned"],
            "trials": trials,
            "prompt_level": data.get("prompt_level", 0),
        }, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════════════════
# Trial Meta
# ═══════════════════════════════════════════════════════════════════════════

class SpeechTrialMetaUpsertView(APIView):
    """
    POST /speech/trials/{trial_id}/meta
    """
    permission_classes = [IsAuthenticated, CanAccessSpeechTrial]

    def post(self, request, trial_id: int):
        try:
            trial = SessionTrial.objects.select_related("session__child__user").get(id=trial_id)
        except SessionTrial.DoesNotExist:
            return Response({"detail": "Trial not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, trial)

        if not _is_speech_trial(trial):
            return Response({"detail": "This trial is not a speech trial"}, status=status.HTTP_400_BAD_REQUEST)

        ser = SpeechMetaUpsertSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        meta, _created = SpeechTrialMeta.objects.get_or_create(trial=trial)

        # Handle activity_id separately
        activity_id = ser.validated_data.pop("activity_id", None)
        if activity_id:
            try:
                meta.activity = SpeechActivity.objects.get(id=activity_id)
            except SpeechActivity.DoesNotExist:
                pass

        for k, v in ser.validated_data.items():
            setattr(meta, k, v)
        meta.save()

        return Response(SpeechTrialMetaSerializer(meta).data, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════
# Audio Upload
# ═══════════════════════════════════════════════════════════════════════════

class SpeechTrialAudioUploadView(APIView):
    """
    POST /speech/trials/{trial_id}/upload-audio
    Upload audio file, create recording, enqueue analysis.
    """
    permission_classes = [IsAuthenticated, CanAccessSpeechTrial]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, trial_id: int):
        try:
            trial = SessionTrial.objects.select_related("session__child__user").get(id=trial_id)
        except SessionTrial.DoesNotExist:
            return Response({"detail": "Trial not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, trial)

        if not _is_speech_trial(trial):
            return Response({"detail": "This trial is not a speech trial"}, status=status.HTTP_400_BAD_REQUEST)

        ser = SpeechAudioUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        f = ser.validated_data["file"]
        ct = getattr(f, "content_type", "") or ""

        # Mark trial as running
        if trial.status == SessionTrial.Status.PLANNED:
            trial.status = SessionTrial.Status.RUNNING
            trial.started_at = timezone.now()
            trial.save(update_fields=["status", "started_at"])

        recording, _created = SpeechRecording.objects.get_or_create(
            trial=trial,
            defaults={
                "uploaded_by": request.user,
                "content_type": ct,
                "size_bytes": f.size,
                "duration_ms": ser.validated_data.get("duration_ms"),
                "file": f,
            }
        )

        if not _created:
            recording.file.delete(save=False)
            recording.file = f
            recording.uploaded_by = request.user
            recording.uploaded_at = timezone.now()
            recording.content_type = ct
            recording.size_bytes = f.size
            recording.duration_ms = ser.validated_data.get("duration_ms")
            recording.save()

        # Enqueue analysis in background
        analysis = SpeechAnalysis.objects.create(
            trial=trial,
            recording=recording,
            processing_status=SpeechAnalysis.Status.QUEUED,
        )

        # Run analysis in background thread (MVP — no Celery needed)
        thread = threading.Thread(
            target=_run_analysis_background,
            args=(analysis.id,),
            daemon=True,
        )
        thread.start()

        return Response({
            "recording": SpeechRecordingSerializer(recording).data,
            "analysis_id": analysis.id,
            "processing_status": analysis.processing_status,
            "message": "Audio uploaded. Analysis is processing in the background.",
        }, status=status.HTTP_201_CREATED)


def _run_analysis_background(analysis_id: int):
    """Run speech analysis pipeline in background thread."""
    import django
    django.setup()  # ensure DB connection in thread

    try:
        analysis = SpeechAnalysis.objects.select_related(
            "trial", "recording", "trial__speech_meta", "trial__speech_meta__activity"
        ).get(id=analysis_id)
    except SpeechAnalysis.DoesNotExist:
        return

    analysis.processing_status = SpeechAnalysis.Status.RUNNING
    analysis.save(update_fields=["processing_status"])

    try:
        from speech.processing.pipeline import process_speech_audio

        # Get expected text and language from meta
        meta = getattr(analysis.trial, "speech_meta", None)
        expected_text = meta.target_text if meta else ""
        language = meta.language if meta else "en"
        activity_category = meta.category if meta else ""

        # Run pipeline
        result = process_speech_audio(
            audio_file_path=analysis.recording.file.path,
            expected_text=expected_text,
            language=language,
            activity_category=activity_category,
        )

        # Store results
        analysis.transcript_text = result.get("transcript_text", "")
        analysis.transcript_json = result.get("transcript_json", {})
        analysis.vad_json = result.get("vad_json", {})
        analysis.features_json = result.get("features_json", {})
        analysis.target_score_json = result.get("target_score_json", {})
        analysis.feedback_json = result.get("feedback_json", {})
        analysis.model_versions = result.get("model_versions", {})
        analysis.processing_status = SpeechAnalysis.Status.DONE
        analysis.completed_at = timezone.now()
        analysis.save()

        # Update trial meta with auto-transcript if therapist hasn't already
        if meta and not meta.therapist_transcript and analysis.transcript_text:
            meta.therapist_transcript = analysis.transcript_text[:500]
            meta.save(update_fields=["therapist_transcript"])

        # Update recording duration if features computed it
        duration = result.get("features_json", {}).get("duration_ms")
        if duration and analysis.recording:
            analysis.recording.duration_ms = duration
            analysis.recording.save(update_fields=["duration_ms"])

        logger.info(f"SpeechAnalysis {analysis_id} completed successfully")

    except Exception as e:
        analysis.processing_status = SpeechAnalysis.Status.FAILED
        analysis.error_message = str(e)
        analysis.save(update_fields=["processing_status", "error_message"])
        logger.error(f"SpeechAnalysis {analysis_id} failed: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Analysis Retrieval
# ═══════════════════════════════════════════════════════════════════════════

class SpeechTrialAnalysisView(APIView):
    """
    GET /speech/trials/{trial_id}/analysis
    Returns the latest analysis for a trial (transcript + features + feedback).
    """
    permission_classes = [IsAuthenticated, CanAccessSpeechTrial]

    def get(self, request, trial_id: int):
        try:
            trial = SessionTrial.objects.select_related("session__child__user").get(id=trial_id)
        except SessionTrial.DoesNotExist:
            return Response({"detail": "Trial not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, trial)

        analysis = SpeechAnalysis.objects.filter(trial=trial).order_by("-created_at").first()
        if not analysis:
            return Response({"detail": "No analysis found for this trial"}, status=status.HTTP_404_NOT_FOUND)

        # Also include meta info
        meta = getattr(trial, "speech_meta", None)
        meta_data = SpeechTrialMetaSerializer(meta).data if meta else None

        return Response({
            "analysis": SpeechAnalysisSerializer(analysis).data,
            "meta": meta_data,
        })


# ═══════════════════════════════════════════════════════════════════════════
# Therapist Scoring
# ═══════════════════════════════════════════════════════════════════════════

class SpeechTrialScoreView(APIView):
    """
    POST /speech/trials/{trial_id}/score
    Therapist final scoring: success/fail/partial + notes.
    """
    permission_classes = [IsAuthenticated, CanAccessSpeechTrial]

    def post(self, request, trial_id: int):
        try:
            trial = SessionTrial.objects.select_related("session__child__user").get(id=trial_id)
        except SessionTrial.DoesNotExist:
            return Response({"detail": "Trial not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, trial)

        if not _is_speech_trial(trial):
            return Response({"detail": "Not a speech trial"}, status=status.HTTP_400_BAD_REQUEST)

        ser = TherapistScoreSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # Update trial
        score_map = {"success": True, "fail": False, "partial": None}
        trial.success = score_map.get(data["score"])
        trial.score = {"success": 10, "fail": 0, "partial": 5}.get(data["score"], 0)
        trial.status = SessionTrial.Status.COMPLETED
        trial.ended_at = timezone.now()
        trial.save(update_fields=["success", "score", "status", "ended_at"])

        # Update meta
        meta, _ = SpeechTrialMeta.objects.get_or_create(trial=trial)
        meta.therapist_score = data["score"]
        meta.therapist_notes = data.get("notes", "")
        if data.get("override_transcript"):
            meta.therapist_transcript = data["override_transcript"]
        meta.save()

        # Check if session is complete
        session = trial.session
        remaining = session.trials.filter(
            status__in=[SessionTrial.Status.PLANNED, SessionTrial.Status.RUNNING]
        ).count()
        if remaining == 0:
            session.status = TherapySession.Status.COMPLETED
            session.ended_at = timezone.now()
            session.save(update_fields=["status", "ended_at"])

        return Response({
            "trial_id": trial.id,
            "score": data["score"],
            "success": trial.success,
            "session_complete": remaining == 0,
            "remaining_trials": remaining,
        })


# ═══════════════════════════════════════════════════════════════════════════
# Session Summary
# ═══════════════════════════════════════════════════════════════════════════

class SpeechSessionSummaryView(APIView):
    """
    GET /speech/sessions/{session_id}/summary
    Session summary with all trial results and aggregate metrics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id: int):
        try:
            session = TherapySession.objects.get(id=session_id)
        except TherapySession.DoesNotExist:
            return Response({"detail": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        trials = SessionTrial.objects.filter(
            session=session, trial_type__in=["speech_therapy", "speech", "speech_prompt"]
        ).order_by("created_at")

        completed = trials.filter(status=SessionTrial.Status.COMPLETED)
        total = completed.count()
        correct = completed.filter(success=True).count()
        partial = completed.filter(success__isnull=True).count()

        trial_results = []
        for trial in trials:
            meta = getattr(trial, "speech_meta", None)
            analysis = SpeechAnalysis.objects.filter(trial=trial).order_by("-created_at").first()

            trial_results.append({
                "trial_id": trial.id,
                "status": trial.status,
                "success": trial.success,
                "score": trial.score,
                "prompt": trial.prompt,
                "target_text": meta.target_text if meta else "",
                "transcript": meta.therapist_transcript if meta else "",
                "therapist_score": meta.therapist_score if meta else "",
                "prompt_level": meta.prompt_level if meta else 0,
                "analysis_status": analysis.processing_status if analysis else None,
                "feedback_summary": (
                    analysis.feedback_json.get("summary", "") if analysis else ""
                ),
            })

        return Response({
            "session_id": session.id,
            "title": session.title,
            "status": session.status,
            "total_completed": total,
            "correct": correct,
            "partial": partial,
            "failed": total - correct - partial,
            "accuracy": round(correct / total, 3) if total else 0,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "trials": trial_results,
        })


# ═══════════════════════════════════════════════════════════════════════════
# Progress
# ═══════════════════════════════════════════════════════════════════════════

class SpeechProgressView(APIView):
    """
    GET /speech/children/{child_profile_id}/progress
    Aggregated speech therapy metrics for a child.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, child_profile_id: int):
        try:
            child = ChildProfile.objects.select_related("user").get(id=child_profile_id)
        except ChildProfile.DoesNotExist:
            return Response({"detail": "Child profile not found"}, status=status.HTTP_404_NOT_FOUND)

        if not is_admin(request.user):
            if not is_therapist(request.user):
                return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
            if not therapist_has_child(request.user, child.user_id):
                return Response({"detail": "Not assigned to this child"}, status=status.HTTP_403_FORBIDDEN)

        # Speech trials
        qs = SessionTrial.objects.filter(
            session__child_id=child_profile_id,
            trial_type__in=["speech_prompt", "speech", "speech_therapy"],
        )

        completed = qs.filter(status=SessionTrial.Status.COMPLETED)
        total = completed.count()
        avg_score = completed.aggregate(avg=Avg("score"))["avg"]
        success_rate = completed.filter(success=True).count() / total if total else 0.0

        # Category breakdown
        cat_counts = (
            SpeechTrialMeta.objects.filter(trial__in=completed)
            .values("category")
            .annotate(n=Count("id"), avg_score=Avg("trial__score"))
            .order_by("-n")[:10]
        )

        # Prompt level distribution
        prompt_levels = (
            SpeechTrialMeta.objects.filter(trial__in=completed)
            .values("prompt_level")
            .annotate(n=Count("id"))
            .order_by("prompt_level")
        )

        # Recent sessions
        recent_sessions = (
            TherapySession.objects.filter(
                child_id=child_profile_id,
                title__startswith="Speech:",
            ).order_by("-created_at")[:5]
        )

        return Response({
            "child_profile_id": child_profile_id,
            "total_completed_speech_trials": total,
            "avg_score": round(avg_score, 2) if avg_score else 0,
            "success_rate": round(success_rate, 4),
            "top_categories": list(cat_counts),
            "prompt_level_distribution": list(prompt_levels),
            "recent_sessions": [
                {
                    "id": s.id,
                    "title": s.title,
                    "status": s.status,
                    "date": str(s.session_date),
                    "started_at": s.started_at.isoformat() if s.started_at else None,
                }
                for s in recent_sessions
            ],
        })


# ═══════════════════════════════════════════════════════════════════════════
# Legacy Transcribe (kept for backward compat)
# ═══════════════════════════════════════════════════════════════════════════

class SpeechTrialTranscribeView(APIView):
    """
    POST /speech/trials/{trial_id}/transcribe
    Legacy: Creates ASR job via HTTP provider.
    """
    permission_classes = [IsAuthenticated, CanAccessSpeechTrial]

    def post(self, request, trial_id: int):
        try:
            trial = SessionTrial.objects.select_related("session__child__user").get(id=trial_id)
        except SessionTrial.DoesNotExist:
            return Response({"detail": "Trial not found"}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, trial)

        if not _is_speech_trial(trial):
            return Response({"detail": "Not a speech trial"}, status=status.HTTP_400_BAD_REQUEST)

        recording = getattr(trial, "speech_recording", None)
        if not recording or not recording.file:
            return Response({"detail": "No audio uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        ser = ASRJobCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        job = ASRJob.objects.create(
            trial=trial,
            created_by=request.user,
            status=ASRJob.Status.QUEUED,
            provider="http",
            model_name=ser.validated_data.get("model_name", ""),
        )

        asr_url = getattr(settings, "ASR_HTTP_URL", "") or ""
        if not asr_url:
            job.status = ASRJob.Status.FAILED
            job.error = "ASR_HTTP_URL not configured."
            job.save()
            return Response(ASRJobSerializer(job).data, status=status.HTTP_400_BAD_REQUEST)

        try:
            from speech.asr_provider import ASRHTTPProvider
            job.status = ASRJob.Status.RUNNING
            job.save(update_fields=["status"])

            provider = ASRHTTPProvider(asr_url, timeout_seconds=int(getattr(settings, "ASR_HTTP_TIMEOUT", 60)))
            payload = {
                "audio_path": recording.file.path,
                "trial_id": trial.id,
                "model": job.model_name or "default",
            }
            result = provider.transcribe(payload)

            job.status = ASRJob.Status.SUCCEEDED
            job.result_text = result.text or ""
            job.result_confidence = result.confidence
            job.save()

            meta, _ = SpeechTrialMeta.objects.get_or_create(trial=trial)
            if not meta.therapist_transcript and job.result_text:
                meta.therapist_transcript = job.result_text[:500]
                meta.save(update_fields=["therapist_transcript"])

        except Exception as e:
            job.status = ASRJob.Status.FAILED
            job.error = str(e)
            job.save()

        return Response(ASRJobSerializer(job).data)
