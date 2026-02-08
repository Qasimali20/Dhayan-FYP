"""
Dashboard & Analytics API endpoints for DHYAN.
Provides aggregated stats for admin & therapist dashboards.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import UserRole
from patients.models import ChildProfile, TherapistChildAssignment
from therapy.models import TherapySession, SessionTrial, Observation
from patients.permissions import user_has_role

User = get_user_model()


class DashboardStatsView(APIView):
    """
    GET /api/v1/therapy/dashboard/stats
    Returns high-level stats for the authenticated user's dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_admin = user.is_staff or user_has_role(user, "admin")

        if is_admin:
            total_children = ChildProfile.objects.filter(deleted_at__isnull=True).count()
            total_therapists = UserRole.objects.filter(role__slug="therapist").values("user").distinct().count()
            total_sessions = TherapySession.objects.count()
            completed_sessions = TherapySession.objects.filter(status="completed").count()
            active_sessions = TherapySession.objects.filter(status="in_progress").count()
        else:
            assigned_child_ids = TherapistChildAssignment.objects.filter(
                therapist=user
            ).values_list("child_user_id", flat=True)

            total_children = ChildProfile.objects.filter(
                user_id__in=assigned_child_ids, deleted_at__isnull=True
            ).count()
            total_therapists = 1
            total_sessions = TherapySession.objects.filter(
                therapist=user
            ).count()
            completed_sessions = TherapySession.objects.filter(
                therapist=user, status="completed"
            ).count()
            active_sessions = TherapySession.objects.filter(
                therapist=user, status="in_progress"
            ).count()

        # Recent 7 days activity
        week_ago = timezone.now() - timedelta(days=7)
        if is_admin:
            recent_sessions = TherapySession.objects.filter(created_at__gte=week_ago).count()
            recent_trials = SessionTrial.objects.filter(
                session__created_at__gte=week_ago, status="completed"
            ).count()
            recent_correct = SessionTrial.objects.filter(
                session__created_at__gte=week_ago, status="completed", success=True
            ).count()
        else:
            recent_sessions = TherapySession.objects.filter(
                therapist=user, created_at__gte=week_ago
            ).count()
            recent_trials = SessionTrial.objects.filter(
                session__therapist=user, session__created_at__gte=week_ago, status="completed"
            ).count()
            recent_correct = SessionTrial.objects.filter(
                session__therapist=user, session__created_at__gte=week_ago, status="completed", success=True
            ).count()

        weekly_accuracy = (recent_correct / recent_trials) if recent_trials else 0.0

        return Response({
            "total_children": total_children,
            "total_therapists": total_therapists,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "active_sessions": active_sessions,
            "recent_sessions_7d": recent_sessions,
            "recent_trials_7d": recent_trials,
            "weekly_accuracy": round(weekly_accuracy, 3),
        })


