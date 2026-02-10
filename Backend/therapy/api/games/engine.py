from __future__ import annotations

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError

from patients.models import ChildProfile, TherapistChildAssignment
from therapy.models import TherapySession, SessionTrial, Observation

from therapy.api.games.registry import get_game

# --- Consent toggle (fast MVP) ---
CONSENT_ENFORCED = False

try:
    from compliance.models import Consent
    HAS_CONSENT = True
except Exception:
    HAS_CONSENT = False


def _as_game_instance(game_obj):
    """
    Robust: registry might return a class or an instance.
    If it's a class, instantiate it.
    """
    if isinstance(game_obj, type):
        return game_obj()
    return game_obj


def require_assignment(user, child: ChildProfile) -> None:
    qs = TherapistChildAssignment.objects.filter(therapist_id=user.id)
    ok = (
        qs.filter(child_profile_id=child.id).exists()
        or qs.filter(child_user_id=child.user_id).exists()
    )
    if not ok and not getattr(user, "is_superuser", False):
        raise PermissionDenied("Therapist is not assigned to this child")


def require_consent(child: ChildProfile) -> None:
    if not CONSENT_ENFORCED:
        return

    if HAS_CONSENT:
        active = Consent.objects.filter(child=child, revoked_at__isnull=True)
        types = set(active.values_list("consent_type", flat=True))
        required = {"data", "ai"}
        missing = required - types
        if missing:
            raise PermissionDenied(f"Missing active consent: {', '.join(sorted(missing))}")
    else:
        if not getattr(child, "consent_ai", False):
            raise PermissionDenied("Missing consent_ai on child profile")


def start_session(
    *,
    game_code: str,
    user,
    child_id: int,
    trials_planned: int = 10,
    supervision_mode: str = "therapist",
    session_title: str | None = None,
    time_limit_ms: int = 10000,
) -> dict:
    game = _as_game_instance(get_game(game_code))

    child = ChildProfile.objects.filter(id=child_id, deleted_at__isnull=True).first()
    if not child:
        raise NotFound("Child not found")

    require_assignment(user, child)
    require_consent(child)

    session = TherapySession.objects.create(
        child=child,
        therapist=user,
        created_by=user,
        supervision_mode=supervision_mode,
        status="in_progress",
        session_date=timezone.localdate(),
        started_at=timezone.now(),
        title=session_title or getattr(game, "game_name", game_code),
    )

    for _ in range(int(trials_planned)):
        SessionTrial.objects.create(
            session=session,
            trial_type=game.trial_type,
            target_behavior="select_target_object",
            status="planned",
        )

    return {
        "session_id": session.id,
        "trials_planned": int(trials_planned),
        "time_limit_ms": int(time_limit_ms),
    }


def next_trial(*, game_code: str, user, session_id: int) -> dict:
    game = _as_game_instance(get_game(game_code))

    session = (
        TherapySession.objects.filter(id=session_id)
        .select_related("child", "therapist")
        .first()
    )
    if not session:
        raise NotFound("Session not found")

    if session.therapist_id != user.id and not getattr(user, "is_superuser", False):
        raise PermissionDenied("Not your session")

    if session.status == "completed":
        return {"detail": "Session already completed"}

    trial = SessionTrial.objects.filter(session=session, status="planned").order_by("id").first()
    if not trial:
        return {"detail": "No more planned trials"}

    # AI-driven level (safe)
    level = int(game.compute_level(session.id))

    # Build adaptive trial spec (pass session_id so AI can adapt)
    spec = game.build_trial(level, session_id=session.id)

    # Normalise keys: plugin may use prompt_text/highlight_id/target_id
    prompt  = spec.get("prompt") or spec.get("prompt_text") or ""
    highlight = spec.get("highlight") or spec.get("highlight_id")
    target  = spec.get("target") or spec.get("target_id")
    prompt_audio = spec.get("prompt_audio") or ""

    trial.status = "running"
    trial.prompt = prompt
    trial.started_at = timezone.now()
    trial.save(update_fields=["status", "prompt", "started_at"])

    Observation.objects.create(
        session=session,
        trial=trial,
        therapist=user,
        note="trial_started",
        tags={
            "game": game_code,
            "trial_type": game.trial_type,
            "level": int(spec.get("extra", {}).get("level", level)) if isinstance(spec.get("extra"), dict) else level,
            "options": spec.get("options", []),
            "target": target,
            "target_id": target,
            "time_limit_ms": int(spec.get("time_limit_ms", 10000)),
            "ai_hint": spec.get("ai_hint"),
            "ai_reason": spec.get("ai_reason"),
            "extra": spec.get("extra", {}),
        },
    )

    # Merge plugin spec and always include trial.id as 'id'
    trial_dict = dict(spec)
    trial_dict["id"] = trial.id
    trial_dict["trial_id"] = trial.id  # for backward compatibility
    trial_dict["game"] = game_code
    trial_dict["trial_type"] = game.trial_type
    trial_dict["level"] = level
    trial_dict["prompt"] = prompt
    trial_dict["prompt_audio"] = prompt_audio
    trial_dict["highlight"] = highlight
    trial_dict["options"] = spec.get("options", [])
    trial_dict["target"] = target
    trial_dict["time_limit_ms"] = int(spec.get("time_limit_ms", 10000))
    trial_dict["ai_hint"] = spec.get("ai_hint")
    trial_dict["ai_reason"] = spec.get("ai_reason")
    trial_dict["extra"] = spec.get("extra", {})
    return trial_dict


