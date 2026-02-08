from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

# ✅ IMPORTANT: importing games ensures plugins register (ja plugin loads)
import therapy.api.games  # noqa: F401

from therapy.api.games import engine
from .game_ja_serializers import StartSessionSerializer, SubmitTrialSerializer

GAME_CODE = "ja"  # ✅ registry key for plugin


class JAStartSessionAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        World-class UX:
        - Create session
        - Immediately fetch the first trial (so user doesn't need to press Next Trial)
        """
        ser = StartSessionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        # 1) Create the session
        session_out = engine.start_session(
            game_code=GAME_CODE,
            user=request.user,
            child_id=int(data["child_id"]),
            trials_planned=int(data.get("trials_planned", 10)),
            supervision_mode=data.get("supervision_mode", "therapist"),
            session_title=data.get("session_title") or "Look Where I Point",
            time_limit_ms=int(data.get("time_limit_ms", 10000)),
        )

        # 2) Immediately load the first trial
        first_trial = engine.next_trial(
            game_code=GAME_CODE,
            user=request.user,
            session_id=int(session_out["session_id"]),
        )

        # If there are no planned trials (edge case), just return session info
        payload = {
            "session": session_out,
            "first_trial": first_trial,
        }

        # Optional: if first_trial says "No more planned trials", include summary
        detail = (first_trial or {}).get("detail")
        if isinstance(detail, str) and "No more planned trials" in detail:
            payload["summary"] = engine.summary(
                game_code=GAME_CODE,
                user=request.user,
                session_id=int(session_out["session_id"]),
            )

        return Response(payload, status=status.HTTP_201_CREATED)


class JANextTrialAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id: int):
        """
        If trials finished, return summary automatically.
        """
        out = engine.next_trial(
            game_code=GAME_CODE,
            user=request.user,
            session_id=int(session_id),
        )

        detail = (out or {}).get("detail")
        if isinstance(detail, str) and "No more planned trials" in detail:
            return Response(
                {
                    "detail": detail,
                    "summary": engine.summary(
                        game_code=GAME_CODE,
                        user=request.user,
                        session_id=int(session_id),
                    ),
                },
                status=status.HTTP_200_OK,
            )

        return Response(out, status=status.HTTP_200_OK)


class JASubmitTrialAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trial_id: int):
        """
        Submit returns:
        - success, score, feedback
        - ai_recommendation / ai_reason
        - session_completed + summary (when finished)
        """
        ser = SubmitTrialSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        out = engine.submit_trial(
            game_code=GAME_CODE,
            user=request.user,
            trial_id=int(trial_id),
            clicked=str(data["clicked"]),
            response_time_ms=int(data["response_time_ms"]),
            timed_out=bool(data.get("timed_out", False)),
        )

        return Response(out, status=status.HTTP_200_OK)


class JASessionSummaryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id: int):
        out = engine.summary(
            game_code=GAME_CODE,
            user=request.user,
            session_id=int(session_id),
        )
        return Response(out, status=status.HTTP_200_OK)
