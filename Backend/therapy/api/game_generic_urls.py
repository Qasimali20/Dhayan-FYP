from django.urls import path
from .game_generic_views import (
    GameStartSessionView,
    GameNextTrialView,
    GameSubmitTrialView,
    GameSummaryView,
)

urlpatterns = [
    path("<str:game_code>/start/", GameStartSessionView.as_view()),
    path("<str:game_code>/<int:session_id>/next/", GameNextTrialView.as_view()),
    path("<str:game_code>/trial/<int:trial_id>/submit/", GameSubmitTrialView.as_view()),
    path("<str:game_code>/<int:session_id>/summary/", GameSummaryView.as_view()),
]