def submit_trial(
    *,
    game_code: str,
    user,
    trial_id: int,
    **submit_data,
) -> dict:
    game = _as_game_instance(get_game(game_code))

    trial = SessionTrial.objects.filter(id=trial_id).first()
    if not trial:
        raise NotFound("Trial not found")
        trial=trial,

    if trial.session.therapist_id != user.id and not getattr(user, "is_superuser", False):
        raise PermissionDenied("Not your trial")

    if trial.status != "running":
        raise ValidationError(f"Trial not in running state (current={trial.status})")

    started = Observation.objects.filter(trial_id=trial.id, note="trial_started").order_by("-id").first()
    if not started or not isinstance(started.tags, dict) or "target" not in started.tags:
        raise ValidationError("Missing trial_started state (target not found)")

    target = started.tags.get("target") or ""
    level = int(started.tags.get("level") or 1)

    # Pass all submit_data to plugin
    result = game.evaluate(
        target=target,
        submit=submit_data,
        level=level,
        session_id=trial.session_id,
    )

    success = bool(result["success"])
    score = int(result["score"])

    trial.success = success
    trial.score = score
    trial.status = "completed"
    trial.ended_at = timezone.now()
    trial.save(update_fields=["success", "score", "status", "ended_at"])

    Observation.objects.create(
        session=trial.session,
        trial=trial,
        therapist=user,
        note="trial_telemetry",
        tags=result.get("telemetry", {}),
    )

    # Auto-complete session if no more planned/running
    session_id = trial.session_id
    remaining = SessionTrial.objects.filter(session_id=session_id).exclude(status="completed").exists()

    session_completed = False
    session_summary = None

    if not remaining:
        s = trial.session
        if s.status != "completed":
            s.status = "completed"
            s.ended_at = timezone.now()
            s.save(update_fields=["status", "ended_at"])

        session_completed = True
        session_summary = summary(game_code=game_code, user=user, session_id=session_id)

    response = {
        "trial_id": trial.id,
        "success": success,
        "score": score,
        "feedback": result.get("feedback", ""),
        "ai_recommendation": result.get("ai_recommendation"),
        "ai_reason": result.get("ai_reason"),
        "session_completed": session_completed,
        "summary": session_summary,
    }
    # Merge all extra fields from result (without overwriting above keys)
    for k, v in result.items():
        if k not in response:
            response[k] = v
    return response


def summary(*, game_code: str, user, session_id: int) -> dict:
    game = _as_game_instance(get_game(game_code))

    session = TherapySession.objects.filter(id=session_id).select_related("therapist").first()
    if not session:
        raise NotFound("Session not found")

    if session.therapist_id != user.id and not getattr(user, "is_superuser", False):
        raise PermissionDenied("Not your session")

    trials = SessionTrial.objects.filter(session=session)
    total = trials.count()
    completed = trials.filter(status="completed").count()
    correct = trials.filter(status="completed", success=True).count()
    accuracy = (correct / completed) if completed else 0.0

    obs = Observation.objects.filter(session=session, note="trial_telemetry")
    rts = []
    for o in obs:
        if isinstance(o.tags, dict) and "response_time_ms" in o.tags:
            try:
                rts.append(int(o.tags["response_time_ms"]))
            except Exception:
                pass
    avg_rt = (sum(rts) // len(rts)) if rts else None

    level = int(game.compute_level(session.id))

    # One solid therapist-facing suggestion (simple + deterministic)
    suggestion = ""
    if completed:
        if accuracy >= 0.8 and (avg_rt is None or avg_rt <= 3200):
            suggestion = "Suggestion: Fade prompts next session (L2/L3) and increase distractor difficulty."
        elif accuracy < 0.5:
            suggestion = "Suggestion: Return to Level 1, reduce distractors, and slow pacing."
        else:
            suggestion = "Suggestion: Maintain current level and continue practice."

    return {
        "session_id": session.id,
        "game": game_code,
        "status": session.status,
        "total_trials": total,
        "completed_trials": completed,
        "correct": correct,
        "accuracy": round(accuracy, 3),
        "avg_response_time_ms": avg_rt,
        "current_level": level,
        "suggestion": suggestion,
    }