class ChildProgressView(APIView):
    """
    GET /api/v1/therapy/children/<child_id>/progress
    Returns aggregated progress for a specific child across all games.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, child_id: int):
        user = request.user
        is_admin = user.is_staff or user_has_role(user, "admin")

        try:
            child = ChildProfile.objects.select_related("user").get(id=child_id)
        except ChildProfile.DoesNotExist:
            return Response({"detail": "Child not found"}, status=404)

        # Check access
        if not is_admin:
            assigned = TherapistChildAssignment.objects.filter(
                therapist=user, child_user=child.user
            ).exists()
            if not assigned:
                return Response({"detail": "Not assigned to this child"}, status=403)

        sessions = TherapySession.objects.filter(child=child)
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(status="completed").count()

        trials = SessionTrial.objects.filter(session__child=child, status="completed")
        total_trials = trials.count()
        correct_trials = trials.filter(success=True).count()
        overall_accuracy = (correct_trials / total_trials) if total_trials else 0.0

        # Per-game breakdown
        game_stats = []
        game_types = trials.values_list("trial_type", flat=True).distinct()
        for gt in game_types:
            gt_trials = trials.filter(trial_type=gt)
            gt_total = gt_trials.count()
            gt_correct = gt_trials.filter(success=True).count()
            gt_accuracy = (gt_correct / gt_total) if gt_total else 0.0

            # Avg response time from telemetry
            obs = Observation.objects.filter(
                session__child=child,
                trial__trial_type=gt,
                note="trial_telemetry",
            )
            rts = []
            for o in obs:
                if isinstance(o.tags, dict) and "response_time_ms" in o.tags:
                    try:
                        rts.append(int(o.tags["response_time_ms"]))
                    except (ValueError, TypeError):
                        pass

            game_stats.append({
                "game": gt,
                "total_trials": gt_total,
                "correct": gt_correct,
                "accuracy": round(gt_accuracy, 3),
                "avg_response_time_ms": (sum(rts) // len(rts)) if rts else None,
                "sessions": sessions.filter(
                    trials__trial_type=gt
                ).distinct().count(),
            })

        # Recent sessions timeline
        recent = sessions.order_by("-created_at")[:10]
        recent_list = []
        for s in recent:
            s_trials = SessionTrial.objects.filter(session=s, status="completed")
            s_total = s_trials.count()
            s_correct = s_trials.filter(success=True).count()
            recent_list.append({
                "session_id": s.id,
                "date": str(s.session_date),
                "status": s.status,
                "title": s.title,
                "total_trials": s_total,
                "correct": s_correct,
                "accuracy": round((s_correct / s_total), 3) if s_total else 0.0,
            })

        return Response({
            "child_id": child.id,
            "child_name": child.user.full_name or child.user.email,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "total_trials": total_trials,
            "correct_trials": correct_trials,
            "overall_accuracy": round(overall_accuracy, 3),
            "game_breakdown": game_stats,
            "recent_sessions": recent_list,
        })


class SessionHistoryView(APIView):
    """
    GET /api/v1/therapy/sessions/history
    Returns all sessions for the current user (therapist) with summary data.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_admin = user.is_staff or user_has_role(user, "admin")

        if is_admin:
            sessions = TherapySession.objects.select_related("child__user", "therapist").order_by("-created_at")
        else:
            sessions = TherapySession.objects.select_related("child__user", "therapist").filter(
                therapist=user
            ).order_by("-created_at")

        # Hide orphaned sessions (in_progress with zero completed trials)
        # unless explicitly requesting in_progress status
        hide_orphans = request.query_params.get("include_orphans") != "true"

        # Optional filters
        child_id = request.query_params.get("child_id")
        status_filter = request.query_params.get("status")
        game_type = request.query_params.get("game_type")

        if child_id:
            sessions = sessions.filter(child_id=child_id)
        if status_filter:
            sessions = sessions.filter(status=status_filter)
        if game_type:
            sessions = sessions.filter(trials__trial_type=game_type).distinct()

        # Limit
        limit = min(int(request.query_params.get("limit", 50)), 200)

        # Filter out orphaned / broken sessions:
        # - sessions with 0 completed trials (never played)
        # - sessions with completed trials but 0 correct (from buggy period)
        if hide_orphans:
            sessions = sessions.annotate(
                completed_trial_count=Count("trials", filter=Q(trials__status="completed")),
                correct_trial_count=Count("trials", filter=Q(trials__status="completed", trials__success=True)),
            ).exclude(completed_trial_count=0).exclude(correct_trial_count=0)

        sessions = sessions[:limit]

        result = []
        for s in sessions:
            s_trials = SessionTrial.objects.filter(session=s, status="completed")
            s_total = s_trials.count()
            s_correct = s_trials.filter(success=True).count()

            trial_types = list(
                SessionTrial.objects.filter(session=s)
                .values_list("trial_type", flat=True)
                .distinct()
            )

            result.append({
                "id": s.id,
                "title": s.title,
                "status": s.status,
                "session_date": str(s.session_date),
                "child_id": s.child_id,
                "child_name": s.child.user.full_name or s.child.user.email,
                "therapist_name": s.therapist.full_name or s.therapist.email,
                "total_trials": s_total,
                "correct": s_correct,
                "accuracy": round((s_correct / s_total), 3) if s_total else 0.0,
                "game_types": trial_types,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "created_at": s.created_at.isoformat(),
            })

        return Response(result)
