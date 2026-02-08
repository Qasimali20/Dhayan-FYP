"""
Generic game API views — work for ANY registered game plugin.
URL pattern: /api/v1/therapy/games/<game_code>/start/ etc.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

import therapy.api.games  # noqa: F401 — ensure plugins register

from therapy.api.games import engine
from therapy.api.game_ja_serializers import StartSessionSerializer, SubmitTrialSerializer


class GameStartSessionView(APIView):
    """POST /api/v1/therapy/games/<game_code>/start/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, game_code: str):
        ser = StartSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        session_out = engine.start_session(
            game_code=game_code,
            user=request.user,
            child_id=int(data["child_id"]),
            trials_planned=int(data.get("trials_planned", 10)),
            supervision_mode=data.get("supervision_mode", "therapist"),
            session_title=data.get("session_title") or game_code.replace("_", " ").title(),
            time_limit_ms=int(data.get("time_limit_ms", 10000)),
        )

        first_trial = engine.next_trial(
            game_code=game_code,
            user=request.user,
            session_id=int(session_out["session_id"]),
        )

        payload = {"session": session_out, "first_trial": first_trial}

        detail = (first_trial or {}).get("detail")
        if isinstance(detail, str) and "No more planned trials" in detail:
            payload["summary"] = engine.summary(
                game_code=game_code,
                user=request.user,
                session_id=int(session_out["session_id"]),
            )

        return Response(payload, status=status.HTTP_201_CREATED)


class GameNextTrialView(APIView):
    """POST /api/v1/therapy/games/<game_code>/<session_id>/next/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, game_code: str, session_id: int):
        out = engine.next_trial(
            game_code=game_code,
            user=request.user,
            session_id=int(session_id),
        )

        detail = (out or {}).get("detail")
        if isinstance(detail, str) and "No more planned trials" in detail:
            return Response({
                "detail": detail,
                "summary": engine.summary(
                    game_code=game_code,
                    user=request.user,
                    session_id=int(session_id),
                ),
            })

        return Response(out)


class GameSubmitTrialView(APIView):
    """POST /api/v1/therapy/games/<game_code>/trial/<trial_id>/submit/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, game_code: str, trial_id: int):
        ser = SubmitTrialSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        out = engine.submit_trial(
            game_code=game_code,
            user=request.user,
            trial_id=int(trial_id),
            clicked=str(data["clicked"]),
            response_time_ms=int(data["response_time_ms"]),
            timed_out=bool(data.get("timed_out", False)),
        )

        return Response(out)


class GameSummaryView(APIView):
    """GET /api/v1/therapy/games/<game_code>/<session_id>/summary/"""
    permission_classes = [IsAuthenticated]

    def get(self, request, game_code: str, session_id: int):
        out = engine.summary(
            game_code=game_code,
            user=request.user,
            session_id=int(session_id),
        )
        return Response(out)
