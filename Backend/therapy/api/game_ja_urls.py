from django.urls import path
from .game_ja_views import JAStartSessionAPIView, JANextTrialAPIView, JASubmitTrialAPIView, JASessionSummaryAPIView

urlpatterns = [
    path("start/", JAStartSessionAPIView.as_view()),
    path("<int:session_id>/next/", JANextTrialAPIView.as_view()),
    path("trial/<int:trial_id>/submit/", JASubmitTrialAPIView.as_view()),
    path("<int:session_id>/summary/", JASessionSummaryAPIView.as_view()),
]
