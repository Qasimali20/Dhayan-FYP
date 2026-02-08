import { apiFetch } from "./client";

const BASE = "/api/v1/therapy";

// ── Dashboard Stats ──
export function getDashboardStats() {
  return apiFetch(`${BASE}/dashboard/stats`);
}

// ── Session History ──
export function getSessionHistory({ child_id, status, game_type, limit } = {}) {
  const params = new URLSearchParams();
  if (child_id) params.set("child_id", child_id);
  if (status) params.set("status", status);
  if (game_type) params.set("game_type", game_type);
  if (limit) params.set("limit", limit);
  const qs = params.toString();
  return apiFetch(`${BASE}/sessions/history${qs ? "?" + qs : ""}`);
}

// ── Child Progress ──
export function getChildProgress(childId) {
  return apiFetch(`${BASE}/children/${childId}/progress`);
}

// ── Generic Game API (works for matching, object_discovery, problem_solving) ──
export function startGameSession(gameCode, childId, trialCount = 10, opts = {}) {
  return apiFetch(`${BASE}/games/${gameCode}/start/`, {
    method: "POST",
    body: {
      child_id: childId,
      trials_planned: trialCount,
      time_limit_ms: opts.time_limit_ms || 10000,
      supervision_mode: opts.supervision_mode || "therapist",
      session_title: opts.session_title || null,
    },
  });
}

export function nextGameTrial(gameCode, sessionId) {
  return apiFetch(`${BASE}/games/${gameCode}/${sessionId}/next/`, {
    method: "POST",
    body: {},
  });
}

export function submitGameTrial(gameCode, trialId, clicked, responseTimeMs, timedOut = false) {
  return apiFetch(`${BASE}/games/${gameCode}/trial/${trialId}/submit/`, {
    method: "POST",
    body: { clicked, response_time_ms: responseTimeMs, timed_out: timedOut },
  });
}

export function getGameSummary(gameCode, sessionId) {
  return apiFetch(`${BASE}/games/${gameCode}/${sessionId}/summary/`);
}

// ── End / Abandon Session ──
export function endSession(sessionId) {
  return apiFetch(`${BASE}/sessions/${sessionId}/end`, {
    method: "POST",
    body: {},
  });
}
