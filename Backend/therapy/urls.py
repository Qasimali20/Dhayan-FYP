from django.urls import path, include
from therapy.views import (
    SessionListCreateView,
    SessionDetailView,
    SessionStartView,
    SessionEndView,
    SessionAddTrialView,
    TrialStartView,
    TrialFinalizeView,
    SessionAddObservationView,
)
from therapy.api.dashboard_views import (
    DashboardStatsView,
    ChildProgressView,
    SessionHistoryView,
)

urlpatterns = [
    # --- Existing therapy APIs (unchanged & correct) ---
    path("sessions", SessionListCreateView.as_view(), name="therapy-sessions-list-create"),
    path("sessions/<int:session_id>", SessionDetailView.as_view(), name="therapy-sessions-detail"),
    path("sessions/<int:session_id>/start", SessionStartView.as_view(), name="therapy-sessions-start"),
    path("sessions/<int:session_id>/end", SessionEndView.as_view(), name="therapy-sessions-end"),

    path("sessions/<int:session_id>/trials", SessionAddTrialView.as_view(), name="therapy-trials-add"),
    path("sessions/<int:session_id>/trials/<int:trial_id>/start", TrialStartView.as_view(), name="therapy-trials-start"),
    path("sessions/<int:session_id>/trials/<int:trial_id>/finalize", TrialFinalizeView.as_view(), name="therapy-trials-finalize"),

    path("sessions/<int:session_id>/observations", SessionAddObservationView.as_view(), name="therapy-observations-add"),

    # --- Dashboard & Analytics ---
    path("dashboard/stats", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("children/<int:child_id>/progress", ChildProgressView.as_view(), name="child-progress"),
    path("sessions/history", SessionHistoryView.as_view(), name="session-history"),

    # --- Joint Attention Game (legacy routes) ---
    # API
    path("games/ja/", include("therapy.api.game_ja_urls")),

    # UI (HTML/JS)
    path("games/ja/ui/", include("therapy.api.game_ja_urls_ui")),

    # --- Generic Game API (matching, object_discovery, problem_solving, etc.) ---
    path("games/", include("therapy.api.game_generic_urls")),
]
